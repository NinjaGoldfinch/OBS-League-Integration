"""
Logging formatters and style configurations.
"""

import logging
from colorama import Fore, Style
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors and timestamp formatting to log messages.
    
    Colors are applied based on log level:
    - DEBUG: Cyan
    - INFO: Green 
    - WARNING: Yellow
    - ERROR: Red
    """
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
    }

    def formatTime(self, record, datefmt=None):
        """Format timestamp with milliseconds."""
        created = datetime.fromtimestamp(record.created)
        return created.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    def format(self, record):
        """Format log record with colors and proper indentation."""
        color = self.COLORS.get(record.levelname, Fore.WHITE)
        timestamp = self.formatTime(record)
        
        # Indent multiline messages
        message_lines = record.getMessage().split('\n')
        formatted_message = '\n    '.join(message_lines)
        
        return (
            f"{Fore.WHITE}[{timestamp}] "
            f"{color}{record.levelname:<8}{Style.RESET_ALL} "
            f"{formatted_message}"
        )