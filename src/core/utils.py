# src/core/utils.py (NEW FILE)
import logging
from datetime import datetime
import sys

def setup_logging():
    """تنظیم ساختار لاگ‌گیری برای ذخیره در فایل و نمایش خطاها در کنسول."""
    log_filename = datetime.now().strftime("app_log_%Y%m%d.txt")
    
    logger = logging.getLogger('PIPEDREAM')
    logger.setLevel(logging.INFO)
    
    # 1. File Handler: ذخیره تمام پیام‌ها در فایل
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    # فرمت شامل زمان، سطح خطا و ماژول
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 2. Console Handler: نمایش فقط اخطارها و ارورها در ترمینال
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    logger.info("--- Logging System Initialized ---")
    return logger

# ایجاد نمونه سراسری Logger برای استفاده در کل برنامه
LOGGER = setup_logging()