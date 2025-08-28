"""
Debug Components Module
Provides debugging and monitoring tools for the HEAL application
"""

from .startup_performance_dashboard import (
    StartupPerformanceDashboard,
    show_startup_performance_dashboard
)

__all__ = [
    "StartupPerformanceDashboard",
    "show_startup_performance_dashboard"
]
