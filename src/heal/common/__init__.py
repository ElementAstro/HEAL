"""
Common Utilities Package

This package contains core functionality that is used across different
parts of the HEAL application. It provides the foundational infrastructure
that other components depend on.

Modules:
    application: Singleton application management and lifecycle
    logging_config: Unified logging system with performance monitoring
    config_validator: Configuration file validation and management
    exception_handler: Centralized exception handling and reporting
    resource_manager: Resource lifecycle management and cleanup
    i18n: Internationalization and localization support
    cache_manager: Intelligent caching system for performance
    performance_analyzer: Application performance monitoring
    memory_optimizer: Memory optimization and object pooling
    workflow_optimizer: Complex workflow optimization
    optimization_validator: Performance validation and testing
    signal_bus: Global signal communication system
    ui_utils: Common UI utilities and helpers

Key Features:
    - Centralized logging with multiple output formats
    - Configuration validation with auto-repair capabilities
    - Resource management with automatic cleanup
    - Multi-language support with dynamic switching
    - Performance monitoring and optimization
    - Exception handling with user-friendly error reporting

Example:
    Setting up the common infrastructure:

    >>> from src.heal.common import setup_logging, get_logger
    >>> setup_logging()
    >>> logger = get_logger('my_module')
    >>> logger.info("Application started")
"""

# Core application infrastructure
from .application import SingletonApplication
from .async_io_utils import AsyncFileManager, AsyncNetworkManager, AsyncIOWorker
from .cache_manager import CacheManager
from .config_validator import ConfigValidator, validate_all_configs
from .exception_handler import ExceptionHandler

# Internationalization
from .i18n import set_language, setup_i18n, t
from .i18n_ui import I18nUI
from .i18n_updater import I18nUpdater

# Utilities
from .json_utils import JsonUtils
from .logging_config import get_logger, setup_logging
from .memory_optimizer import MemoryOptimizer, create_object_pool, optimize_memory
from .optimization_validator import OptimizationValidator, benchmark_function, validate_optimization
from .performance_analyzer import PerformanceAnalyzer
from .resource_manager import cleanup_on_exit, resource_manager
from .signal_bus import signalBus
from .signal_utils import SignalManager, SignalConnection, ConnectionType
from .ui_utils import UIComponentManager, create_responsive_operation, batch_ui_update
from .workflow_optimizer import WorkflowOptimizer, create_workflow, execute_workflow

__all__: list[str] = [
    # Core infrastructure
    "SingletonApplication",
    "setup_logging",
    "get_logger",
    "validate_all_configs",
    "ConfigValidator",
    "ExceptionHandler",
    "resource_manager",
    "cleanup_on_exit",
    # Internationalization
    "setup_i18n",
    "set_language",
    "t",
    "I18nUI",
    "I18nUpdater",
    # Utilities
    "JsonUtils",
    "AsyncIOUtils",
    "CacheManager",
    "MemoryOptimizer",
    "OptimizationValidator",
    "PerformanceAnalyzer",
    "WorkflowOptimizer",
    "signalBus",
    "SignalUtils",
    "UIUtils",
    # Optimization functions
    "create_object_pool",
    "optimize_memory",
    "benchmark_function",
    "validate_optimization",
    "create_workflow",
    "execute_workflow",
    "create_responsive_operation",
    "batch_ui_update",
]
