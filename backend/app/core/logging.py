import logging
import sys

def setup_logging():
    logger = logging.getLogger("gridflex")
    logger.setLevel(logging.INFO)
    
    # Check if handlers already exist to avoid duplicates during testing
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

logger = setup_logging()
