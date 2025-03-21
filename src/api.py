import json
import ssl
import websockets
import asyncio
import threading
from typing import Dict, Callable, Optional, List
from logger import Logger
from auth import LeagueClientAuth
import requests
import urllib3

# Disable SSL warnings for local connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LCUApi:
    """
    League Client Update (LCU) API client that handles WebSocket connections and events.
    
    This class provides functionality to connect to the League Client's WebSocket interface,
    subscribe to events, and handle incoming messages through callbacks.
    
    Attributes:
        auth (LeagueClientAuth): Authentication handler for the League Client
        logger (Logger): Logger instance for debug and error messages
    """

    def __init__(self, auth: LeagueClientAuth):
        """
        Initialize the LCU API client.

        Args:
            auth (LeagueClientAuth): Authentication handler for the League Client
        """
        self.auth = auth
        self.logger = Logger()
        self._ws_thread: Optional[threading.Thread] = None
        self._running = False
        self._event_handlers: Dict[str, List[Callable]] = {}  # Changed to support multiple callbacks
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._subscribed = False
        self._connection_callback: Optional[Callable] = None
        self.is_connected = False  # Add connection state tracking

    def set_connection_callback(self, callback: Callable):
        """
        Set a callback to be called when the WebSocket connection is established.

        Args:
            callback (Callable): Function to be called on connection
        """
        self._connection_callback = callback
        self.logger.debug("Connection callback set")

    # Lifecycle Management
    def start(self):
        """
        Start the WebSocket client in a separate thread.
        
        If the client is already running, a warning will be logged and the method
        will return without taking any action.
        """
        if self._running:
            self.logger.warning("WebSocket client is already running")
            return

        self._running = True
        self._ws_thread = threading.Thread(target=self._run_websocket_client)
        self._ws_thread.daemon = True
        self._ws_thread.start()
        self.logger.info("WebSocket client thread started")

    def stop(self):
        """
        Stop the WebSocket client and clean up resources.
        
        This method will:
        1. Set the running flag to False
        2. Wait for the WebSocket thread to finish (with a 5-second timeout)
        3. Stop the event loop if it exists
        """
        self.logger.info("Stopping WebSocket client...")
        self._running = False
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=5)
        if self._loop:
            self._loop.stop()
        self.logger.info("WebSocket client stopped")

    # Event Subscription
    def subscribe(self, event_path: str, callback: Callable):
        """
        Subscribe to an LCU event with a callback function.
        
        Args:
            event_path (str): The path of the event to subscribe to
            callback (Callable): The function to call when the event occurs
        """
        self._store_subscription(event_path, callback)
        self.logger.debug(f"Added callback for event: {event_path}")
        
        # If we're already connected but not subscribed, try to subscribe
        if self.is_connected and not self._subscribed and self._ws:
            asyncio.run_coroutine_threadsafe(
                self._subscribe_to_events(), 
                self._loop
            )

    def unsubscribe(self, event_path: str, callback: Callable = None):
        """
        Unsubscribe from an LCU event.
        
        Args:
            event_path (str): The path of the event to unsubscribe from
            callback (Callable, optional): The specific callback to remove. If None,
                                        removes all callbacks for the event.
        """
        if event_path in self._event_handlers:
            if callback is None:
                self._event_handlers[event_path].clear()
                self.logger.debug(f"Removed all callbacks for event: {event_path}")
            else:
                self._event_handlers[event_path].remove(callback)
                self.logger.debug(f"Removed specific callback for event: {event_path}")

    def _store_subscription(self, event_path: str, callback: Callable):
        """Helper method to store event subscriptions."""
        if event_path not in self._event_handlers:
            self._event_handlers[event_path] = []
        if callback not in self._event_handlers[event_path]:
            self._event_handlers[event_path].append(callback)

    # WebSocket Connection Handling
    async def _subscribe_to_events(self):
        """Subscribe to specific events based on registered event handlers."""
        if not self._subscribed and self._ws:
            try:
                # Get list of unique event paths
                event_paths = list(self._event_handlers.keys())
                if not event_paths:
                    self.logger.debug("No events to subscribe to")
                    return

                # Subscribe to each event individually
                for event_path in event_paths:
                    subscribe_msg = [5, "OnJsonApiEvent_" + event_path, {}]
                    await self._ws.send(json.dumps(subscribe_msg))
                    self.logger.debug(f"Subscribed to event: {event_path}")

                self._subscribed = True
                self.logger.info(f"Subscribed to {len(event_paths)} LCU events")

            except Exception as e:
                self.logger.error(f"Failed to subscribe to events: {str(e)}")
                self._subscribed = False
                raise

    async def _connect(self):
        """
        Establish WebSocket connection to LCU.
        """
        # Wait for client to be running
        while not self.auth.is_client_running:
            self.logger.debug("Waiting for League Client to start...")
            await asyncio.sleep(1)

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        uri = f"wss://127.0.0.1:{self.auth.client_port}"
        conn_headers = self.auth.get_connection_headers()
        headers = {
            "Authorization": conn_headers["Authorization"],
            "Accept": conn_headers["Accept"],
            "Content-Type": conn_headers["Content-Type"]
        }

        try:
            self._ws = await websockets.connect(
                uri,
                ssl=ssl_context,
                additional_headers=headers
            )
            self.logger.info("Connected to LCU WebSocket")
            
            # Update connection state first
            self.is_connected = True
            self._subscribed = False  # Reset subscription flag
            
            # Handle connection callback
            if self._connection_callback:
                try:
                    self._connection_callback(self.is_connected)
                except Exception as e:
                    self.logger.error(f"Error in connection callback: {str(e)}")

            # Subscribe to events after successful connection
            await self._subscribe_to_events()

        except Exception as e:
            self.logger.error(f"Failed to connect to LCU WebSocket: {str(e)}")
            self.is_connected = False
            self._subscribed = False
            # Call callback on connection failure
            if self._connection_callback:
                try:
                    self._connection_callback(False)
                except Exception as e:
                    self.logger.error(f"Error in connection callback during failure: {str(e)}")
            raise

    async def _handle_messages(self):
        """
        Handle incoming WebSocket messages.
        
        This method:
        1. Receives messages from the WebSocket connection
        2. Parses JSON data
        3. Dispatches events to registered callbacks
        
        The method runs in a loop until the connection is closed or an error occurs.
        """
        try:
            while self._running and self._ws:
                message = await self._ws.recv()
                try:
                    data = json.loads(message)
                    if len(data) == 3 and data[0] == 8:  # Event message format
                        event_path = data[1].replace("OnJsonApiEvent_", "")
                        event_data = data[2]
                        event_uri = event_data.get("uri", "")
                        
                        #self.logger.debug(f"Received event: {event_path}")
                        
                        # Check if any callbacks are registered for this event
                        for registered_path, callbacks in self._event_handlers.items():
                            if event_path.startswith(registered_path):
                                for callback in callbacks:
                                    try:
                                        self.logger.debug(f"Calling event handler for {event_path}")
                                        callback(event_data)
                                    except Exception as e:
                                        self.logger.error(f"Error in event handler for {event_path}: {str(e)}")
                                        
                except json.JSONDecodeError:
                    self.logger.warning(f"Received invalid JSON message: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
        except Exception as e:
            self.logger.error(f"Error handling WebSocket messages: {str(e)}")

    def _run_websocket_client(self):
        """
        Main WebSocket client loop running in separate thread.
        
        This method:
        1. Creates and sets up the event loop
        2. Handles connection and reconnection logic
        3. Manages the WebSocket lifecycle
        
        If connection fails, it will attempt to reconnect every 5 seconds.
        """
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        while self._running:
            try:
                self._loop.run_until_complete(self._connect())
                self._loop.run_until_complete(self._handle_messages())
            except Exception as e:
                self.logger.error(f"WebSocket error: {str(e)}")
                if self._running:
                    self.logger.info("Attempting to reconnect in 5 seconds...")
                    asyncio.run(asyncio.sleep(5))
            finally:
                if self._ws:
                    self._loop.run_until_complete(self._ws.close())

        self.logger.debug("WebSocket client thread ending")

    def get_request(self, endpoint: str) -> Dict:
        """
        Make a GET request to the LCU API.
        
        Args:
            endpoint (str): API endpoint path (e.g. "lol-gameflow/v1/session")
            
        Returns:
            Dict: Response data as dictionary
            
        Raises:
            requests.RequestException: If request fails
        """
        if not self.auth.is_client_running:
            self.logger.error("League Client not running")
            return {}
            
        url = f"https://127.0.0.1:{self.auth.client_port}/{endpoint}"
        headers = self.auth.get_connection_headers()
        
        try:
            response = requests.get(
                url, 
                headers=headers,
                verify=False
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"GET request failed: {str(e)}")
            return {}

    def post_request(self, endpoint: str, data: Dict = None) -> Dict:
        """
        Make a POST request to the LCU API.
        
        Args:
            endpoint (str): API endpoint path
            data (Dict): JSON data to send
            
        Returns:
            Dict: Response data as dictionary
            
        Raises:
            requests.RequestException: If request fails
        """
        if not self.auth.is_client_running:
            self.logger.error("League Client not running") 
            return {}

        url = f"https://127.0.0.1:{self.auth.client_port}/{endpoint}"
        headers = self.auth.get_connection_headers()
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=data,
                verify=False
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.RequestException as e:
            self.logger.error(f"POST request failed: {str(e)}")
            return {}

    def get_current_gameflow(self) -> Dict:
        """Get current game flow session state"""
        return self.get_request("lol-gameflow/v1/session")

    def get_champ_select(self) -> Dict:
        """Get current champion select session"""
        return self.get_request("lol-champ-select/v1/session")

    def get_current_summoner(self) -> Dict:
        """Get current summoner information"""
        return self.get_request("lol-summoner/v1/current-summoner")

    def get_game_data(self) -> Dict:
        """Get live game data if in game"""
        return self.get_request("liveclientdata/allgamedata")