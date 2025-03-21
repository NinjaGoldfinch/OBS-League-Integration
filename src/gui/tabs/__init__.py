"""
GUI tabs package.
Exports tab components for the main window.
"""

from .game_tab import GameTab
from .obs_tab import OBSTab
from .config_tab import ConfigTab

__all__ = ['GameTab', 'OBSTab', 'ConfigTab']