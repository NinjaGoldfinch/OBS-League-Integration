"""
Base class for application tabs.
"""

from tkinter import ttk
from typing import Optional
from ..styles import ColorScheme

class BaseTab(ttk.Frame):
    """Base class for all application tabs."""
    
    title = "Untitled"
    
    def __init__(self, parent, colors: ColorScheme, config=None, logger=None):
        super().__init__(parent)
        self.colors = colors
        self.config = config
        self.logger = logger
        self._setup_gui()
        
    def _setup_gui(self):
        """Setup tab GUI components. Override in subclasses."""
        raise NotImplementedError
        
    def update_theme(self, colors: ColorScheme):
        """Update tab with new theme colors."""
        self.colors = colors