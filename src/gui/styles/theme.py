"""
Theme enumeration and configuration.
"""

from dataclasses import dataclass
from enum import Enum

class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"

@dataclass
class ColorScheme:
    """Base color scheme definition"""
    # Primary colors
    primary: str
    accent: str  
    accent_light: str
    accent_dark: str
    
    # Backgrounds
    background: str
    secondary_bg: str
    tertiary_bg: str
    
    # Text
    foreground: str
    secondary_fg: str
    disabled_fg: str
    
    # Logging
    log_debug: str
    log_info: str
    log_warning: str
    log_error: str
    
    # Borders
    border: str
    focus_border: str

@dataclass
class DarkTheme(ColorScheme):
    """Dark theme color scheme"""
    def __init__(self):
        super().__init__(
            # Primary colors
            primary="#9103a9",      # Main purple
            accent="#b366b3",       # Lighter purple
            accent_light="#cc99cc", # Even lighter purple for hover
            accent_dark="#8c4d8c",  # Darker purple for pressed
            
            # Backgrounds
            background="#1e1e1e",   # Main background
            secondary_bg="#2d2d2d", # Secondary background
            tertiary_bg="#3d3d3d",  # Tertiary background
            
            # Text
            foreground="#ffffff",    # Main text
            secondary_fg="#cccccc",  # Secondary text
            disabled_fg="#666666",   # Disabled text
            
            # Logging
            log_debug="#569cd6",    # Blue
            log_info="#6a9955",     # Green
            log_warning="#d7ba7d",  # Yellow
            log_error="#f44747",    # Red
            
            # Borders
            border="#404040",       # Normal borders
            focus_border="#007acc"  # Focus borders
        )

@dataclass 
class LightTheme(ColorScheme):
    """Light theme color scheme"""
    def __init__(self):
        super().__init__(
            # Primary colors
            primary="#9103a9",      # Main purple
            accent="#b366b3",       # Lighter purple
            accent_light="#d4b3d4", # Even lighter purple for hover
            accent_dark="#995d99",  # Darker purple for pressed
            
            # Backgrounds
            background="#ffffff",    # Main background
            secondary_bg="#f0f0f0", # Secondary background
            tertiary_bg="#e5e5e5",  # Tertiary background
            
            # Text
            foreground="#000000",   # Main text
            secondary_fg="#333333", # Secondary text
            disabled_fg="#999999",  # Disabled text
            
            # Logging
            log_debug="#0066cc",    # Darker Blue
            log_info="#008000",     # Darker Green
            log_warning="#b3a600",  # Darker Yellow
            log_error="#cc0000",    # Darker Red
            
            # Borders
            border="#cccccc",       # Normal borders
            focus_border="#007acc"  # Focus borders
        )

class ThemeManager:
    """Theme management utility"""
    _dark_theme = DarkTheme()
    _light_theme = LightTheme()
    
    @classmethod
    def get_colors(cls, theme: Theme) -> ColorScheme:
        """Get color scheme for specified theme"""
        return cls._dark_theme if theme == Theme.DARK else cls._light_theme