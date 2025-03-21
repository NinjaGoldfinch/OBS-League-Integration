from enum import Enum
from dataclasses import dataclass

class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"

@dataclass
class DarkThemeColors:
    # Primary colors
    primary: str = "#9103a9"  # Main purple
    accent: str = "#b366b3"   # Lighter purple
    accent_light: str = "#cc99cc"  # Even lighter purple for hover states
    accent_dark: str = "#8c4d8c"   # Darker purple for pressed states
    
    # Background colors
    background: str = "#1e1e1e"       # Main background
    secondary_bg: str = "#2d2d2d"     # Secondary background
    tertiary_bg: str = "#363636"      # Tertiary background
    
    # Text colors
    foreground: str = "#ffffff"        # Main text
    secondary_fg: str = "#cccccc"      # Secondary text
    disabled_fg: str = "#666666"       # Disabled text
    
    # Log colors
    log_debug: str = "#4a9eff"        # Blue
    log_info: str = "#4aff4a"         # Green
    log_warning: str = "#ffff4a"       # Yellow
    log_error: str = "#ff4a4a"         # Red
    
    # Border colors
    border: str = "#404040"           # Normal borders
    focus_border: str = "#9103a9"     # Focused borders

@dataclass
class LightThemeColors:
    # Primary colors
    primary: str = "#9103a9"          # Main purple
    accent: str = "#b366b3"           # Lighter purple
    accent_light: str = "#d4b3d4"     # Even lighter purple for hover states
    accent_dark: str = "#995d99"      # Darker purple for pressed states
    
    # Background colors
    background: str = "#ffffff"        # Main background
    secondary_bg: str = "#f0f0f0"     # Secondary background
    tertiary_bg: str = "#e5e5e5"      # Tertiary background
    
    # Text colors
    foreground: str = "#000000"       # Main text
    secondary_fg: str = "#333333"     # Secondary text
    disabled_fg: str = "#999999"      # Disabled text
    
    # Log colors
    log_debug: str = "#0066cc"        # Darker Blue for better contrast
    log_info: str = "#008000"         # Darker Green for better contrast
    log_warning: str = "#b3a600"      # Darker Yellow for better contrast
    log_error: str = "#cc0000"        # Darker Red for better contrast
    
    # Border colors
    border: str = "#cccccc"           # Normal borders
    focus_border: str = "#9103a9"     # Focused borders

class ThemeManager:
    _dark_theme = DarkThemeColors()
    _light_theme = LightThemeColors()
    
    @classmethod
    def get_colors(cls, theme: Theme) -> DarkThemeColors | LightThemeColors:
        return cls._dark_theme if theme == Theme.DARK else cls._light_theme