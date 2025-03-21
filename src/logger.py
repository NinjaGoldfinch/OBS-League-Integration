"""
Logging system configuration.
Handles both file and console output with proper formatting.
"""

import logging
import sys
from enum import Enum
from pathlib import Path
from typing import Optional
from datetime import datetime

from utils.log_formatting import ColoredFormatter

class LogLevel(Enum):
    """Log level enumeration matching standard logging levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR

class Logger:
    """Centralized logging configuration."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize logging system."""
        self.logger = logging.getLogger('LeagueOBS')
        self.logger.setLevel(LogLevel.DEBUG.value)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
            
        # Setup log directory
        if log_dir is None:
            log_dir = Path.home() / "AppData" / "Local" / "LeagueOBSIntegration" / "logs"
        else:
            log_dir = Path(log_dir)
            
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"league_obs_{timestamp}.log"
        
        # File handler with detailed formatting
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s.%(msecs)03d %(levelname)-8s %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("Logging system initialized")
        self.logger.debug(f"Log file created at: {log_file}")
    
    def debug(self, msg: str):
        """Log debug message."""
        self.logger.debug(msg)
    
    def info(self, msg: str):
        """Log info message."""
        self.logger.info(msg)
    
    def warning(self, msg: str):
        """Log warning message."""
        self.logger.warning(msg)
    
    def error(self, msg: str):
        """Log error message."""
        self.logger.error(msg)

# Make sure LogLevel is available when importing from logger
__all__ = ['Logger', 'LogLevel']