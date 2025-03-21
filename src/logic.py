from typing import Optional, Dict, Any
from enum import Enum, auto
from logger import Logger
from api import LCUApi
from obs_client import OBSClient
from auth import LeagueClientAuth

class GamePhase(Enum):
    NONE = auto()
    LOBBY = auto()
    MATCHMAKING = auto()
    CHAMPION_SELECT = auto()
    GAME_START = auto()
    IN_GAME = auto()
    POST_GAME = auto()

class GameTracker:
    """
    Tracks League of Legends game state and manages OBS recording.
    
    Attributes:
        logger (Logger): Logger instance
        obs (OBSClient): OBS WebSocket client
        api (LCUApi): League Client API interface
        current_phase (GamePhase): Current game phase
    """
    
    def __init__(self, auth: LeagueClientAuth, api: LCUApi, obs: OBSClient):
        """
        Initialize GameTracker.
        
        Args:
            auth (LeagueClientAuth): Authentication handler for League Client
            api (LCUApi): League Client API interface
            obs (OBSClient): OBS WebSocket client
            gui (Optional): GUI instance for updates
        """
        self.logger = Logger()
        self.obs = obs
        self.api = api
        self.auth = auth
        self.current_phase = GamePhase.NONE
        self.recording_started = False
        self.client_connected = False
        self._game_update_callback = None
        
        # Register event handlers
        self.api.subscribe("lol-gameflow_v1_session", self._handle_gameflow_update)
        self.api.subscribe("lol-champ-select_v1_session", self._handle_champselect_update)
            
    def register_game_update_callback(self, callback):
        """Register callback for game state updates."""
        self._game_update_callback = callback
        self.logger.info("Game update callback registered")

    def start(self):
        """Start tracking game state"""
        self.logger.info("Starting game tracker...")
        
        # Check initial game state
        try:
            gameflow = self.api.get_current_gameflow()
            if gameflow:
                self._gameflow_update({'data': gameflow})
                
            # Don't auto-start recording for in-progress games
            if self.current_phase == GamePhase.IN_GAME:
                self.logger.warning("Game in progress detected - not starting recording")
                
        except Exception as e:
            self.logger.error(f"Error checking initial game state: {str(e)}")
        
        # Set initial profile in OBS if connected
        if self.obs.is_connected:
            self._set_obs_profile()
        
        self.obs.register_event_handler('RecordStateChanged', self._handle_recording_state)

    def stop(self):
        """Stop tracking and clean up"""
        self.logger.info("Stopping game tracker...")
        if self.recording_started:
            self._stop_recording()

    def _set_obs_profile(self):
        """Set OBS profile for League of Legends"""
        profile_name = "League of Legends"  # Could be configurable
        
        def on_profile_set(success: bool):
            if success:
                self.logger.info(f"Set OBS profile to: {profile_name}")
            else:
                self.logger.error(f"Failed to set OBS profile to: {profile_name}")
        
        self.obs.set_profile(profile_name, callback=on_profile_set)

    def _handle_gameflow_update(self, data: Dict[str, Any]):
        """Handle game flow state updates from LCU"""
        try:
            game_data = data.get('data', {})
            new_phase = game_data.get('phase', 'None')
            queue_info = game_data.get('gameData', {}).get('queue', {}).get('description', 'Unknown Queue')
            
            phase_mapping = {
                'Home Screen': GamePhase.NONE,
                'Lobby': GamePhase.LOBBY,
                'Matchmaking': GamePhase.MATCHMAKING,
                'ChampSelect': GamePhase.CHAMPION_SELECT,
                'GameStart': GamePhase.GAME_START,
                'InProgress': GamePhase.IN_GAME,
                'WaitingForStats': GamePhase.POST_GAME,
                'PreEndOfGame': GamePhase.POST_GAME,
                'EndOfGame': GamePhase.POST_GAME
            }
            
            new_game_phase = phase_mapping.get(new_phase, GamePhase.NONE)
            
            if new_game_phase != self.current_phase:
                self.logger.info(f"Game phase changed: {new_phase} ({queue_info})")
                # Use callback instead of direct GUI access
                if self._game_update_callback:
                    try:
                        self._game_update_callback('gameflow', {
                            'phase': new_phase,
                            'queue': queue_info
                        })
                    except Exception as e:
                        self.logger.error(f"Error in game update callback: {e}")
                        
                self._handle_phase_change(new_game_phase)
                self.current_phase = new_game_phase
                
        except Exception as e:
            self.logger.error(f"Error handling gameflow update: {str(e)}")

    def _handle_champselect_update(self, data: Dict[str, Any]):
        """Handle champion select updates"""
        try:
            # Check for dodge
            if not data.get('data'):  # Session ended
                if self.current_phase == GamePhase.CHAMPION_SELECT:
                    self.logger.info("Champion select ended - possible dodge")
                    self._handle_dodge()
                    
        except Exception as e:
            self.logger.error(f"Error handling champselect update: {str(e)}")

    def _handle_phase_change(self, new_phase: GamePhase):
        """Handle game phase transitions"""
        try:
            if new_phase == GamePhase.CHAMPION_SELECT:
                self._start_recording()
                
            elif new_phase == GamePhase.IN_GAME:
                if not self.recording_started:
                    self._start_recording()
                    
            elif new_phase in [GamePhase.NONE, GamePhase.LOBBY, GamePhase.POST_GAME]:
                if self.recording_started:
                    self._stop_recording()
                    
        except Exception as e:
            self.logger.error(f"Error handling phase change: {str(e)}")

    def _handle_dodge(self):
        """Handle game dodge detection"""
        self.logger.info("Game was dodged - stopping recording")
        self._stop_recording()
        self.current_phase = GamePhase.NONE

    def _handle_recording_state(self, is_recording: bool):
        """Handle recording state changes from OBS"""
        self.recording_started = is_recording
        self.logger.info(f"Recording {'started' if is_recording else 'stopped'}")

    def _start_recording(self):
        """Start OBS recording"""
        if not self.recording_started and self.obs.is_connected:
            def on_record_start(success: bool):
                if success:
                    self.logger.info("Started recording")
                else:
                    self.logger.error("Failed to start recording")
            
            self.obs.start_recording(callback=on_record_start)

    def _stop_recording(self):
        """Stop OBS recording"""
        if self.recording_started and self.obs.is_connected:
            def on_record_stop(success: bool):
                if success:
                    self.logger.info("Stopped recording")
                else:
                    self.logger.error("Failed to stop recording")
            
            self.obs.stop_recording(callback=on_record_stop)