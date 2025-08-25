"""
Monitoring Components Package

Contains components for monitoring various aspects of the application including:
- Download monitoring and progress tracking
- Process monitoring and management
- Performance monitoring and metrics
- System resource monitoring
"""

from .download_monitor import DownloadItemCard, DownloadManagerWidget
from .process_monitor import ProcessMonitorWidget, ProcessStatusCard

__all__: list[str] = [
    "DownloadManagerWidget",
    "DownloadItemCard",
    "ProcessMonitorWidget",
    "ProcessStatusCard",
]

# Package metadata
__version__ = "1.0.0"
__author__ = "HEAL Development Team"
__description__ = "Monitoring components for HEAL application"
