"""
Utility Components Package

Contains utility functions organized by functional categories:
- System utilities (installation checks, platform operations)
- UI utilities (scaffolding, dispatch mechanisms)
- Data utilities (validation, transformation)
"""

# System utilities
from .system_utils import SystemUtilities
from .check_installed import is_software_installed, get_software_path, get_software_version

# UI utilities
from .ui_utils import UIUtilities, UIEventTracker
from .dispatch import CommandDispatcher
from .scaffold import query_user, create_component_main

# Data utilities
from .data_utils import DataUtilities

__all__: list[str] = [
    # System utilities
    "SystemUtilities",
    "is_software_installed",
    "get_software_path",
    "get_software_version",

    # UI utilities
    "UIUtilities",
    "UIEventTracker",
    "CommandDispatcher",
    "query_user",
    "create_component_main",

    # Data utilities
    "DataUtilities",
]
