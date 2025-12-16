# EcoLogistix Risk Scout Agent
import os
import time
import signal
import sys
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()

logger = get_logger("RiskScout")

running = True

def signal_handler(signum, frame):
    global running
    logger.info(f"Received signal {signum}, shutting down...")
    running = False

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Risk Scout Agent Initialized")
    
    # Simulate some activity for log verification
    try:
        ais_key = os.getenv("AIS_API_KEY")
        if not ais_key:
            logger.warning("AIS_API_KEY not found in environment")
        
        logger.info("Starting main loop...")
        while running:
            # Placeholder for actual logic
            time.sleep(1) # Faster loop for responsiveness
            
            # Real agent logic would go here
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Agent Stopped")
