"""
Module components package
Contains all modular components for the module interface with enhanced workflow management,
error handling, notifications, and bulk operations support.
"""

from .mod_download import ModDownload

# UI Components
from .mod_manager import ModManager
from .module_bulk_operations import (
    BulkOperation,
    BulkOperationStatus,
    BulkOperationType,
    ModuleBulkOperations,
    ModuleOperationResult,
)
from .module_config_manager import ModuleConfigManager
from .module_dashboard import ModuleDashboard
from .module_error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    ModuleError,
    ModuleErrorHandler,
    RecoveryAction,
)
from .module_event_manager import ModuleEventManager
from .module_metrics_manager import ModuleMetricsManager

# Core models and managers
from .module_models import ModuleConfig, ModuleMetrics, ModuleState
from .module_notification_system import (
    ModuleNotificationSystem,
    Notification,
    NotificationAction,
    NotificationPriority,
    NotificationType,
)
from .module_operation_handler import ModuleOperationHandler

# Enhanced workflow and error handling
from .module_workflow_manager import (
    ModuleWorkflow,
    ModuleWorkflowManager,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepInfo,
)
from .performance_dashboard_ui import PerformanceDashboardUI
from .scaffold_wrapper import ScaffoldAppWrapper

__all__: list[str] = [
    # Core models and managers
    "ModuleState",
    "ModuleMetrics",
    "ModuleConfig",
    "ModuleEventManager",
    "ModuleConfigManager",
    "ModuleMetricsManager",
    "ModuleOperationHandler",
    "ScaffoldAppWrapper",
    # Enhanced workflow and error handling
    "ModuleWorkflowManager",
    "WorkflowStep",
    "WorkflowStatus",
    "ModuleWorkflow",
    "WorkflowStepInfo",
    "ModuleErrorHandler",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "RecoveryAction",
    "ModuleError",
    "ModuleNotificationSystem",
    "NotificationType",
    "NotificationPriority",
    "Notification",
    "NotificationAction",
    "ModuleBulkOperations",
    "BulkOperationType",
    "BulkOperationStatus",
    "BulkOperation",
    "ModuleOperationResult",
    # UI Components
    "ModManager",
    "ModDownload",
    "ModuleDashboard",
    "PerformanceDashboardUI",
]
