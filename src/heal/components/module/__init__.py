"""
Module components package
Contains modular components for the module interface with clear separation between
UI components, business logic, and data models.
"""

# UI Components - User interface elements
from .mod_manager import ModManager
from .mod_download import ModDownload
from .module_dashboard import ModuleDashboard
from .performance_dashboard_ui import PerformanceDashboardUI
from .scaffold_wrapper import ScaffoldAppWrapper

# Business Logic - Core functionality and workflows
from .module_core import (
    ModuleController,
    ModuleWorkflowManager,
    ModuleOperationHandler,
    ModuleBulkOperations,
)

# Data Models and State Management
from .module_models import (
    ModuleConfig,
    ModuleMetrics,
    ModuleState,
    ModuleWorkflow,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepInfo,
)

# Error Handling and Notifications
from .module_support import (
    ModuleErrorHandler,
    ModuleNotificationSystem,
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    ModuleError,
    RecoveryAction,
    Notification,
    NotificationAction,
    NotificationPriority,
    NotificationType,
    BulkOperation,
    BulkOperationStatus,
    BulkOperationType,
    ModuleOperationResult,
)

__all__: list[str] = [
    # UI Components
    "ModManager",
    "ModDownload",
    "ModuleDashboard",
    "PerformanceDashboardUI",
    "ScaffoldAppWrapper",

    # Business Logic
    "ModuleController",
    "ModuleWorkflowManager",
    "ModuleOperationHandler",
    "ModuleBulkOperations",

    # Data Models and State
    "ModuleConfig",
    "ModuleMetrics",
    "ModuleState",
    "ModuleWorkflow",
    "WorkflowStatus",
    "WorkflowStep",
    "WorkflowStepInfo",

    # Error Handling and Notifications
    "ModuleErrorHandler",
    "ModuleNotificationSystem",
    "ErrorCategory",
    "ErrorContext",
    "ErrorSeverity",
    "ModuleError",
    "RecoveryAction",
    "Notification",
    "NotificationAction",
    "NotificationPriority",
    "NotificationType",
    "BulkOperation",
    "BulkOperationStatus",
    "BulkOperationType",
    "ModuleOperationResult",
]
