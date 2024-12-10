import logging
import sys
from pathlib import Path
from datetime import datetime
import os
from typing import Optional

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger with both console and file handlers
    
    Args:
        name: Logger name
        log_file: Optional log file path. If None, only console logging is enabled
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handlers if none exist
    if not logger.handlers:
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
        # File handler (if log_file specified)
        if log_file:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)
        
        # Set overall logger level to DEBUG to capture all logs
        logger.setLevel(logging.DEBUG)
        
        logger.info(f"Logger initialized: {name}")
        if log_file:
            logger.info(f"Logging to file: {log_file}")
    
    return logger

def setup_default_logging():
    """
    Setup default logging configuration for the entire application
    """
    # Create logs directory in project root
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = logs_dir / f'blog_automation_{timestamp}.log'
    
    # Root logger configuration
    root_logger = get_logger('blog_automation', str(log_file))
    
    # Set log level from environment variable
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    root_logger.setLevel(getattr(logging, log_level))
    
    return root_logger

def log_execution_time(logger):
    """
    Decorator to log function execution time
    
    Usage:
        @log_execution_time(logger)
        def my_function():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.debug(f"Starting {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration = end_time - start_time
                logger.debug(f"Completed {func.__name__} in {duration}")
                return result
            except Exception as e:
                end_time = datetime.now()
                duration = end_time - start_time
                logger.error(f"Error in {func.__name__} after {duration}: {str(e)}")
                raise
        return wrapper
    return decorator