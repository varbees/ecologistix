import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import json
import asyncio
import redis
from dotenv import load_dotenv
from smolagents import CodeAgent, InferenceClientModel

from rag_manager import RAGManager
from tools.carbon_tool import CarbonTool
from db import ShipmentDB
from utils.logger import get_logger

load_dotenv()
logger = get_logger("CarbonAuditor")

class CarbonAuditor:
    def __init__(self):
        # Redis
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        self.redis_client = redis.Redis(host=redis_host, port=int(redis_port), decode_responses=True)
        self.task_queue = "agent:task:carbon_audit" # Triggered by Route Planner or Orchestrator
        
        # Components
        self.db = ShipmentDB()
        self.rag = RAGManager()
        self.carbon_tool = CarbonTool()
        
        # Model
        model_id = os.getenv("CARBON_AUDITOR_MODEL", "Qwen/Qwen2.5-Math-7B-Instruct")
        self.model = InferenceClientModel(model_id=model_id)
        
        # Tools list for Agent
        self.tools = [self.carbon_tool]
        
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            max_steps=5
        )
        
        self.running = True

    async def run(self):
        logger.info(f"Carbon Auditor started. Listening on {self.task_queue}...")
        while self.running:
            try:
                task_data = self.redis_client.blpop(self.task_queue, timeout=5)
                if task_data:
                    queue, payload = task_data
                    logger.info(f"Received audit task: {payload}")
                    await self.audit_route_options(json.loads(payload))
            except redis.exceptions.ConnectionError:
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in audit loop: {e}")
                await asyncio.sleep(1)

    async def audit_route_options(self, task: dict):
        """
        Task Payload expected:
        {
            "shipment_id": "...",
            "route_options": [ { "route_name": "...", "distance_km": ... } ]
        }
        """
        shipment_id = task.get("shipment_id")
        options = task.get("route_options", [])
        
        if not options:
            # Fallback: fetch from DB if only shipment_id provided?
            # For now assume payload has data
            logger.warning("No route options to audit")
            return

        # 1. Retrieve Compliance Info
        # Query generic rules + specific destination rules (if we knew destination)
        # Assuming destination is in options or shipment ID lookup
        compliance_docs = await self.rag.query_knowledge("EU ETS shipping emissions caps 2025")
        compliance_context = "\n".join([f"- {doc['content']} (Source: {doc['source']})" for doc in compliance_docs])
        
        prompt = f"""
        You are the Carbon Auditor.
        
        Task: Audit the proposed route options for Shipment {shipment_id}.
        
        Compliance Context (RAG Retrieved):
        {compliance_context}
        
        Route Options:
        {json.dumps(options, indent=2)}
        
        1. For each route, calculate total emissions if not already provided (estimate 10g CO2/ton-km for Container).
        2. Check against compliance rules.
        3. Recommend the most sustainable compliant route.
        
        Output JSON:
        {{
            "audit_id": "AUDIT_1",
            "compliant": true,
            "recommended_route": "Route Name",
            "details": "..."
        }}
        """
        
        try:
            # Run Agent
            # CodeAgent run is sync
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.agent.run, prompt)
            
            logger.info(f"Audit Result: {result}")
            
            # Save to Audit Reports DB
            await self.save_audit_report(shipment_id, result)
            
        except Exception as e:
            logger.error(f"Audit failed: {e}")

    async def save_audit_report(self, shipment_id: str, report: Any):
        conn = await asyncpg.connect(self.db.dsn)
        try:
            # Parse report if string
            if isinstance(report, str):
                # Try simple storage or JSON parse
                 audit_details_json = json.dumps({"raw_output": report})
            else:
                 audit_details_json = json.dumps(report)
                 
            await conn.execute("""
                INSERT INTO audit_reports (shipment_id, audit_details)
                VALUES ($1, $2)
            """, shipment_id, audit_details_json)
        finally:
            await conn.close()

if __name__ == "__main__":
    auditor = CarbonAuditor()
    asyncio.run(auditor.run())
