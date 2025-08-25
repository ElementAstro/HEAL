"""
Main Components Package
Contains all modular components for the main interface
"""

from .audio_manager import AudioManager
from .auth_manager import AuthenticationManager
from .font_manager import FontManager
from .navigation_manager import MainNavigationManager
from .theme_manager import ThemeManager
from .update_manager import UpdateManager
from .window_manager import WindowManager

__all__: list[str] = [
    "WindowManager",
    "MainNavigationManager",
    "AuthenticationManager",
    "ThemeManager",
    "AudioManager",
    "FontManager",
    "UpdateManager",
]
