"""
GUI styling package.
Exports theme and style definitions.
"""

from .theme import Theme
from .colors import ColorScheme, DarkColors as DarkTheme, LightColors as LightTheme
from .widgets import WidgetStyles
from .frames import configure_frame_styles, configure_status_styles

__all__ = [
    'Theme',
    'ColorScheme',
    'DarkTheme',
    'LightTheme',
    'WidgetStyles',
    'configure_frame_styles',
    'configure_status_styles'
]