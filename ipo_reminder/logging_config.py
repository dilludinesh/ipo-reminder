"""
Centralized logging configuration for the IPO Reminder system.

This module provides a consistent logging configuration across the entire application,
with support for different log levels, file rotation, and structured logging.
"""
import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any, Union
import json
from datetime import datetime

# Log levels as strings for configuration
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Default log format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_JSON_FORMAT = {
    'timestamp': '%(asctime)s',
    'name': '%(name)s',
    'level': '%(levelname)s',
    'message': '%(message)s',
    'module': '%(module)s',
    'function': '%(funcName)s',
    'line': '%(lineno)d',
    'process': '%(process)d',
    'thread': '%(thread)d',
}

class JsonFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string."""
        log_record = {}
        
        # Add default fields
        for field, fmt in DEFAULT_JSON_FORMAT.items():
            log_record[field] = fmt % {
                'asctime': self.formatTime(record, self.datefmt),
                'name': record.name,
                'levelname': record.levelname,
                'message': record.getMessage(),
                'module': record.module,
                'funcName': record.funcName,
                'lineno': record.lineno,
                'process': record.process,
                'thread': record.thread,
            }
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        # Add any extra attributes
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            log_record.update(record.extra)
        
        return json.dumps(log_record, ensure_ascii=False)

def get_log_level(level_name: str) -> int:
    """Get the logging level from a string name."""
    return LOG_LEVELS.get(level_name.upper(), logging.INFO)

def setup_logging(
    log_level: str = 'INFO',
    log_file: Optional[str] = None,
    log_format: str = 'text',
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file. If None, logs only to console.
        log_format: Log format ('text' or 'json')
        max_bytes: Maximum log file size in bytes before rotation
        backup_count: Number of backup log files to keep
    """
    # Convert log level to numeric value
    level = get_log_level(log_level)
    
    # Create formatter based on format type
    if log_format.lower() == 'json':
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file).absolute()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use RotatingFileHandler for log rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure third-party loggers
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('aioredis').setLevel(logging.INFO)

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name. If None, returns the root logger.
    """
    return logging.getLogger(name)

# Initialize logging with default configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'text')

setup_logging(
    log_level=LOG_LEVEL,
    log_file=LOG_FILE,
    log_format=LOG_FORMAT,
)

# Create a default logger for this module
logger = get_logger(__name__)

# Log the logging configuration
logger.info("Logging configured with level=%s, format=%s, file=%s", 
           LOG_LEVEL, LOG_FORMAT, LOG_FILE or 'console')
