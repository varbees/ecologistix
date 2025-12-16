import logging
import json
import sys
import os
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_object = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_object)

def get_logger(name: str):
    logger = logging.getLogger(name)
    
    # Defaults
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(log_level)
    
    handler = logging.StreamHandler(sys.stdout)
    
    if os.getenv("ENVIRONMENT") == "production":
        handler.setFormatter(JSONFormatter())
    else:
        # Simple text format for dev
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
    logger.addHandler(handler)
    return logger
