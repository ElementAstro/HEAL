"""
Main Components Package
Contains all modular components for the main interface
"""

from .window_manager import WindowManager
from .navigation_manager import MainNavigationManager
from .auth_manager import AuthenticationManager
from .theme_manager import ThemeManager
from .audio_manager import AudioManager
from .font_manager import FontManager
from .update_manager import UpdateManager

__all__ = [
    'WindowManager',
    'MainNavigationManager', 
    'AuthenticationManager',
    'ThemeManager',
    'AudioManager',
    'FontManager',
    'UpdateManager'
]
