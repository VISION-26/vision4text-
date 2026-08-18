import logging
import sys
from typing import Optional


def setup_logger(name: str = "vision_text", level: int = logging.INFO) -> logging.Logger:
    """
    Configure enterprise structured console logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d]: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger


logger = setup_logger()
