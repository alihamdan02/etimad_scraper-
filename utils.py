import logging
import logging.config
from config import LOGGING_CONFIG
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
from db import db_manager
import json

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


def generate_main_to_sub_mapping(output_path="main_to_sub.json"):
    """
    Fetches classification-keyword pairs from the database and saves them
    as a nested dictionary (classification -> [keywords]) to a JSON file.

    Args:
        output_path (str): File path to save the output JSON.
    """
    query = """ 
    SELECT 
        eck.keyword_ar AS keyword_name_ar,
        ec.name_ar AS classification_name_ar
    FROM 
        etimad_classification_keywords AS eck
    JOIN 
        etimad_classifications AS ec ON eck.classification_id = ec.id
    ORDER BY 
        ec.name_en, eck.keyword_en;
    """

    myresult = db_manager.fetch_all(query, dictionary=True)

    data = {}
    for row in myresult:
        keyword = row["keyword_name_ar"]
        classification = row["classification_name_ar"]
        if classification not in data:
            data[classification] = []
        data[classification].append(keyword)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"✅ MAIN_TO_SUB loaded and saved to {output_path}")
    return data

