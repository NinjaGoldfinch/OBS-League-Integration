"""
Color definitions for application themes.
"""

from dataclasses import dataclass

@dataclass
class ColorScheme:
    """Base color scheme definition."""
    # Primary colors
    primary: str
    accent: str
    accent_light: str
    accent_dark: str
    
    # Backgrounds
    background: str
    secondary_bg: str
    tertiary_bg: str
    
    # Text colors
    foreground: str
    secondary_fg: str
    disabled_fg: str
    
    # Log level colors
    log_debug: str
    log_info: str
    log_warning: str
    log_error: str
    
    # UI elements
    border: str
    focus_border: str

class DarkColors(ColorScheme):
    """Dark theme color palette with purple accents."""
    
    def __init__(self):
        super().__init__(
            # Primary colors
            primary="#9147FF",      # Main purple
            accent="#B066FF",       # Light purple
            accent_light="#C990FF", # Lighter purple for hover
            accent_dark="#6441A5",  # Dark purple for pressed
            
            # Backgrounds
            background="#18181B",   # Dark gray
            secondary_bg="#242428", # Slightly lighter
            tertiary_bg="#2D2D32",  # Even lighter
            
            # Text colors
            foreground="#FFFFFF",   # White
            secondary_fg="#E0E0E0", # Light gray
            disabled_fg="#666666",  # Dark gray
            
            # Log level colors - Purple theme with better contrast
            log_debug="#9147FF",    # Main purple
            log_info="#B066FF",     # Light purple
            log_warning="#FF9147",  # Orange
            log_error="#FF4747",    # Red
            
            # UI elements
            border="#333333",       # Dark border
            focus_border="#B066FF"  # Light purple focus
        )

class LightColors(ColorScheme):
    """Light theme color palette."""
    
    def __init__(self):
        super().__init__(
            # Primary colors
            primary="#9147FF",      # Keep brand color
            accent="#772CE8",       # Main accent
            accent_light="#B088F9", # Hover state
            accent_dark="#5C16C5",  # Pressed state
            
            # Backgrounds
            background="#FFFFFF",    # White
            secondary_bg="#F7F7F8",  # Light gray
            tertiary_bg="#EFEFF1",   # Darker gray
            
            # Text colors
            foreground="#0E0E10",    # Almost black
            secondary_fg="#53535F",   # Dark gray
            disabled_fg="#ADADB8",    # Light gray
            
            # Log level colors
            log_debug="#0098C7",     # Darker cyan
            log_info="#008C46",      # Darker green
            log_warning="#B59B00",    # Darker yellow
            log_error="#D12F2F",     # Darker red
            
            # UI elements
            border="#DEDEE3",        # Light border
            focus_border="#772CE8"    # Purple focus
        )