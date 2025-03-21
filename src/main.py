"""
League Client OBS Integration
Main entry point that initializes and coordinates all components.

This module sets up the core application components:
- League Client authentication and API
- OBS WebSocket client
- GUI interface
- Game state tracking
"""

import sys
from typing import Optional

# Core components
from auth import LeagueClientAuth 
from api import LCUApi
from obs_client import OBSClient

# UI and state management
from gui import GUI  # This will now work correctly
from logic import GameTracker

# Utilities
from logger import Logger
from config import ConfigManager

class Application:
    """
    Main application controller that manages component lifecycle.
    
    Attributes:
        logger (Logger): Application logger
        config (ConfigManager): Configuration manager
        obs (OBSClient): OBS WebSocket client
        auth (LeagueClientAuth): League client authentication
        api (LCUApi): League client API
        gui (GUI): Application GUI
        tracker (GameTracker): Game state tracker
    """
    
    def __init__(self):
        """Initialize application components."""
        # Initialize logger first with proper setup
        try:
            self.logger = Logger()
            self.logger.info("Starting League OBS Integration")
        except Exception as e:
            print(f"Failed to initialize logging: {e}")
            sys.exit(1)
        
        # Initialize config with logging
        try:
            self.config = ConfigManager()
            if not self.config.enabled:
                self.logger.warning("Config system not fully initialized, using defaults")
        except Exception as e:
            self.logger.error(f"Failed to initialize config: {e}")
            raise RuntimeError("Cannot start without configuration system")
        
        # Initialize core components first
        self.auth = LeagueClientAuth()
        self.api = LCUApi(self.auth)
        
        # Initialize OBS client
        self.obs = OBSClient(
            host=self.config.get('obs.host', 'localhost'),
            port=self.config.get('obs.port', 4455),
            password=self.config.get('obs.password', '')
        )
        
        # Initialize game tracker before GUI
        self.tracker = GameTracker(self.auth, self.api, self.obs)
        
        # Create GUI with all dependencies
        self.gui = GUI(
            obs=self.obs,
            config=self.config,
            logger=self.logger,
            lcu=self.api,
            tracker=self.tracker  # Pass tracker to GUI
        )
        
        # Set up event handlers
        self.config.add_change_handler('obs', self._handle_obs_config_change)
        self.auth.add_connection_callback(self._handle_lcu_connection)

    def _handle_obs_config_change(self, changes: dict):
        """Handle OBS configuration changes."""
        self.obs.update_settings(
            host=self.config.get('obs.host', 'localhost'),
            port=self.config.get('obs.port', 4455),
            password=self.config.get('obs.password', '')
        )

    def _handle_lcu_connection(self, connected: bool):
        """Handle LCU connection status changes."""
        self.gui.update_lcu_status(connected)

    def _setup_obs(self) -> OBSClient:
        """Initialize OBS client with config settings."""
        return OBSClient(
            host=self.config.get('obs.host', 'localhost'),
            port=self.config.get('obs.port', 4455),
            password=self.config.get('obs.password', '')
        )

    def start(self):
        """Start all application components."""
        try:
            # Initialize GUI first to register callbacks
            self.logger.info("Initializing GUI...")
            self.gui.initialize()
            
            # Start services after GUI is ready
            self.logger.info("Starting League Client monitoring...")
            self.auth.start_monitoring()
            
            self.logger.info("Starting League Client API...")
            self.api.start()
            
            self.logger.info("Starting game tracker...")
            self.tracker.start()
            
            # Auto-connect to OBS if configured
            if self.config.get('obs.auto_connect', False):
                self.logger.info("Auto-connecting to OBS...")
                self.obs.connect()
            
            # Finally start GUI main loop
            self.logger.info("Starting main window...")
            self.gui.start()
            
        except Exception as e:
            self.logger.error(f"Fatal error: {str(e)}")
            self._cleanup()
            sys.exit(1)

    def _cleanup(self):
        """Clean up and stop all components."""
        components = [
            self.tracker,
            self.auth,
            self.api,
            self.obs,
            self.gui
        ]
        
        for component in components:
            try:
                if hasattr(component, 'stop'):
                    component.stop()
            except Exception as e:
                self.logger.error(f"Error stopping {component.__class__.__name__}: {e}")

def main():
    """Application entry point."""
    app = Application()
    app.start()

if __name__ == "__main__":
    main()