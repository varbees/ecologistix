import os
import sys
import json
import time
import asyncio
import redis
from dotenv import load_dotenv

# Add current directory to path so imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from smolagents import CodeAgent, InferenceClientModel

from tools.routing_tool import RoutingTool
from tools.carbon_tool import CarbonTool
from tools.shipping_tool import ShippingTool
from db import ShipmentDB
from utils.logger import get_logger

load_dotenv()
logger = get_logger("RoutePlanner")

class RoutePlanner:
    def __init__(self):
        # Redis Connection
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        self.redis_client = redis.Redis(host=redis_host, port=int(redis_port), decode_responses=True)
        self.task_queue = "agent:task:route_planner"
        
        # DB Connection
        self.db = ShipmentDB()
        
        # Tools
        self.tools = [RoutingTool(), CarbonTool(), ShippingTool()]
        
        # Model
        # Use deepseek-coder if available or fallback to Qwen
        model_id = os.getenv("ROUTE_PLANNER_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct")
        self.model = InferenceClientModel(model_id=model_id)
        
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            max_iterations=8,
            additional_authorized_imports=["networkx", "json"]
        )
        
        self.running = True

    async def run(self):
        logger.info(f"Route Planner Agent started. Listening on {self.task_queue}...")
        
        while self.running:
            try:
                # Blocking pop from Redis (timeout 5s to allow graceful shutdown check)
                task_data = self.redis_client.blpop(self.task_queue, timeout=5)
                
                if task_data:
                    queue, payload = task_data
                    logger.info(f"Received task: {payload}")
                    await self.process_task(json.loads(payload))
                    
            except redis.exceptions.ConnectionError:
                logger.error("Redis connection lost. Retrying in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(1)

    async def process_task(self, task: dict):
        task_type = task.get("task_type")
        shipment_id = task.get("shipment_id")
        reason_data = task.get("reason", {})
        
        if task_type != "PLAN_NEW_ROUTE":
            logger.warning(f"Unknown task type: {task_type}")
            return

        logger.info(f"Planning new route for Shipment {shipment_id} due to {reason_data.get('event_type', 'UNKNOWN')}")
        
        # Fetch shipment details
        shipments = await self.db.get_active_shipments()
        # Find specific shipment (inefficient fetch all, but ok for prototype)
        shipment = next((s for s in shipments if str(s['id']) == shipment_id), None)
        
        if not shipment:
            logger.error(f"Shipment {shipment_id} not found in DB")
            return

        prompt = f"""
        You are an expert Maritime Logistician.
        
        Task: Plan alternative routes for Shipment {shipment_id} (Vessel: {shipment['vessel_name']}).
        Origin: {shipment['origin_port']}
        Destination: {shipment['destination_port']}
        Current Status: AT_RISK
        Disruption Reason: {reason_data}
        
        1. Use the 'find_route' tool to get the standard route.
        2. Use the 'find_route' tool again with 'avoid_nodes' if the disruption implies a blockage (e.g., if reason is 'Suez Canal Blockage', avoid 'Suez Canal').
        3. If no specific blockage, try to find an alternative route via a different hub (e.g., via Cape of Good Hope if Suez is risky).
        4. Calculate Carbon Emissions for each route using 'calculate_carbon'.
        5. Return a JSON object with 2-3 options.
        
        Output Format:
        {{
            "options": [
                {{
                    "route_name": "Standard Route",
                    "path": ["Port A", "Port B"],
                    "distance_km": 5000,
                    "carbon_kg": 10000,
                    "estimated_days": 15,
                    "risk_analysis": "High risk due to ..."
                }},
                {{
                     "route_name": "Cape Route",
                     ...
                }}
            ],
            "recommendation": "Cape Route"
        }}
        """
        
        try:
            # Run Agent
            # Note: CodeAgent runs synchronously. We might want to offload to thread if blocking event loop too much.
            # For now, simplistic approach.
            result = self.agent.run(prompt)
            logger.info(f"Agent generated plan: {result}")
            
            # Save to DB
            await self.db.save_route_alternatives(shipment_id, result)

            # Week 8 Integrated Flow: Trigger Carbon Auditor
            # Prepare task for Carbon Auditor
            if isinstance(result, dict) and "options" in result:
                audit_task = {
                    "task_type": "CARBON_AUDIT",
                    "shipment_id": shipment_id, # Wait, shipment_id var name is task.get("shipment_id")
                    "route_options": result["options"]
                }
                # Fix variable scope
                audit_task["shipment_id"] = shipment_id 
                
                self.redis_client.rpush("agent:task:carbon_audit", json.dumps(audit_task))
                logger.info("Chained task: Pushed to Carbon Auditor queue")
            
        except Exception as e:
            logger.error(f"Agent failed to plan route: {e}")

if __name__ == "__main__":
    planner = RoutePlanner()
    asyncio.run(planner.run())
