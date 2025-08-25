"""
Interfaces Package

Contains all user interface modules for different sections of the application.
Each interface module provides a complete UI for a specific functionality area.
"""

from .download_interface import Download
from .environment_interface import Environment
from .home_interface import Home
from .launcher_interface import Launcher
from .log_interface import LogManagement
from .main_interface import Main
from .module_interface import Module
from .proxy_interface import Proxy
from .setting_interface import Setting
from .tool_interface import Tools

__all__: list[str] = [
    "Main",
    "Home",
    "Download",
    "Environment",
    "Launcher",
    "LogManagement",
    "Module",
    "Proxy",
    "Setting",
    "Tools",
]
