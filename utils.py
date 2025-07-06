import logging
import logging.config
from config import LOGGING_CONFIG
from typing import Optional, Dict, Any
from datetime import datetime

def setup_logger(name: str = "etimad") -> logging.Logger:
    logging.config.dictConfig(LOGGING_CONFIG)
    return logging.getLogger(name)

def format_tender_data(tender: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize tender data format"""
    formatted = {}
    for k, v in tender.items():
        if isinstance(v, str):
            formatted[k] = v.strip()
        else:
            formatted[k] = v
    return formatted

def validate_tender(tender: Dict[str, Any]) -> bool:
    """Validate required fields in tender"""
    required_fields = ["رقم المنافسة", "اسم المنافسة", "الجهة الحكوميه"]
    return all(field in tender for field in required_fields)

def log_execution_time(func):
    """Decorator to log function execution time"""
    async def async_wrapper(*args, **kwargs):
        start = datetime.now()
        logger = setup_logger("etimad.timing")
        logger.info(f"Starting {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            duration = (datetime.now() - start).total_seconds()
            logger.info(f"Completed {func.__name__} in {duration:.2f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            logger.error(f"Failed {func.__name__} after {duration:.2f}s: {str(e)}")
            raise
    
    def sync_wrapper(*args, **kwargs):
        start = datetime.now()
        logger = setup_logger("etimad.timing")
        logger.info(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start).total_seconds()
            logger.info(f"Completed {func.__name__} in {duration:.2f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            logger.error(f"Failed {func.__name__} after {duration:.2f}s: {str(e)}")
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper