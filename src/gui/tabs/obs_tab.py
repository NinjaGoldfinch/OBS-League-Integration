"""
OBS WebSocket connection and scene control tab.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable

from ..components import StatusLabel, ConnectionPanel
from .base_tab import BaseTab

class OBSTab(BaseTab):
    """OBS Studio integration interface."""
    
    title = "OBS"
    
    def __init__(self, parent, colors, obs=None, config=None, logger=None):
        self.obs = obs
        self.logger = logger
        self.connection_status = tk.StringVar(value="Disconnected")
        self.current_scene = tk.StringVar(value="No scene")
        self.scenes = []
        super().__init__(parent, colors, config)
        
        # Set up OBS client if provided
        if self.obs:
            self.set_obs_client(self.obs)
    
    def set_obs_client(self, obs):
        """Set OBS client and update UI accordingly."""
        self.obs = obs
        if self.obs:
            # Register single callback for connection state
            self.obs.add_connection_handler(self._handle_obs_connection)
            
            # Update UI based on current connection state
            self._handle_obs_connection(self.obs.is_connected)

    def _handle_obs_connection(self, connected: bool):
        """Handle OBS connection state changes."""
        if connected:
            self.connection_status.set("Connected")
            self._refresh_scenes()
            self.scene_list.configure(state='normal')
            # Get and set current scene
            self.obs.get_current_scene(callback=self._update_current_scene)
        else:
            self.connection_status.set("Disconnected")
            self.scenes.clear()
            self.scene_list.delete(0, tk.END)
            self.current_scene.set("No scene")
            self.scene_list.configure(state='disabled')

        if self.logger:
            self.logger.info(f"OBS {'connected' if connected else 'disconnected'}")

    def _setup_gui(self):
        """Setup OBS tab interface."""
        # Connection panel
        self.conn_panel = ConnectionPanel(
            self,
            self.colors,
            self.connection_status,
            connect_callback=self._connect_obs,
            disconnect_callback=self._disconnect_obs
        )
        self.conn_panel.pack(fill='x', padx=5, pady=5)
        
        # Scene control frame
        self.scene_frame = ttk.LabelFrame(
            self,
            text="Scene Control",
            style="Main.TLabelframe"
        )
        self.scene_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self._setup_scene_controls()
        
    def _setup_scene_controls(self):
        """Setup scene selection and control widgets."""
        # Current scene display
        current_frame = ttk.Frame(self.scene_frame)
        current_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(
            current_frame,
            text="Current Scene:",
            style="Title.TLabel"
        ).pack(side='left', padx=5)
        
        StatusLabel(
            current_frame,
            textvariable=self.current_scene,
            colors=self.colors
        ).pack(side='left', padx=5)
        
        # Scene list
        list_frame = ttk.Frame(self.scene_frame)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.scene_list = tk.Listbox(
            list_frame,
            bg=self.colors.secondary_bg,
            fg=self.colors.foreground,
            selectmode='single',
            relief='flat'
        )
        self.scene_list.pack(side='left', fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient='vertical',
            command=self.scene_list.yview
        )
        scrollbar.pack(side='right', fill='y')
        self.scene_list.configure(yscrollcommand=scrollbar.set)
        
        # Control buttons
        button_frame = ttk.Frame(self.scene_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Switch Scene",
            command=self._switch_scene,
            style="Accent.TButton"
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="Refresh List",
            command=self._refresh_scenes,
            style="TButton"
        ).pack(side='left', padx=5)
    
    def _connect_obs(self):
        """Attempt to connect to OBS."""
        try:
            if not self.obs:
                messagebox.showerror("Error", "OBS client not initialized")
                return
                
            self.obs.connect()
            
            # Check connection status after a short delay
            self.after(500, self._check_connection_status)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"OBS connection failed: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect to OBS: {e}")
            self.connection_status.set("Connection Failed")

    def _check_connection_status(self):
        """Check if OBS connection was successful."""
        if self.obs and self.obs.is_connected:
            self.connection_status.set("Connected")
            self._refresh_scenes()
            # Get and set current scene
            self.obs.get_current_scene(callback=self._update_current_scene)
        else:
            # If not connected, try checking again after a delay
            if self.connection_status.get() != "Connection Failed":
                self.after(500, self._check_connection_status)
    
    def _disconnect_obs(self):
        """Disconnect from OBS WebSocket server."""
        try:
            self.obs.disconnect()
            # Cleanup will be handled by _handle_obs_connection
        except Exception as e:
            if self.logger:
                self.logger.error(f"OBS disconnect failed: {e}")
    
    def _refresh_scenes(self):
        """Refresh scene list from OBS."""
        try:
            if not self.obs or not self.obs.is_connected:
                return
                
            def on_scenes_received(scenes):
                self.scenes = scenes
                self.scene_list.delete(0, tk.END)
                self.scene_list.configure(state='normal')
                for scene in self.scenes:
                    self.scene_list.insert(tk.END, scene)
                # Update current scene selection after refreshing list
                self.obs.get_current_scene(callback=self._update_current_scene)
                
            self.obs.get_scene_list(callback=on_scenes_received)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get scene list: {e}")
            messagebox.showerror("Error", f"Failed to get scene list: {e}")
    
    def _switch_scene(self):
        """Switch to selected scene."""
        if not self.obs or not self.obs.is_connected:  # Changed from .connected to .is_connected
            return
            
        selection = self.scene_list.curselection()
        if not selection:
            return
            
        scene_name = self.scenes[selection[0]]
        try:
            self.obs.set_current_scene(scene_name)
            self.current_scene.set(scene_name)
        except Exception as e:
            if self.logger:  # Add check for logger existence
                self.logger.error(f"Failed to switch scene: {e}")
            messagebox.showerror("Error", f"Failed to switch scene: {e}")  # Add user feedback

    def _update_current_scene(self, scene_name):
        """Update current scene display."""
        self.current_scene.set(scene_name)
        # Select the current scene in the list
        for i, scene in enumerate(self.scenes):
            if scene == scene_name:
                self.scene_list.selection_clear(0, tk.END)
                self.scene_list.selection_set(i)
                self.scene_list.see(i)
                break