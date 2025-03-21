"""
Log viewing component with filtering and colored output.
"""

import tkinter as tk
from tkinter import ttk
import queue
import logging
from datetime import datetime
from typing import Dict, Optional

from logger import Logger, LogLevel
from gui.styles.theme import ColorScheme

class LogView(ttk.Frame):
    """Log viewer with filtering and colored output."""
    
    def __init__(self, parent, colors: ColorScheme, config=None, logger=None):
        super().__init__(parent)
        self.colors = colors
        self.config = config
        self.logger = logger or Logger()
        self.log_queue = queue.Queue()
        
        # Use LogLevel enum values for consistency
        self.level_filters = {level.name: True for level in LogLevel}
        
        self._setup_gui()
        self._setup_logging()
        
    def _setup_gui(self):
        """Setup log view interface."""
        # Filter frame
        self.filter_frame = ttk.Frame(self)
        self.filter_frame.pack(fill='x', padx=5, pady=5)
        
        # Setup log filters - use defaults if no config
        self.level_filters = {}
        for level in LogLevel:
            default_value = True
            if self.config:
                value = self.config.get(f'logs.filters.{level.name}', default_value)
            else:
                value = default_value
                
            var = tk.BooleanVar(value=value)
            self.level_filters[level.name] = var
            cb = ttk.Checkbutton(
                self.filter_frame,
                text=level.name,
                variable=var,
                command=self._apply_filters,
                style="Accent.TCheckbutton"
            )
            cb.pack(side='left', padx=5)
            
        # Log text area with custom font and colors
        self.log_text = tk.Text(
            self,
            wrap=tk.WORD,
            height=10,
            bg=self.colors.secondary_bg,      # Use theme background
            fg=self.colors.foreground,        # Use theme foreground
            font=("Cascadia Code", 10),       # Modern monospace font
            relief="flat",
            state="disabled",
            padx=10,
            pady=5
        )
        self.log_text.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Configure log level tags with purple theme
        self.log_text.tag_configure(
            'DEBUG',
            foreground=self.colors.log_debug,
            font=("Cascadia Code", 10, "bold")
        )
        self.log_text.tag_configure(
            'INFO',
            foreground=self.colors.log_info,
            font=("Cascadia Code", 10)
        )
        self.log_text.tag_configure(
            'WARNING',
            foreground=self.colors.log_warning,
            font=("Cascadia Code", 10, "bold")
        )
        self.log_text.tag_configure(
            'ERROR',
            foreground=self.colors.log_error,
            font=("Cascadia Code", 10, "bold")
        )
        self.log_text.tag_configure(
            'timestamp',
            foreground="#666666",
            font=("Cascadia Code", 10, "italic")
        )
        
    def _setup_tags(self):
        """Configure text tags for log levels."""
        level_colors = {
            'DEBUG': self.colors.log_debug,
            'INFO': self.colors.log_info,
            'WARNING': self.colors.log_warning,
            'ERROR': self.colors.log_error
        }
        
        for level, color in level_colors.items():
            self.log_text.tag_configure(level, foreground=color)
            
    def _setup_logging(self):
        """Setup logging handler and queue checking."""
        # Create custom handler
        self.handler = self.LogHandler(self.log_queue)
        self.handler.setLevel(LogLevel.DEBUG.value)
        
        # Add handler to logger
        if self.logger and hasattr(self.logger, 'logger'):
            self.logger.logger.addHandler(self.handler)
            
        # Start checking queue
        self.after(100, self._check_log_queue)
        
    def _check_log_queue(self):
        """Check for new log messages."""
        while True:
            try:
                record = self.log_queue.get_nowait()
                self._add_log_message(record)
                self.log_queue.task_done()
            except queue.Empty:
                break
        
        self.after(100, self._check_log_queue)
        
    def _add_log_message(self, record: logging.LogRecord):
        """Add a log message to the text widget."""
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
        self.log_text.configure(state='normal')
        start_index = self.log_text.index('end-1c')
        self.log_text.insert('end', f"[{timestamp}] ", ('timestamp',))
        self.log_text.insert('end', f"{record.levelname}: ", (record.levelname,))
        self.log_text.insert('end', f"{record.message}\n")
        end_index = self.log_text.index('end-1c')
        
        # Add a tag for the entire log entry with the level name
        self.log_text.tag_add(f"level_{record.levelname}", start_index, end_index)
        
        # Hide the entry if the filter is off
        if not self.level_filters[record.levelname].get():
            self.log_text.tag_configure(f"level_{record.levelname}", elide=True)
            
        self.log_text.configure(state='disabled')
        self.log_text.see('end')
        
    def _apply_filters(self):
        """Apply log level filters and save states."""
        if not self.config:
            return
            
        # Save filter states and update visibility
        self.log_text.configure(state='normal')
        for level, var in self.level_filters.items():
            self.config.set(f'logs.filters.{level}', var.get())
            # Configure the level tag to show/hide entries
            self.log_text.tag_configure(f"level_{level}", elide=not var.get())
        self.log_text.configure(state='disabled')
        
    def update_theme(self, colors: ColorScheme):
        """Update component theme colors."""
        self.colors = colors
        self.log_text.configure(
            bg=colors.secondary_bg,
            fg=colors.foreground
        )
        
        # Update log level colors
        self.log_text.tag_configure('DEBUG', foreground=colors.log_debug)
        self.log_text.tag_configure('INFO', foreground=colors.log_info)
        self.log_text.tag_configure('WARNING', foreground=colors.log_warning)  
        self.log_text.tag_configure('ERROR', foreground=colors.log_error)
        
    class LogHandler(logging.Handler):
        """Custom logging handler that writes to a queue."""
        
        def __init__(self, queue):
            super().__init__()
            self.queue = queue
            
        def emit(self, record):
            # Format the message before queuing
            record.message = record.getMessage()
            self.queue.put(record)