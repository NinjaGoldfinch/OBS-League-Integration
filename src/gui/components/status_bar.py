"""
Status bar component for displaying application state.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from ..styles import ColorScheme
from .status_label import StatusLabel

class StatusBar(ttk.Frame):
    """Status bar showing connection and version information."""
    
    def __init__(self, parent, colors: ColorScheme):
        super().__init__(parent)
        self.colors = colors
        self.configure(style="Status.TFrame")
        
        # Create frames for each section
        lcu_frame = ttk.Frame(self, style="Status.TFrame")
        lcu_frame.pack(side='left', padx=5)
        
        obs_frame = ttk.Frame(self, style="Status.TFrame")
        obs_frame.pack(side='left', padx=5)
        
        # Create StringVars for dynamic updates
        self.lcu_status_var = tk.StringVar(value="Disconnected")
        self.obs_status_var = tk.StringVar(value="Disconnected")
        
        # LCU status section
        StatusLabel(
            lcu_frame,
            text="League Client:",
            colors=colors
        ).pack(side='left', padx=2)
        
        # Create and pack widgets separately
        self.lcu_status = StatusLabel(
            lcu_frame,
            textvariable=self.lcu_status_var,
            colors=colors
        )
        self.lcu_status.pack(side='left')
        
        # OBS status section
        StatusLabel(
            obs_frame,
            text="OBS:",
            colors=colors
        ).pack(side='left', padx=2)
        
        self.obs_status = StatusLabel(
            obs_frame,
            textvariable=self.obs_status_var,
            colors=colors
        )
        self.obs_status.pack(side='left')
        
        # Version on right
        self.version = StatusLabel(
            self,
            text="League OBS Integration v1.0.0",
            colors=colors
        )
        self.version.pack(side='right', padx=5)
    
    def update_lcu_status(self, connected: bool):
        """Update League Client connection status."""
        status = "Connected" if connected else "Disconnected"
        self.lcu_status_var.set(status)
        self.lcu_status.update_idletasks()

    def update_obs_status(self, connected: bool):
        """Update OBS connection status."""
        status = "Connected" if connected else "Disconnected"
        self.obs_status_var.set(status)  # Just set the status without "OBS:"
        self.obs_status.update_idletasks()
    
    def update_theme(self, colors: ColorScheme):
        """Update status bar theme colors."""
        self.colors = colors
        self.configure(style="Status.TFrame")
        
        # Update child labels
        for child in (self.lcu_status, self.obs_status, self.version):
            child.update_theme(colors)