import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_level=logging.INFO):
    """
    Configure application-wide logging
    
    Args:
        log_level: The minimum log level to capture (default: INFO)
    
    Returns:
        logger: Configured logger instance
    """
    log_directory = "logs"
    os.makedirs(log_directory, exist_ok=True)
    log_file = os.path.join(log_directory, "app.log")
    
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            root_logger.removeHandler(handler)
    
    root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name):
    """
    Get a logger for a specific module
    
    Args:
        name: Usually __name__ from the calling module
        
    Returns:
        A logger instance with the specified name
    """
    return logging.getLogger(name)