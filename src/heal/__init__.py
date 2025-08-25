"""
HEAL - Hello ElementAstro Launcher

A comprehensive launcher and management system for astronomical software.
This package provides a unified interface for managing various astronomy tools,
downloads, configurations, and workflows.

Features:
    - Modular component architecture for extensibility
    - Comprehensive resource management system
    - Multi-language support with i18n
    - Advanced logging and monitoring capabilities
    - Configuration management and validation
    - Plugin system for custom extensions

Package Structure:
    - common: Shared utilities and infrastructure
    - components: Modular UI components organized by functionality
    - interfaces: Main application interface modules
    - models: Data models and business logic
    - resources: Static assets, translations, and configuration files

Example:
    Basic usage of the HEAL application:

    >>> from heal import Main, setup_logging
    >>> setup_logging()
    >>> app = Main()
    >>> app.show()

Note:
    This package follows the src-layout pattern and PEP 518/621 standards
    for modern Python packaging and distribution.
"""

__version__ = "1.0.0"
__author__ = "Max Qian"
__email__ = "astro_air@126.com"
__license__ = "MIT"
__copyright__ = "Copyright 2025, ElementAstro Team"

from .common.application import SingletonApplication
from .common.config_validator import validate_all_configs
from .common.logging_config import get_logger, setup_logging

# Core application components
from .interfaces.main_interface import Main

__all__: list[str] = [
    "Main",
    "SingletonApplication",
    "setup_logging",
    "get_logger",
    "validate_all_configs",
]
