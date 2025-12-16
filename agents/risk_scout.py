# EcoLogistix Risk Scout Agent
import os
import time
import signal
import asyncio
import json
import re
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from smolagents import CodeAgent, ApiModel
from utils.logger import get_logger
from db import ShipmentDB
from tools import WeatherTool, CarbonTool, ShippingTool

load_dotenv()

logger = get_logger("RiskScout")

running = True

def signal_handler(signum, frame):
    global running
    logger.info(f"Received signal {signum}, shutting down...")
    running = False

class RiskScout:
    def __init__(self):
        self.db = ShipmentDB()
        self.tools = [WeatherTool(), CarbonTool(), ShippingTool()]
        
        # Configure Model
        # Roadmap suggested mistralai/Mistral-Nemo-12B-Instruct-2407
        # Using HfApiModel. If HF_API_KEY is not set, this might fail unless using a public endpoint or local.
        # Assuming user has HF key from .env check earlier.
        model_id = os.getenv("RISK_SCOUT_MODEL", "mistralai/Mistral-Nemo-12B-Instruct-2407")
        self.model = ApiModel(model_id=model_id)
        
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            max_steps=3,
            verbosity_level=2
        )
        
        self.system_prompt = """
You are the Risk Scout agent in EcoLogistix.
Your role is to analyze active shipments for risks based on weather, news, and route data.

For the given shipment:
1. Check weather forecast at current location and destination.
2. Calculate a risk score (0.0 to 1.0).
   - > 0.7 is HIGH risk.
   - > 0.4 is MEDIUM risk.
   - < 0.4 is LOW risk.
3. Identify specific risk factors (e.g., "High Wind", "Heavy Rain").

Return ONLY a valid JSON object with this format:
{
    "risk_score": 0.15,
    "risk_factors": [],
    "recommended_action": "MONITOR",
    "reasoning": "Weather is clear."
}
"""

    async def scan_shipment(self, shipment: Dict[str, Any]):
        """Analyze a single shipment"""
        logger.info(f"Scanning shipment {shipment.get('id')} ({shipment.get('vessel_name')})")
        
        prompt = f"""
{self.system_prompt}

Analyze this shipment:
- ID: {shipment.get('id')}
- Vessel: {shipment.get('vessel_name')}
- Location: {shipment.get('current_location_wkt')}
- Origin: {shipment.get('origin_port')}
- Destination: {shipment.get('destination_port')}
- ETA: {shipment.get('eta')}

Use the 'fetch_weather' tool if you need weather data.
"""
        # Run agent (blocking call, run in executor if needed, but for now simple sync call inside async loop is okay for low volume)
        # CodeAgent.run is synchronous.
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.agent.run, prompt)
            
            parsed = self._parse_output(result)
            if parsed:
                logger.info(f"Risk assessment for {shipment.get('vessel_name')}: {parsed['risk_score']} ({parsed['recommended_action']})")
                
                await self.db.update_shipment_risk(
                    shipment['id'], 
                    parsed['risk_score'], 
                    parsed.get('risk_factors', [])
                )
            else:
                logger.warning(f"Failed to parse agent output for {shipment.get('id')}")

        except Exception as e:
            logger.error(f"Error scanning shipment {shipment.get('id')}: {e}")

    def _parse_output(self, output: Any) -> Optional[Dict[str, Any]]:
        try:
            # If output is already dict (sometimes agent returns structured)
            if isinstance(output, dict):
                return output
            
            # Use regex to find JSON
            match = re.search(r'\{.*\}', str(output), re.DOTALL)
            if match:
                return json.loads(match.group())
            return None
        except Exception as e:
            logger.error(f"JSON Parse Error: {e}")
            return None

    async def run(self):
        logger.info("Risk Scout Loop Starting...")
        while running:
            try:
                shipments = await self.db.get_active_shipments()
                if not shipments:
                    logger.info("No active shipments found. Sleeping...")
                    await asyncio.sleep(60)
                    continue
                
                for shipment in shipments:
                    if not running: break
                    await self.scan_shipment(shipment)
                    await asyncio.sleep(5) # Rate limit between shipments
                
                # Sleep between cycles
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    scout = RiskScout()
    asyncio.run(scout.run())
