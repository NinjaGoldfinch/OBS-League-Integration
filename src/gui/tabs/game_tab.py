"""
Game status and control tab.
"""

import tkinter as tk
from tkinter import ttk

from ..components import StatusLabel
from ..styles import ColorScheme, configure_frame_styles, configure_status_styles
from .base_tab import BaseTab

class GameTab(BaseTab):
    """Game monitoring and control interface."""
    
    title = "Game"
    
    def __init__(self, parent, colors, config=None, logger=None):
        self.game_phase_var = tk.StringVar(value="None")
        self.queue_type_var = tk.StringVar(value="Not in queue")
        self.champion_var = tk.StringVar(value="No champion selected")
        super().__init__(parent, colors, config, logger)
        
    def _setup_styles(self):
        """Configure tab-specific styles."""
        style = ttk.Style()
        configure_frame_styles(style, self.colors)
        configure_status_styles(style, self.colors)
        
    def _setup_gui(self):
        """Setup game tab interface."""
        self._setup_styles()
        
        # Game status frame
        status_frame = ttk.LabelFrame(
            self,
            text="Current Game Status",
            style="Main.TLabelframe"
        )
        status_frame.pack(fill='x', padx=5, pady=5)
        
        # Queue type
        queue_frame = ttk.Frame(status_frame, style="TFrame")
        queue_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(
            queue_frame,
            text="Queue Type:",
            style="Title.TLabel"
        ).pack(side='left', padx=5)
        
        StatusLabel(
            queue_frame,
            textvariable=self.queue_type_var,
            colors=self.colors
        ).pack(side='left', padx=5)
        
        # Game phase
        phase_frame = ttk.Frame(status_frame, style="TFrame")
        phase_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(
            phase_frame,
            text="Game Phase:",
            style="Title.TLabel"
        ).pack(side='left', padx=5)
        
        StatusLabel(
            phase_frame,
            textvariable=self.game_phase_var,
            colors=self.colors
        ).pack(side='left', padx=5)
        
    def update_theme(self, colors):
        """Update component theme."""
        self.colors = colors
        self._setup_styles()
        
        # Update all status labels
        for child in self.winfo_children():
            if isinstance(child, StatusLabel):
                child.update_theme(colors)
                
    def update_game_info(self, game_type: str, game_info: dict):
        """
        Update game-related information in the tab.
        
        Args:
            game_type: Type of game update (e.g., 'gameflow', 'champselect')
            game_info: Dictionary containing game state information
        """
        try:
            if self.logger:
                self.logger.debug(f"Received game update - type: {game_type}, info: {game_info}")
                
            # Validate input
            if not isinstance(game_info, dict):
                if self.logger:
                    self.logger.error(f"Invalid game_info type: {type(game_info)}")
                return
                
            if game_type == 'gameflow':
                # Update game phase
                phase = str(game_info.get('phase', 'None'))
                self.game_phase_var.set(phase)
                
                # Update queue type if available
                queue_info = game_info.get('gameData', {})
                if isinstance(queue_info, dict):
                    queue_data = queue_info.get('queue', {})
                    queue_type = queue_data.get('type', 'Not in queue')
                    self.queue_type_var.set(queue_type)
                    
            elif game_type == 'champselect':
                # Update champion selection
                champion = game_info.get('champion', 'No champion selected')
                self.champion_var.set(champion)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to update game tab info: {e}")