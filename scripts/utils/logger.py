import logging
import sys
from pathlib import Path
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    """
    Configure and return a logger instance with both file and console handlers
    
    Args:
        name: Name of the logger (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Only add handlers if the logger doesn't already have them
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Create file handler
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            logs_dir / f'blog_publisher_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger