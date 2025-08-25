"""
Module components package
Contains all modular components for the module interface with enhanced workflow management,
error handling, notifications, and bulk operations support.
"""

# Core models and managers
from .module_models import ModuleState, ModuleMetrics, ModuleConfig
from .module_event_manager import ModuleEventManager
from .module_config_manager import ModuleConfigManager
from .module_metrics_manager import ModuleMetricsManager
from .module_operation_handler import ModuleOperationHandler
from .scaffold_wrapper import ScaffoldAppWrapper

# Enhanced workflow and error handling
from .module_workflow_manager import (
    ModuleWorkflowManager, WorkflowStep, WorkflowStatus,
    ModuleWorkflow, WorkflowStepInfo
)
from .module_error_handler import (
    ModuleErrorHandler, ErrorSeverity, ErrorCategory,
    ErrorContext, RecoveryAction, ModuleError
)
from .module_notification_system import (
    ModuleNotificationSystem, NotificationType, NotificationPriority,
    Notification, NotificationAction
)
from .module_bulk_operations import (
    ModuleBulkOperations, BulkOperationType, BulkOperationStatus,
    BulkOperation, ModuleOperationResult
)

# UI Components
from .mod_manager import ModManager
from .mod_download import ModDownload
from .module_dashboard import ModuleDashboard
from .performance_dashboard_ui import PerformanceDashboardUI

__all__ = [
    # Core models and managers
    'ModuleState',
    'ModuleMetrics',
    'ModuleConfig',
    'ModuleEventManager',
    'ModuleConfigManager',
    'ModuleMetricsManager',
    'ModuleOperationHandler',
    'ScaffoldAppWrapper',

    # Enhanced workflow and error handling
    'ModuleWorkflowManager',
    'WorkflowStep',
    'WorkflowStatus',
    'ModuleWorkflow',
    'WorkflowStepInfo',
    'ModuleErrorHandler',
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorContext',
    'RecoveryAction',
    'ModuleError',
    'ModuleNotificationSystem',
    'NotificationType',
    'NotificationPriority',
    'Notification',
    'NotificationAction',
    'ModuleBulkOperations',
    'BulkOperationType',
    'BulkOperationStatus',
    'BulkOperation',
    'ModuleOperationResult',

    # UI Components
    'ModManager',
    'ModDownload',
    'ModuleDashboard',
    'PerformanceDashboardUI'
]
