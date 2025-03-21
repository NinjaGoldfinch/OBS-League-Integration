import threading
import time
from typing import Optional, Dict, Callable, List
from obswebsocket import obsws, requests, events
from logger import Logger

class OBSClient:
    """
    OBS WebSocket client that handles connections and events.
    
    Attributes:
        logger (Logger): Logger instance
        host (str): OBS WebSocket host
        port (int): OBS WebSocket port
        password (str): OBS WebSocket password
    """
    
    def __init__(self, host: str = "localhost", port: int = 4455, password: str = ""):
        self.logger = Logger()
        self.host = host
        self.port = port
        self.password = password
        
        self._ws: Optional[obsws] = None
        self._running = False
        self._connected = False
        self._profiles: List[str] = []
        self._recording = False
        
        # Locks for thread safety
        self._connection_lock = threading.Lock()
        self._operation_lock = threading.Lock()
        
        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Background thread
        self._bg_thread = None

        self._connection_callbacks: List[Callable[[bool], None]] = []
        self._connection_handlers: List[Callable[[bool], None]] = []  # Changed to handle connection state
        self._disconnection_handlers: List[Callable] = []

    @property
    def connected(self) -> bool:
        """Get connection state."""
        return self._connected

    def _on_recording_state_changed(self, event):
        """Handle recording state change events"""
        try:
            # OBS WebSocket v5 uses 'outputActive' in datain
            if hasattr(event, 'datain'):
                self._recording = event.datain.get('outputActive', False)
                self.logger.debug(f"Recording state changed to: {self._recording}")
                # Trigger any registered callbacks
                if 'RecordStateChanged' in self._event_handlers:
                    for callback in self._event_handlers['RecordStateChanged']:
                        try:
                            callback(self._recording)
                        except Exception as e:
                            self.logger.error(f"Error in recording state callback: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error handling recording state change: {str(e)}")
            self._recording = False

    def _connect(self):
        """Establish connection to OBS WebSocket"""
        with self._connection_lock:
            try:
                self.logger.info(f"Connecting to OBS WebSocket at {self.host}:{self.port}...")
                self._ws = obsws(self.host, self.port, self.password)
                self._ws.register(self._on_recording_state_changed, events.RecordStateChanged)
                
                # Connect and verify connection
                self._ws.connect()
                response = self._ws.call(requests.GetVersion())
                
                if response:
                    self._connected = True
                    self._update_profiles()
                    return True
                    
                raise ConnectionError("No response from OBS")
                    
            except Exception as e:
                self.logger.error(f"Connection failed: {str(e)}")
                self._connected = False
                if self._ws:
                    self._ws.disconnect()
                return False

    def _update_profiles(self):
        """Get available profiles from OBS"""
        with self._operation_lock:
            try:
                response = self._ws.call(requests.GetProfileList())
                if hasattr(response, 'datain') and 'profiles' in response.datain:
                    self._profiles = response.datain['profiles']
                    self.logger.debug(f"Retrieved profiles: {self._profiles}")
                else:
                    self.logger.error("Unexpected response format from GetProfileList")
                    self._profiles = []
            except Exception as e:
                self.logger.error(f"Failed to get profiles: {str(e)}")
                self._profiles = []

    def get_profiles(self) -> List[str]:
        """Get available OBS profiles and update internal list"""
        if not self._connected:
            self.logger.error("Not connected to OBS")
            return []
            
        try:
            self._update_profiles()
            return self._profiles
        except Exception as e:
            self.logger.error(f"Failed to get profiles: {str(e)}")
            return []

    def _run_client(self):
        """Main client loop running in separate thread"""
        while self._running:
            try:
                if not self._connected:
                    success = self._connect()
                    if success:
                        self._update_profiles()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"WebSocket error: {str(e)}")
                if self._running:
                    self.logger.info("Attempting to reconnect...")
                    time.sleep(1)
            finally:
                if self._ws and not self._running:
                    self._ws.disconnect()
                    self._connected = False

        self.logger.debug("OBS WebSocket client thread ending")

    # Public API
    def start(self) -> bool:
        """Start the OBS WebSocket client"""
        if self._running:
            return False
            
        self._running = True
        success = self.connect(callback=self._on_connect_complete)
        return success

    def _on_connect_complete(self, success: bool):
        """Handle connection completion"""
        if success:
            # Start background thread for keepalive
            self._bg_thread = threading.Thread(target=self._keepalive_loop)
            self._bg_thread.daemon = True
            self._bg_thread.start()
        else:
            self._running = False

    def _keepalive_loop(self):
        """Background thread for keepalive"""
        while self._running and self._connected:
            try:
                with self._operation_lock:
                    self._ws.call(requests.GetVersion())
                time.sleep(5)
            except Exception:
                break
                
        self._connected = False

    def stop(self) -> bool:
        """Stop the OBS WebSocket client"""
        if not self._running:
            return True
            
        try:
            self.logger.info("Stopping OBS WebSocket client...")
            self._running = False
            
            # Handle WebSocket disconnect
            if self._ws:
                try:
                    self._ws.disconnect()
                except Exception as e:
                    self.logger.error(f"Error disconnecting WebSocket: {str(e)}")
            
            # Handle thread cleanup
            if self._bg_thread and self._bg_thread.is_alive():
                try:
                    self._bg_thread.join(timeout=1)
                except Exception as e:
                    self.logger.error(f"Error joining thread: {str(e)}")
            
            self._connected = False
            self._ws = None
            self._bg_thread = None
            self.logger.info("OBS WebSocket client stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping client: {str(e)}")
            return False

    def set_profile(self, profile_name: str, callback: Optional[Callable[[bool], None]] = None) -> bool:
        """Set OBS profile with optional callback"""
        if not self._connected:
            self.logger.error("Not connected to OBS")
            if callback:
                callback(False)
            return False
            
        def _set_profile():
            try:
                with self._operation_lock:
                    # First verify profile exists
                    if profile_name not in self._profiles:
                        self.logger.error(f"Profile '{profile_name}' not found")
                        if callback:
                            callback(False)
                        return False
                    
                    # For OBS WebSocket v5, call with parameters directly
                    try:
                        # Create request with proper parameters
                        response = self._ws.call(requests.SetCurrentProfile(**{
                            'profile-name': profile_name
                        }))
                        
                        # In v5, no response means success
                        success = True
                        
                        if success:
                            self.logger.info(f"Changed profile to: {profile_name}")
                        else:
                            self.logger.error(f"Failed to change profile - unexpected response")
                            
                        if callback:
                            callback(success)
                        return success
                            
                    except obsws.exceptions.OBSWebSocketError as e:
                        self.logger.error(f"OBS WebSocket error: {str(e)}")
                        if callback:
                            callback(False)
                        return False
                        
            except Exception as e:
                self.logger.error(f"Failed to set profile: {str(e)}")
                if callback:
                    callback(False)
                return False
        
        thread = threading.Thread(target=_set_profile)
        thread.daemon = True
        thread.start()
        return True

    def start_recording(self, callback: Optional[Callable[[bool], None]] = None) -> bool:
        """Start recording with optional callback"""
        if not self._connected:
            self.logger.error("Not connected to OBS")
            if callback:
                callback(False)
            return False
            
        def _start_recording():
            try:
                with self._operation_lock:
                    response = self._ws.call(requests.StartRecord())
                    success = hasattr(response, 'status') and response.status
                    if success:
                        self._recording = True
                        self.logger.info("Started recording")
                    if callback:
                        callback(success)
                    return success
            except Exception as e:
                self.logger.error(f"Failed to start recording: {str(e)}")
                if callback:
                    callback(False)
                return False
        
        thread = threading.Thread(target=_start_recording)
        thread.daemon = True
        thread.start()
        return True

    def stop_recording(self, callback: Optional[Callable[[bool], None]] = None) -> bool:
        """Stop recording with optional callback"""
        if not self._connected:
            self.logger.error("Not connected to OBS")
            if callback:
                callback(False)
            return False
            
        def _stop_recording():
            try:
                with self._operation_lock:
                    response = self._ws.call(requests.StopRecord())
                    success = hasattr(response, 'status') and response.status
                    if success:
                        self._recording = False
                        self.logger.info("Stopped recording")
                    if callback:
                        callback(success)
                    return success
            except Exception as e:
                self.logger.error(f"Failed to stop recording: {str(e)}")
                if callback:
                    callback(False)
                return False
        
        thread = threading.Thread(target=_stop_recording)
        thread.daemon = True
        thread.start()
        return True

    def register_event_handler(self, event_type: str, callback: Callable):
        """Register a callback for specific events"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(callback)

    def connect(self, callback: Optional[Callable[[bool], None]] = None) -> bool:
        """Connect to OBS WebSocket with callback"""
        if self._connected:
            if callback:
                callback(True)
            return True

        def _connect_thread():
            try:
                with self._connection_lock:
                    self.logger.info(f"Connecting to OBS WebSocket at {self.host}:{self.port}...")
                    self._ws = obsws(self.host, self.port, self.password)
                    self._ws.register(self._on_recording_state_changed, events.RecordStateChanged)
                    
                    # Connect and verify connection
                    self._ws.connect()
                    response = self._ws.call(requests.GetVersion())
                    
                    if response:
                        self._connected = True
                        self._update_profiles()
                        self._notify_connection_state(True)  # Changed to use new notification
                        if callback:
                            callback(True)
                        return True
                        
                    raise ConnectionError("No response from OBS")
                        
            except Exception as e:
                self.logger.error(f"Connection failed: {str(e)}")
                self._connected = False
                if self._ws:
                    self._ws.disconnect()
                if callback:
                    callback(False)
                return False

        thread = threading.Thread(target=_connect_thread)
        thread.daemon = True
        thread.start()
        return True

    def get_profiles(self, callback: Optional[Callable[[List[str]], None]] = None) -> bool:
        """Get available OBS profiles with callback"""
        if not self._connected:
            self.logger.error("Not connected to OBS")
            if callback:
                callback([])
            return False
                
        def _get_profiles_thread():
            try:
                with self._operation_lock:
                    response = self._ws.call(requests.GetProfileList())
                    if hasattr(response, 'datain'):
                        self._profiles = response.datain.get('profiles', [])
                        self.logger.debug(f"Retrieved profiles: {self._profiles}")
                        if callback:
                            callback(self._profiles)
                    else:
                        self.logger.error("Unexpected response format from GetProfileList")
                        if callback:
                            callback([])
            except Exception as e:
                self.logger.error(f"Failed to get profiles: {str(e)}")
                if callback:
                    callback([])

        thread = threading.Thread(target=_get_profiles_thread)
        thread.daemon = True
        thread.start()
        return True

    def disconnect(self, callback: Optional[Callable[[bool], None]] = None) -> bool:
        """Disconnect from OBS with callback"""
        if not self._connected:
            if callback:
                callback(True)
            return True

        def _disconnect_thread():
            try:
                with self._connection_lock:
                    self.logger.info("Disconnecting from OBS...")
                    self._running = False
                    
                    # Stop keepalive thread first
                    if self._bg_thread and self._bg_thread.is_alive():
                        self._bg_thread.join(timeout=2)
                    self._bg_thread = None
                    
                    # Disconnect WebSocket
                    if self._ws:
                        try:
                            self._ws.disconnect()
                        except Exception as e:
                            self.logger.error(f"Error during WebSocket disconnect: {str(e)}")
                    
                    self._ws = None
                    self._connected = False
                    self._profiles = []
                    self._recording = False
                    self._notify_connection_state(False)  # Changed to use new notification
                    if callback:
                        callback(True)
                    return True

            except Exception as e:
                self.logger.error(f"Failed to disconnect: {str(e)}")
                if callback:
                    callback(False)
                return False

        thread = threading.Thread(target=_disconnect_thread)
        thread.daemon = True
        thread.start()
        return True

    def update_settings(self, host: str, port: int, password: str):
        """Update connection settings."""
        self.host = host
        self.port = port
        self.password = password
        
        # If already connected, reconnect with new settings
        if self.is_connected:
            self.disconnect()
            self.connect()

    @property
    def profiles(self) -> List[str]:
        """Get available OBS profiles"""
        return self._profiles

    @property
    def is_recording(self) -> bool:
        """Get current recording state"""
        return self._recording

    @property
    def is_connected(self) -> bool:
        """Get connection state"""
        return self._connected

    def add_connection_callback(self, callback: Callable[[bool], None]):
        """Add a callback to be notified of connection state changes."""
        if callback not in self._connection_callbacks:
            self._connection_callbacks.append(callback)

    def _notify_connection_callbacks(self, connected: bool):
        """Notify all registered callbacks of connection state changes."""
        for callback in self._connection_callbacks:
            try:
                callback(connected)
            except Exception as e:
                self.logger.error(f"Error in connection callback: {str(e)}")

    def get_scene_list(self, callback: Optional[Callable[[List[str]], None]] = None) -> bool:
        """
        Get available OBS scenes with callback.
        
        Args:
            callback: Optional callback function that receives the list of scene names
            
        Returns:
            bool: True if the request was initiated successfully, False otherwise
        """
        if not self._connected:
            self.logger.error("Not connected to OBS")
            if callback:
                callback([])
            return False
                
        def _get_scenes_thread():
            try:
                with self._operation_lock:
                    response = self._ws.call(requests.GetSceneList())
                    scenes = []
                    
                    # For OBS WebSocket v5
                    if hasattr(response, 'datain') and isinstance(response.datain, dict):
                        scene_list = response.datain.get('scenes', [])
                        if isinstance(scene_list, list):
                            scenes = [scene.get('sceneName', '') for scene in scene_list if scene.get('sceneName')]
                    
                    self.logger.debug(f"Retrieved scenes: {scenes}")
                    if callback:
                        callback(scenes)
                    
            except Exception as e:
                self.logger.error(f"Failed to get scenes: {str(e)}")
                if callback:
                    callback([])

        thread = threading.Thread(target=_get_scenes_thread)
        thread.daemon = True
        thread.start()
        return True

    def set_current_scene(self, scene_name: str, callback: Optional[Callable[[bool], None]] = None) -> bool:
        """
        Set current OBS scene with callback.
        
        Args:
            scene_name: Name of the scene to switch to
            callback: Optional callback function that receives success status
            
        Returns:
            bool: True if the request was initiated successfully, False otherwise
        """
        if not self._connected:
            self.logger.error("Not connected to OBS")
            if callback:
                callback(False)
            return False
                
        def _set_scene_thread():
            try:
                with self._operation_lock:
                    # For OBS WebSocket v5
                    response = self._ws.call(requests.SetCurrentProgramScene(**{
                        'sceneName': scene_name  # Changed from 'scene-name' to 'sceneName'
                    }))
                    
                    # In v5, no error response means success
                    success = True
                    
                    if success:
                        self.logger.info(f"Changed scene to: {scene_name}")
                        # Notify any registered callbacks about scene change
                        if 'SceneChanged' in self._event_handlers:
                            for handler in self._event_handlers['SceneChanged']:
                                try:
                                    handler(scene_name)
                                except Exception as e:
                                    self.logger.error(f"Error in scene change handler: {str(e)}")
                    else:
                        self.logger.error("Failed to change scene - unexpected response")
                        
                    if callback:
                        callback(success)
                    return success
                        
            except Exception as e:
                self.logger.error(f"Failed to set scene: {str(e)}")
                if callback:
                    callback(False)
                return False

        thread = threading.Thread(target=_set_scene_thread)
        thread.daemon = True
        thread.start()
        return True

    def get_current_scene(self, callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Get current OBS scene with callback.
        
        Args:
            callback: Optional callback function that receives the current scene name
            
        Returns:
            bool: True if the request was initiated successfully, False otherwise
        """
        if not self._connected:
            self.logger.error("Not connected to OBS")
            if callback:
                callback("")
            return False
                
        def _get_current_scene_thread():
            try:
                with self._operation_lock:
                    # For OBS WebSocket v5
                    response = self._ws.call(requests.GetCurrentProgramScene())
                    scene_name = ""
                    
                    # For OBS WebSocket v5
                    if hasattr(response, 'datain') and isinstance(response.datain, dict):
                        scene_name = response.datain.get('currentProgramSceneName', '')
                    
                    self.logger.debug(f"Current scene: {scene_name}")
                    if callback:
                        callback(scene_name)
                    
            except Exception as e:
                self.logger.error(f"Failed to get current scene: {str(e)}")
                if callback:
                    callback("")

        thread = threading.Thread(target=_get_current_scene_thread)
        thread.daemon = True
        thread.start()
        return True

    def add_connection_handler(self, handler: Callable[[bool], None]):
        """
        Add a handler to be called for both connection and disconnection events.
        
        Args:
            handler: Callback function that receives connection state (True=connected, False=disconnected)
        """
        if handler not in self._connection_handlers:
            self._connection_handlers.append(handler)
            # Immediately notify of current state if already connected
            if self._connected:
                try:
                    handler(True)
                except Exception as e:
                    self.logger.error(f"Error in connection handler: {str(e)}")

    def _notify_connection_state(self, connected: bool):
        """Notify all registered handlers of connection state change."""
        self.logger.debug(f"Notifying connection handlers of state: {'Connected' if connected else 'Disconnected'}")
        for handler in self._connection_handlers:
            try:
                handler(connected)
            except Exception as e:
                self.logger.error(f"Error in connection handler: {str(e)}")