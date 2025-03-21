"""
Reusable connection management panel component.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ..styles import ColorScheme
from .status_label import StatusLabel

class ConnectionPanel(ttk.LabelFrame):
    """
    Panel for managing connection state and controls.
    
    Features:
    - Connection status display
    - Connect/Disconnect buttons  
    - Status indicators
    - Theme support
    """
    
    def __init__(
        self,
        parent,
        colors: ColorScheme,
        status_var: tk.StringVar,
        connect_callback: Callable,
        disconnect_callback: Callable,
        **kwargs
    ):
        super().__init__(
            parent,
            text="Connection",
            style="Main.TLabelframe",
            **kwargs 
        )
        
        self.colors = colors
        self.status_var = status_var
        self.connect_cb = connect_callback
        self.disconnect_cb = disconnect_callback
        
        self._setup_gui()
        
    def _setup_gui(self):
        """Setup panel components."""
        # Status display
        status_frame = ttk.Frame(self)
        status_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(
            status_frame,
            text="Status:",
            style="Title.TLabel"
        ).pack(side='left', padx=5)
        
        self.status_label = StatusLabel(
            status_frame,
            textvariable=self.status_var,
            colors=self.colors
        )
        self.status_label.pack(side='left', padx=5)
        
        # Control buttons  
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        self.connect_btn = ttk.Button(
            button_frame,
            text="Connect",
            command=self.connect_cb,
            style="Accent.TButton"
        )
        self.connect_btn.pack(side='left', padx=5)
        
        self.disconnect_btn = ttk.Button(
            button_frame,
            text="Disconnect",
            command=self.disconnect_cb,
            style="TButton"
        )
        self.disconnect_btn.pack(side='left', padx=5)
        
    def update_theme(self, colors: ColorScheme):
        """Update component with new theme colors."""
        self.colors = colors
        self.status_label.update_theme(colors)