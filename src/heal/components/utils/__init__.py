"""
Utility Components Package

Contains utility functions and helper components that provide
common functionality across different parts of the application.
"""

from .check_installed import is_software_installed, get_software_path, get_software_version
from .dispatch import CommandDispatcher
from .scaffold import query_user, create_component_main

__all__: list[str] = ["is_software_installed", "get_software_path", "get_software_version", "CommandDispatcher", "query_user", "create_component_main"]
