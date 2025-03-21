"""
Configuration settings tab.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

# Fix the import path for ColorScheme
from ..styles import ColorScheme

from ..components import StatusLabel
from .base_tab import BaseTab


class ConfigTab(ttk.Frame):
    """Settings and configuration interface."""
    
    title = "Settings"
    
    def __init__(self, parent: ttk.Notebook, colors: ColorScheme, config=None, callback: Optional[Callable] = None):
        super().__init__(parent)
        self.colors = colors
        self.config = config
        self.callback = callback
        # Initialize variables with defaults
        self.theme_var = tk.StringVar(value='dark')
        self.obs_host = tk.StringVar(value='localhost')
        self.obs_port = tk.StringVar(value='4455')
        self.obs_password = tk.StringVar(value='')
        self.obs_autoconnect = tk.BooleanVar(value=False)
        
        # Store references
        self.config = config
        self.callback = callback
        
        # Load config if available
        if self.config:
            self.theme_var.set(config.get('theme', 'dark'))
            self.obs_host.set(config.get('obs.host', 'localhost'))
            self.obs_port.set(str(config.get('obs.port', 4455)))
            self.obs_password.set(config.get('obs.password', ''))
            self.obs_autoconnect.set(config.get('obs.auto_connect', False))
        
        self._setup_gui()

    def _setup_gui(self):
        """Setup configuration interface."""
        # Theme settings
        theme_frame = ttk.LabelFrame(
            self, 
            text="Theme",
            style="Main.TLabelframe"
        )
        theme_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Radiobutton(
            theme_frame,
            text="Dark Theme",
            value="dark",
            variable=self.theme_var,
            command=self._save_settings,
            style="TRadiobutton"
        ).pack(side='left', padx=10, pady=5)
        
        ttk.Radiobutton(
            theme_frame,
            text="Light Theme", 
            value="light",
            variable=self.theme_var,
            command=self._save_settings,
            style="TRadiobutton"
        ).pack(side='left', padx=10, pady=5)
        
        # OBS Settings
        obs_frame = ttk.LabelFrame(
            self,
            text="OBS Connection Settings",
            style="Main.TLabelframe"
        )
        obs_frame.pack(fill='x', padx=5, pady=5)
        
        # Host setting
        host_frame = ttk.Frame(obs_frame)
        host_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(
            host_frame,
            text="Host:",
            style="Title.TLabel"
        ).pack(side='left', padx=5)
        
        host_entry = ttk.Entry(
            host_frame,
            textvariable=self.obs_host
        )
        host_entry.pack(side='left', padx=5, fill='x', expand=True)
        host_entry.bind('<Return>', lambda e: self._save_settings())
        
        # Port setting
        port_frame = ttk.Frame(obs_frame)
        port_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(
            port_frame,
            text="Port:",
            style="Title.TLabel"
        ).pack(side='left', padx=5)
        
        port_entry = ttk.Entry(
            port_frame,
            textvariable=self.obs_port,
            width=10,
            validate='key',
            validatecommand=(self.register(self._validate_port), '%P')
        )
        port_entry.pack(side='left', padx=5)
        port_entry.bind('<Return>', lambda e: self._save_settings())
        
        # Password setting
        pass_frame = ttk.Frame(obs_frame)
        pass_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(
            pass_frame,
            text="Password:",
            style="Title.TLabel"
        ).pack(side='left', padx=5)
        
        password_entry = ttk.Entry(
            pass_frame,
            textvariable=self.obs_password,
            show="*"
        )
        password_entry.pack(side='left', padx=5, fill='x', expand=True)
        password_entry.bind('<Return>', lambda e: self._save_settings())
        
        # Auto-connect setting
        ttk.Checkbutton(
            obs_frame,
            text="Auto-connect on startup",
            variable=self.obs_autoconnect,
            command=self._save_settings,
            style="TCheckbutton"
        ).pack(padx=5, pady=5)
        
        # Log filters
        log_frame = ttk.LabelFrame(
            self,
            text="Log Settings",
            style="Main.TLabelframe"
        )
        log_frame.pack(fill='x', padx=5, pady=5)
        
        # Log level filters with default values if no config
        filter_frame = ttk.Frame(log_frame)
        filter_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(
            filter_frame,
            text="Show log levels:",
            style="Title.TLabel"
        ).pack(side='left', padx=5)
        
        # Store filter variables
        self.log_filters = {}
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            # Get value from config if available, otherwise use default
            default_value = True
            if self.config:
                value = self.config.get(f'logs.filters.{level}', default_value)
            else:
                value = default_value
                
            var = tk.BooleanVar(value=value)
            self.log_filters[level] = var
            
            cb = ttk.Checkbutton(
                filter_frame,
                text=level,
                variable=var,
                command=lambda l=level: self._save_log_filter(l),
                style="TCheckbutton"
            )
            cb.pack(side='left', padx=5)

    def _validate_port(self, value):
        """Validate port number input."""
        if value == "":
            return True
        try:
            port = int(value)
            return 0 <= port <= 65535
        except ValueError:
            return False

    def _save_settings(self):
        """Save current settings to config."""
        
        if not self.config:
            messagebox.showerror(
                "Error Saving Settings",
                "Failed to save settings: Configuration system not initialized."
            )
            return

        try:
            # Save OBS settings
            self.config.set('obs.host', self.obs_host.get())
            self.config.set('obs.port', int(self.obs_port.get()))
            self.config.set('obs.password', self.obs_password.get())
            self.config.set('obs.auto_connect', self.obs_autoconnect.get())
            
            # Save theme setting
            self.config.set('theme', self.theme_var.get())
            
            # Save log filters
            for level, var in self.log_filters.items():
                self.config.set(f'logs.filters.{level}', var.get())
            
            # Show success message
            messagebox.showinfo(
                "Settings Saved",
                "Your settings have been saved successfully."
            )
            
            # Trigger callback if provided (e.g., for theme changes)
            if self.callback:
                self.callback()
                
        except Exception as e:
            messagebox.showerror(
                "Error Saving Settings",
                f"Failed to save settings: {str(e)}"
            )

    def _save_log_filter(self, level: str):
        """Save individual log filter setting."""
        if not self.config or level not in self.log_filters:
            return
            
        self.config.set(f'logs.filters.{level}', self.log_filters[level].get())

    def update_theme(self, colors: ColorScheme):
        """Update the tab's theme colors."""
        self.colors = colors
        
        # Update all widget styles
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                child.configure(style="Main.TLabelframe")
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Label):
                        subchild.configure(style="Title.TLabel")
                    elif isinstance(subchild, ttk.Frame):
                        for widget in subchild.winfo_children():
                            if isinstance(widget, ttk.Label):
                                widget.configure(style="Title.TLabel")
                            elif isinstance(widget, ttk.Entry):
                                widget.configure(style="TEntry")
                            elif isinstance(widget, ttk.Checkbutton):
                                widget.configure(style="TCheckbutton")
                            elif isinstance(widget, ttk.Radiobutton):
                                widget.configure(style="TRadiobutton")