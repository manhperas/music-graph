"""Utility functions for data collection"""

import logging
import time
from typing import Optional
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def rate_limit(delay: float = 1.0):
    """Decorator to add rate limiting to functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            time.sleep(delay)
            return result
        return wrapper
    return decorator


def log_progress(current: int, total: int, prefix: str = "Progress"):
    """Log progress in a readable format"""
    percentage = (current / total) * 100 if total > 0 else 0
    logger.info(f"{prefix}: {current}/{total} ({percentage:.1f}%)")


def safe_get(dictionary: dict, key: str, default: Optional[str] = None) -> Optional[str]:
    """Safely get a value from a dictionary"""
    try:
        return dictionary.get(key, default)
    except Exception as e:
        logger.warning(f"Error getting key '{key}': {e}")
        return default


def clean_text(text: Optional[str]) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = " ".join(text.split())
    return text.strip()


