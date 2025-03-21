"""
Main application window.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from .tabs import GameTab, OBSTab, ConfigTab
from .components import LogView, StatusBar
from .styles import Theme, ColorScheme, DarkTheme, LightTheme, WidgetStyles
from .styles.notebook import configure_notebook_styles

class MainWindow:
    """Main application window controller."""
    
    DEFAULT_WIDTH = 800
    DEFAULT_HEIGHT = 600
    
    def __init__(self, obs=None, config=None, logger=None, lcu=None, tracker=None):
        self.window = tk.Tk()
        self.window.title("League OBS Integration")
        
        # Store dependencies and register callbacks immediately
        self.obs = obs
        self.config = config
        self.logger = logger
        self.lcu = lcu
        self.tracker = tracker

        # Register LCU callback before any UI initialization
        if lcu:
            lcu.set_connection_callback(self._handle_lcu_connection)
        
        if tracker:
            tracker.register_game_update_callback(self.update_game_info)

                
        # Register single callback for both connect/disconnect
        if obs:
            obs.add_connection_handler(self._handle_obs_connection)
        
        # Load window size from config if available
        if self.config:
            width = self.config.get('window.width', 800)
            height = self.config.get('window.height', 600)
            theme_name = self.config.get('theme', 'dark')
        else:
            width = 800
            height = 600
            theme_name = 'dark'
            
        self.current_theme = Theme.DARK if theme_name == 'dark' else Theme.LIGHT
        self.colors = DarkTheme() if self.current_theme == Theme.DARK else LightTheme()
        
        # Window setup
        self.window.geometry(f"{width}x{height}")
        self.window.configure(bg=self.colors.background)
        
        # Initialize UI
        self._setup_styles()
        self._create_widgets()
        
        # Set up remaining connection callbacks and update initial states
        if lcu:
            self.status_bar.update_lcu_status(lcu.is_connected)
            
            # Queue status
            #self.update_game_info(lcu.get_request('lol-gameflow_v1_session'))
            
        if obs:
            self.status_bar.update_obs_status(obs.is_connected)
            
        if config:
            self.config = config
        
    def _setup_styles(self):
        """Initialize theme styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure common styles
        style.configure(
            "Status.TFrame",
            background=self.colors.background
        )
        
        style.configure(
            "Small.TLabel",
            background=self.colors.background,
            foreground=self.colors.foreground,
            font=("Arial", 8)
        )
        
        # Configure notebook styles
        configure_notebook_styles(style, self.colors)
        
    def _create_widgets(self):
        """Create and layout window components."""
        # Main container
        self.main = ttk.Frame(self.window)
        self.main.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Create status bar first
        self.status_bar = StatusBar(self.window, self.colors)
        self.status_bar.pack(side='bottom', fill='x', padx=5, pady=2)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.main)
        self.notebook.pack(expand=True, fill='both')
        
        # Initialize tabs with dependencies
        self.game_tab = GameTab(self.notebook, self.colors, config=self.config)
        self.obs_tab = OBSTab(self.notebook, self.colors, self.obs, config=self.config)
        self.config_tab = ConfigTab(
            parent=self.notebook,
            colors=self.colors,
            config=self.config,  # Make sure config is properly passed
            callback=self._handle_config_changed
        )
        
        # Add tabs
        self.notebook.add(self.game_tab, text="Game")
        self.notebook.add(self.obs_tab, text="OBS")
        self.notebook.add(self.config_tab, text="Settings")
        
        # Log view
        self.log_view = LogView(self.window, self.colors, self.config, self.logger)
        self.log_view.pack(fill='x', padx=5, pady=5)
        
    def start(self):
        """Start the GUI event loop."""
        self.window.mainloop()
        
    def stop(self):
        """Clean up and close the window."""
        if self.window:
            self.window.quit()
            
    def update_theme(self, colors: ColorScheme):
        """Update theme colors."""
        self.colors = colors
        self._setup_styles()
        
        # Update child components
        self.status_bar.update_theme(colors)
        self.log_view.update_theme(colors)
        self.game_tab.update_theme(colors)
        self.obs_tab.update_theme(colors)
        self.config_tab.update_theme(colors)
        
    def _handle_config_changed(self):
        """Handle configuration changes."""
        # Update theme if changed
        theme_name = self.config.get('theme', 'dark')
        new_theme = Theme.DARK if theme_name == 'dark' else Theme.LIGHT
        
        if new_theme != self.current_theme:
            self.current_theme = new_theme
            self.colors = DarkTheme() if new_theme == Theme.DARK else LightTheme()
            self.update_theme(self.colors)
            
    def _handle_obs_connection(self, connected: bool):
        """Handle OBS connection status changes."""
        self.status_bar.update_obs_status(connected)
        if self.logger:
            self.logger.info(f"OBS {'connected' if connected else 'disconnected'}")
        
    def update_lcu_status(self, connected: bool):
        """Update League Client connection status."""
        self.status_bar.update_lcu_status(connected)

    def _handle_lcu_connection(self, connected: bool):
        """Handle League Client connection status changes."""
        self.logger.info(f"LCU connection callback triggered: {'Connected' if connected else 'Disconnected'}")
        self.status_bar.update_lcu_status(connected)

    def update_game_info(self, game_type: str, game_info: dict):
        """
        Update game-related information in the UI.
        
        Args:
            game_type: Type of game update (e.g., 'gameflow', 'champselect')
            game_info: Dictionary containing game state information
        """
        try:
            # Pass game info update to game tab
            if hasattr(self, 'game_tab'):
                self.game_tab.update_game_info(game_type, game_info)
                        
        except AttributeError as e:
            if self.logger:
                self.logger.error(f"Missing required attribute for game updates: {e}")
                self.logger.debug(f"Game info update failed - type: {game_type}, data: {game_info}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to update game info: {e}")