"""
GUI initialization and management module.
"""

from .main_window import MainWindow

class GUI:
    """
    Main GUI controller that manages window lifecycle and dependencies.
    
    Attributes:
        obs: OBS WebSocket client
        config: Configuration manager
        logger: Application logger
        lcu: League Client API
        window: Main application window
    """
    
    def __init__(self, obs=None, config=None, logger=None, lcu=None, tracker=None):
        """
        Initialize GUI controller with dependencies.
        
        Args:
            obs: OBS WebSocket client
            config: Configuration manager
            logger: Application logger
            lcu: League Client API
            tracker: Game tracker
        """
        self.obs = obs
        self.config = config
        self.logger = logger
        self.lcu = lcu
        self.tracker = tracker
        self.window = None
        # Track states before window is created
        self._pending_lcu_status = False
        self._pending_obs_status = False
        
        # Register callbacks with tracker instead of LCU directly

    def initialize(self):
        """
        Initialize GUI components without starting the main loop.
        Creates the main window and sets up all UI components.
        """
        if self.window:
            self.logger.warning("GUI already initialized")
            return
            
        self.logger.debug("Initializing GUI components")
        self.window = MainWindow(
            obs=self.obs,
            config=self.config,
            logger=self.logger,
            lcu=self.lcu,
            tracker=self.tracker
        )
        
        # Apply any pending status updates
        if self._pending_lcu_status:
            self.window.status_bar.update_lcu_status(self._pending_lcu_status)
        if self._pending_obs_status:
            self.window.status_bar.update_obs_status(self._pending_obs_status)
            
        self.logger.info("GUI initialization complete")

    def start(self):
        """
        Start the GUI main loop.
        Must be called after initialize().
        
        Raises:
            RuntimeError: If GUI has not been initialized
        """
        if not self.window:
            raise RuntimeError("GUI must be initialized before starting")
        self.logger.info("Starting GUI main loop")
        self.window.start()

    def stop(self):
        """Clean up and close the window."""
        if self.window:
            self.logger.info("Stopping GUI")
            self.window.stop()
            self.window = None
            
    def update_lcu_status(self, connected: bool):
        """Update LCU connection status in GUI."""
        self._pending_lcu_status = connected
        if self.window:
            self.window.status_bar.update_lcu_status(connected)
            
    def update_obs_status(self, connected: bool):
        """Update OBS connection status."""
        self._pending_obs_status = connected
        if self.window:
            self.window.status_bar.update_obs_status(connected)