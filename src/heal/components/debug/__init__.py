"""
Debug Components Module
Provides unified debugging and monitoring tools for the HEAL application.
Components have been consolidated into a comprehensive debug system.
"""

# Unified debug system
from .unified_debug_system import (
    UnifiedDebugSystem,
    DebugLevel,
    DebugCategory,
    DebugEvent,
    PerformanceMetric
)

# Legacy components - for backward compatibility
from .startup_performance_dashboard import (
    StartupPerformanceDashboard,
    show_startup_performance_dashboard
)

__all__ = [
    # Unified debug system
    "UnifiedDebugSystem",
    "DebugLevel",
    "DebugCategory",
    "DebugEvent",
    "PerformanceMetric",

    # Legacy components (backward compatibility)
    "StartupPerformanceDashboard",
    "show_startup_performance_dashboard"
]
