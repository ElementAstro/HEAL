"""
Models package for HEAL application.

Contains data models, configuration classes, and business logic components
that represent the core entities and operations of the application.
"""

from .check_update import UpdateThread, check_update, handle_update, get_latest_version

# Configuration and settings
from .config import Config, cfg

# UI Models and components
from .custom_messagebox import CustomMessageBox

# Process and download management
from .download_manager import DownloadManager
from .download_process import SubDownloadCMD, CommandRunner
from .drag import DraggableButton, DraggableButtonConfig, FlowLayout, DropArea, MainWindow
from .login_card import MessageBoxBase, MessageLogin
from .message_download import (
    MessageCompiler,
    MessageDialog,
    MessageNINA,
    MessagePHD2,
    MessagePython,
)
from .process_manager import ProcessManager

# Remote and update functionality
# from .remote import RemoteManager  # RemoteManager class not found in remote.py
from .setting_card import SettingCard
from .style_sheet import StyleSheet
from .system_tray import SystemTray

__all__: list[str] = [
    # Configuration
    "cfg",
    "Config",
    "SettingCard",
    # UI Models
    "CustomMessageBox",
    "DraggableButton",
    "DraggableButtonConfig",
    "FlowLayout",
    "DropArea",
    "MainWindow",
    "MessageBoxBase",
    "MessageLogin",
    "StyleSheet",
    "SystemTray",
    # Process and download management
    "DownloadManager",
    "SubDownloadCMD",
    "CommandRunner",
    "ProcessManager",
    "MessageDialog",
    "MessagePython",
    "MessageCompiler",
    "MessageNINA",
    "MessagePHD2",
    # Update functionality
    "UpdateThread",
    "check_update",
    "handle_update",
    "get_latest_version",
]
