"""
Custom status label component with theme support.
"""

import tkinter as tk 
from tkinter import ttk
from typing import Optional

from ..styles.theme import ColorScheme  # Update import path

class StatusLabel(ttk.Label):
    """Enhanced status label with theme support."""
    
    def __init__(self, parent, colors: ColorScheme, textvariable: Optional[tk.StringVar] = None, **kwargs):
        # Initialize base widget first
        super().__init__(parent, style="Status.TLabel", **kwargs)
        
        self.colors = colors
        self._setup_styles()
        
        # Handle text variable
        if textvariable:
            self._textvariable = textvariable
            self.configure(textvariable=textvariable)
            textvariable.trace_add('write', self._on_var_change)
            # Set initial text
            self.configure(text=textvariable.get())
            
    def _on_var_change(self, *args):
        """Handle variable changes."""
        if hasattr(self, '_textvariable'):
            new_text = self._textvariable.get()
            self.configure(text=new_text)
            self.update()
            self.update_idletasks()
        
    def _setup_styles(self):
        """Configure label styles."""
        style = ttk.Style()
        
        style.configure(
            "Status.TLabel",
            background=self.colors.background,
            foreground=self.colors.accent_light,
            font=("Arial", 9, "bold"),
            padding=(5, 2)
        )
        
        style.map(
            "Status.TLabel", 
            foreground=[
                ("disabled", self.colors.disabled_fg),
                ("readonly", self.colors.secondary_fg)
            ]
        )
    
    def update_theme(self, colors: ColorScheme):
        """Update theme colors."""
        self.colors = colors
        self._setup_styles()