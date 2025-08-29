"""
Components Package

Contains modular UI components and managers organized by functionality.
Each subpackage provides specialized components for different parts of the application,
following a clean separation of concerns and modular architecture.

Subpackages:
    core: Fundamental components and base classes
    download: Download management and progress tracking
    environment: Environment setup and configuration
    home: Home interface components and dashboard
    launcher: Application launcher components
    logging: Logging interface and log management
    main: Main window and navigation components
    module: Module management and workflow components
    monitoring: System and process monitoring components
    plugin: Plugin system and extension management
    proxy: Proxy configuration and management
    setting: Settings interface and configuration
    tools: Various utility tools and editors
    utils: Common utility components and helpers

Architecture:
    - Each component package is self-contained
    - Components communicate via signals and events
    - Shared functionality is provided by the common package
    - Resource access is managed through the resources package

Design Principles:
    - Modular: Each component can be developed and tested independently
    - Reusable: Components can be used across different interfaces
    - Extensible: New components can be added without affecting existing ones
    - Maintainable: Clear separation of concerns and responsibilities

Example:
    Using components in an interface:

    >>> from .home import ServerButton, HomeLayoutManager
    >>> from .monitoring import ProcessMonitorWidget
    >>>
    >>> # Create and configure components
    >>> server_button = ServerButton()
    >>> layout_manager = HomeLayoutManager()
    >>> monitor = ProcessMonitorWidget()
"""

# Import component managers and utilities
from .monitoring import DownloadManagerWidget, ProcessMonitorWidget

# Core component packages are imported via their __init__.py files
# Individual components can be imported as needed:
# from .home import ServerButton, HomeLayoutManager
# from .download import DownloadSearchManager, DownloadCardManager
# from .module import ModuleWorkflowManager, ModuleErrorHandler
# from .main import WindowManager, ThemeManager
# from .proxy import FiddlerManager, ProxyManager
# from .launcher import LauncherNavigationManager
# from .logging import LogPanel, LogViewer
# from .setting import SettingManager
# from .monitoring import DownloadManagerWidget, ProcessMonitorWidget

__all__: list[str] = ["DownloadManagerWidget", "ProcessMonitorWidget"]

# Component package information - organized by architectural layers
COMPONENT_PACKAGES = {
    # Core Infrastructure
    "infrastructure": ["core", "utils", "monitoring"],

    # User Interface Components
    "ui_components": ["main", "home", "launcher", "logging", "setting", "tools"],

    # Feature Modules
    "feature_modules": ["download", "environment", "module", "proxy", "plugin"],

    # User Experience
    "user_experience": ["onboarding"],
}

# Flat list for backward compatibility
COMPONENT_PACKAGES_LIST = [
    "core", "download", "environment", "home", "launcher",
    "logging", "main", "module", "monitoring", "onboarding",
    "plugin", "proxy", "setting", "tools", "utils"
]
