import logging
from pathlib import Path
from datetime import datetime
from utils.file_path import LOG_DIR

def setup_logging(level=logging.INFO):
    """Set up logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    curr_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = Path(LOG_DIR / f'{curr_time}.log')
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding='utf-8')
        ]
    )