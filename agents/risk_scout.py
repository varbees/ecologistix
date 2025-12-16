# EcoLogistix Risk Scout Agent
import os
import time
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()

logger = get_logger("RiskScout")

if __name__ == "__main__":
    logger.info("Risk Scout Agent Initialized")
    
    # Simulate some activity for log verification
    try:
        ais_key = os.getenv("AIS_API_KEY")
        if not ais_key:
            logger.warning("AIS_API_KEY not found in environment")
        
        logger.info("Starting main loop...")
        while True:
            # Placeholder for actual logic
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Agent shutting down")
