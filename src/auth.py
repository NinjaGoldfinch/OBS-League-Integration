import asyncio
import base64
import json
import os
import psutil
import re
from typing import Optional, Tuple, Callable
from threading import Thread
from logger import Logger

import time

class LeagueClientAuth:
    """Handles League Client authentication and connection state."""
    
    def __init__(self):
        self.auth_token: Optional[str] = None
        self.client_port: Optional[int] = None
        self.process_names = ["LeagueClientUx.exe", "LeagueClient.exe"]  # Support both process names
        self._monitoring = False
        self._monitor_thread: Optional[Thread] = None
        self.logger = Logger()
        self._delay = 0.1
        self._connection_callbacks = []
        self._connected = False
        
    async def get_auth_data(self) -> Tuple[Optional[str], Optional[int]]:
        """Get authentication data from the League Client process."""
        for process in psutil.process_iter(['name', 'cmdline']):
            try:
                if process.info['name'] in self.process_names:
                    cmdline = process.info['cmdline']
                    if not cmdline:
                        continue
                        
                    # Debug logging
                    self.logger.debug(f"Found process: {process.info['name']}")
                    #self.logger.debug(f"Command line: {' '.join(cmdline)}")
                    
                    # More flexible regex patterns
                    cmd_str = ' '.join(cmdline)
                    auth_token = (
                        re.findall(r'--remoting-auth-token=([^"\s]+)', cmd_str) or
                        re.findall(r'--remoting-auth-token="([^"]+)"', cmd_str)
                    )
                    port = (
                        re.findall(r'--app-port=([^"\s]+)', cmd_str) or
                        re.findall(r'--app-port="([^"]+)"', cmd_str)
                    )
                    
                    if auth_token and port:
                        self.logger.debug(f"Found League Client process {process.info['name']} on port {port[0]}")
                        return (
                            base64.b64encode(f"riot:{auth_token[0]}".encode()).decode(),
                            int(port[0])
                        )
                    else:
                        self.logger.debug("Auth token or port not found in command line")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.logger.error(f"Error accessing process: {str(e)}")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error while checking process: {str(e)}")
                continue
                
        self.logger.warning("League Client process not found")
        return None, None

    async def update_auth(self):
        """Update authentication data only if there are changes."""
        self.logger.debug("Checking authentication data...")
        new_auth_token, new_client_port = await self.get_auth_data()
        
        # Check if values have changed
        auth_changed = new_auth_token != self.auth_token
        port_changed = new_client_port != self.client_port
        
        if auth_changed or port_changed:
            self.logger.info("Authentication data changed, updating values")
            self.auth_token = new_auth_token
            self.client_port = new_client_port
            
            # Notify connection state change
            if new_auth_token and new_client_port:
                self.connect()
            else:
                self.disconnect()
        else:
            self.logger.debug("No changes in authentication data")

    def start_monitoring(self):
        """Start monitoring for League Client in a separate thread."""
        if not self._monitoring:
            self.logger.info("Starting League Client monitor thread")
            self._monitoring = True
            self._monitor_thread = Thread(target=self._monitor_client, daemon=True)
            self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring the League Client and cleanup resources."""
        try:
            self.logger.info("Stopping League Client monitor thread")
            self._monitoring = False
            
            if self._monitor_thread and self._monitor_thread.is_alive():
                # Give the thread more time to exit gracefully
                for _ in range(int(3 / self._delay)):  # Try for 3 seconds (30 * 0.1)
                    if not self._monitor_thread.is_alive():
                        break
                    time.sleep(0.1)
                
                if self._monitor_thread.is_alive():
                    self.logger.warning("Monitor thread didn't stop gracefully, forcing stop")
                    # Add proper thread cleanup here if needed
                
        except Exception as e:
            self.logger.error(f"Error during monitor shutdown: {str(e)}")
        finally:
            self.auth_token = None
            self.client_port = None
            self.logger.info("League Client monitor stopped")

    def _monitor_client(self):
        """Monitor the League Client in a separate thread."""
        self.logger.debug("Monitor thread started")
        loop = None
        try:
            while self._monitoring:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.update_auth())
                
                # Use smaller sleep intervals to check monitoring flag more frequently
                if not self.auth_token or not self.client_port:
                    # Sleep for 5 seconds in 0.1s intervals
                    for _ in range(int(5 / self._delay)):  # Try for 5 seconds (5 / 0.1)
                        if not self._monitoring:
                            break
                        time.sleep(0.1)
                else:
                    # Sleep for 30 seconds in 0.1s intervals
                    for _ in range(int(30 / self._delay)):  # Try for 30 seconds (30 / 0.1)
                        if not self._monitoring:
                            break
                        time.sleep(0.1)
                        
                if not self._monitoring:
                    self.logger.debug("Monitoring stopped, exiting monitor loop")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error in monitor thread: {str(e)}")
        finally:
            if loop:
                loop.close()
            self.logger.debug("Monitor thread stopping")

    @property
    def is_client_running(self) -> bool:
        """Check if the League Client is running."""
        return bool(self.auth_token and self.client_port)

    def get_connection_headers(self) -> dict:
        """Get the headers needed for LCU API connections."""
        if not self.auth_token:
            self.logger.warning("No auth token available for headers")
            return {}
        self.logger.debug("Generated connection headers")
        return {
            'Authorization': f'Basic {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
    def __del__(self):
        """Destructor to ensure cleanup on object deletion."""
        if self._monitoring:
            self.stop_monitoring()
            
    def add_connection_callback(self, callback: Callable[[bool], None]):
        """Add a callback to be notified of connection state changes."""
        if callback not in self._connection_callbacks:
            self._connection_callbacks.append(callback)
            # Notify of current state immediately
            callback(self._connected)
            
    def remove_connection_callback(self, callback: Callable[[bool], None]):
        """Remove a previously registered connection callback."""
        if callback in self._connection_callbacks:
            self._connection_callbacks.remove(callback)
            
    def _notify_connection_callbacks(self, connected: bool):
        """Notify all registered callbacks of connection state changes."""
        self._connected = connected
        for callback in self._connection_callbacks:
            try:
                callback(connected)
            except Exception as e:
                self.logger.error(f"Error in connection callback: {str(e)}")
                
    def connect(self):
        """Connect to League Client."""
        successful_connection = self.auth_token is not None and self.client_port is not None
        if successful_connection:
            self._notify_connection_callbacks(True)
        
    def disconnect(self):
        """Disconnect from League Client."""
        # ...existing disconnect code...
        self._notify_connection_callbacks(False)
        
    @property
    def is_connected(self) -> bool:
        """Get current connection state."""
        return self._connected