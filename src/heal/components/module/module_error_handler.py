"""
Module Error Handler

Centralized error handling system with user-friendly messages, contextual help,
recovery suggestions, and comprehensive error reporting and analytics.
"""

import json
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QObject, Signal

from src.heal.common.logging_config import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization"""

    VALIDATION = "validation"
    DOWNLOAD = "download"
    INSTALLATION = "installation"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    PERMISSION = "permission"
    DEPENDENCY = "dependency"
    SYSTEM = "system"
    USER_INPUT = "user_input"


@dataclass
class ErrorContext:
    """Context information for errors"""

    module_name: Optional[str] = None
    operation: Optional[str] = None
    file_path: Optional[str] = None
    user_action: Optional[str] = None
    system_state: Dict[str, Any] = field(default_factory=dict)
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAction:
    """Recovery action suggestion"""

    action_id: str
    title: str
    description: str
    action_type: str  # 'automatic', 'user_guided', 'manual'
    handler: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleError:
    """Comprehensive error information"""

    error_id: str
    timestamp: float
    severity: ErrorSeverity
    category: ErrorCategory
    title: str
    message: str
    technical_details: str
    context: ErrorContext
    recovery_actions: List[RecoveryAction] = field(default_factory=list)
    user_friendly_message: str = ""
    help_url: Optional[str] = None
    resolved: bool = False
    resolution_notes: str = ""


class ModuleErrorHandler(QObject):
    """Centralized error handling and recovery system"""

    # Signals for error events
    error_occurred = Signal(str)  # error_id
    error_resolved = Signal(str)  # error_id
    recovery_action_executed = Signal(str, str)  # error_id, action_id

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = logger.bind(component="ModuleErrorHandler")

        # Error storage
        self.errors: Dict[str, ModuleError] = {}
        self.error_patterns: Dict[str, Dict[str, Any]] = {}

        # Error persistence
        self.errors_file = Path("logs/module_errors.json")
        self.errors_file.parent.mkdir(exist_ok=True)

        # Recovery handlers
        self.recovery_handlers: Dict[str, Callable] = {}

        # Load error patterns and previous errors
        self.load_error_patterns()
        self.load_errors()

        self.logger.info("Module Error Handler initialized")

    def register_recovery_handler(self, action_id: str, handler: Callable) -> None:
        """Register a recovery action handler"""
        self.recovery_handlers[action_id] = handler
        self.logger.debug(f"Registered recovery handler: {action_id}")

    def handle_error(
        self,
        exception: Exception,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        context: Optional[ErrorContext] = None,
        custom_message: Optional[str] = None,
    ) -> str:
        """Handle an error and return error ID"""

        error_id = f"error_{int(time.time() * 1000)}"

        # Extract error information
        error_type = type(exception).__name__
        error_message = str(exception)
        technical_details = traceback.format_exc()

        # Create error context if not provided
        if context is None:
            context = ErrorContext()

        # Generate user-friendly message
        user_friendly_message = custom_message or self._generate_user_friendly_message(
            exception, category, context
        )

        # Create error object
        error = ModuleError(
            error_id=error_id,
            timestamp=time.time(),
            severity=severity,
            category=category,
            title=f"{error_type}: {category.value.title()} Error",
            message=error_message,
            technical_details=technical_details,
            context=context,
            user_friendly_message=user_friendly_message,
        )

        # Generate recovery actions
        error.recovery_actions = self._generate_recovery_actions(
            exception, category, context
        )

        # Add help URL if available
        error.help_url = self._get_help_url(category, error_type)

        # Store error
        self.errors[error_id] = error

        # Log error
        self.logger.error(
            f"Error {error_id}: {error_message}",
            extra={"error_id": error_id, "category": category.value},
        )

        # Emit signal
        self.error_occurred.emit(error_id)

        # Auto-save errors
        self.save_errors()

        return error_id

    def handle_validation_error(
        self, validation_issues: List[Dict[str, Any]], module_name: str
    ) -> str:
        """Handle module validation errors"""
        context = ErrorContext(
            module_name=module_name,
            operation="validation",
            additional_data={"validation_issues": validation_issues},
        )

        # Create synthetic exception for validation errors
        issue_count = len(validation_issues)
        critical_issues = [
            i for i in validation_issues if i.get("level") == "CRITICAL"]

        if critical_issues:
            severity = ErrorSeverity.CRITICAL
            message = (
                f"Module validation failed with {len(critical_issues)} critical issues"
            )
        else:
            severity = ErrorSeverity.WARNING
            message = f"Module validation completed with {issue_count} issues"

        exception = ValueError(message)

        return self.handle_error(
            exception=exception,
            severity=severity,
            category=ErrorCategory.VALIDATION,
            context=context,
            custom_message=f"Module '{module_name}' has validation issues that need attention.",
        )

    def execute_recovery_action(self, error_id: str, action_id: str) -> bool:
        """Execute a recovery action for an error"""
        if error_id not in self.errors:
            self.logger.error(f"Error {error_id} not found")
            return False

        error = self.errors[error_id]

        # Find recovery action
        recovery_action = None
        for action in error.recovery_actions:
            if action.action_id == action_id:
                recovery_action = action
                break

        if not recovery_action:
            self.logger.error(
                f"Recovery action {action_id} not found for error {error_id}"
            )
            return False

        try:
            # Execute recovery action
            if recovery_action.handler:
                success = recovery_action.handler(
                    error, recovery_action.parameters)
            elif action_id in self.recovery_handlers:
                handler = self.recovery_handlers[action_id]
                success = handler(error, recovery_action.parameters)
            else:
                self.logger.error(
                    f"No handler found for recovery action {action_id}")
                return False

            if success:
                self.recovery_action_executed.emit(error_id, action_id)
                self.logger.info(
                    f"Recovery action {action_id} executed successfully for error {error_id}"
                )
                return True
            else:
                self.logger.warning(
                    f"Recovery action {action_id} failed for error {error_id}"
                )
                return False

        except Exception as e:
            self.logger.error(
                f"Error executing recovery action {action_id}: {e}")
            return False

    def resolve_error(self, error_id: str, resolution_notes: str = "") -> None:
        """Mark an error as resolved"""
        if error_id in self.errors:
            error = self.errors[error_id]
            error.resolved = True
            error.resolution_notes = resolution_notes

            self.error_resolved.emit(error_id)
            self.logger.info(f"Error {error_id} marked as resolved")

            # Save updated error state
            self.save_errors()

    def get_error(self, error_id: str) -> Optional[ModuleError]:
        """Get error by ID"""
        return self.errors.get(error_id)

    def get_errors_by_category(self, category: ErrorCategory) -> List[ModuleError]:
        """Get errors by category"""
        return [error for error in self.errors.values() if error.category == category]

    def get_errors_by_module(self, module_name: str) -> List[ModuleError]:
        """Get errors for a specific module"""
        return [
            error
            for error in self.errors.values()
            if error.context.module_name == module_name
        ]

    def get_unresolved_errors(self) -> List[ModuleError]:
        """Get all unresolved errors"""
        return [error for error in self.errors.values() if not error.resolved]

    def get_recent_errors(self, hours: int = 24) -> List[ModuleError]:
        """Get errors from the last N hours"""
        cutoff_time = time.time() - (hours * 3600)
        return [
            error for error in self.errors.values() if error.timestamp > cutoff_time
        ]

    def clear_resolved_errors(self) -> None:
        """Clear all resolved errors"""
        resolved_count = len([e for e in self.errors.values() if e.resolved])
        self.errors = {
            eid: error for eid, error in self.errors.items() if not error.resolved
        }
        self.logger.info(f"Cleared {resolved_count} resolved errors")
        self.save_errors()

    def export_error_report(
        self, filepath: str, include_resolved: bool = False
    ) -> bool:
        """Export error report to file"""
        try:
            errors_to_export = list(self.errors.values())
            if not include_resolved:
                errors_to_export = [
                    e for e in errors_to_export if not e.resolved]

            report_data: Dict[str, Any] = {
                "generated_at": time.time(),
                "total_errors": len(errors_to_export),
                "errors": [],
            }

            for error in errors_to_export:
                error_data = {
                    "error_id": error.error_id,
                    "timestamp": error.timestamp,
                    "severity": error.severity.value,
                    "category": error.category.value,
                    "title": error.title,
                    "message": error.message,
                    "user_friendly_message": error.user_friendly_message,
                    "context": {
                        "module_name": error.context.module_name,
                        "operation": error.context.operation,
                        "file_path": error.context.file_path,
                        "user_action": error.context.user_action,
                    },
                    "recovery_actions": [
                        {
                            "action_id": action.action_id,
                            "title": action.title,
                            "description": action.description,
                            "action_type": action.action_type,
                        }
                        for action in error.recovery_actions
                    ],
                    "resolved": error.resolved,
                    "resolution_notes": error.resolution_notes,
                }
                report_data["errors"].append(error_data)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Error report exported to {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting report: {e}")
            return False

    def _generate_user_friendly_message(
        self, exception: Exception, category: ErrorCategory, context: ErrorContext
    ) -> str:
        """Generate user-friendly error message"""
        error_type = type(exception).__name__

        # Category-specific messages
        if category == ErrorCategory.VALIDATION:
            return f"The module '{context.module_name or 'selected'}' has validation issues that prevent it from being used safely."

        elif category == ErrorCategory.DOWNLOAD:
            return "There was a problem downloading the module. Please check your internet connection and try again."

        elif category == ErrorCategory.INSTALLATION:
            return f"The module '{context.module_name or 'selected'}' could not be installed. This might be due to file permissions or disk space issues."

        elif category == ErrorCategory.NETWORK:
            return "A network error occurred. Please check your internet connection and proxy settings."

        elif category == ErrorCategory.FILESYSTEM:
            return "A file system error occurred. Please check file permissions and available disk space."

        elif category == ErrorCategory.PERMISSION:
            return "Permission denied. Please run the application with appropriate permissions or check file access rights."

        elif category == ErrorCategory.DEPENDENCY:
            return f"The module '{context.module_name or 'selected'}' has missing or incompatible dependencies."

        else:
            return f"An unexpected error occurred: {str(exception)}"

    def _generate_recovery_actions(
        self, exception: Exception, category: ErrorCategory, context: ErrorContext
    ) -> List[RecoveryAction]:
        """Generate recovery action suggestions"""
        actions = []

        # Common actions
        actions.append(
            RecoveryAction(
                action_id="retry_operation",
                title="Retry Operation",
                description="Try the operation again",
                action_type="user_guided",
            )
        )

        # Category-specific actions
        if category == ErrorCategory.DOWNLOAD:
            actions.extend(
                [
                    RecoveryAction(
                        action_id="check_network",
                        title="Check Network Connection",
                        description="Verify internet connectivity and proxy settings",
                        action_type="manual",
                    ),
                    RecoveryAction(
                        action_id="change_download_location",
                        title="Change Download Location",
                        description="Select a different download directory",
                        action_type="user_guided",
                    ),
                ]
            )

        elif category == ErrorCategory.VALIDATION:
            actions.extend(
                [
                    RecoveryAction(
                        action_id="view_validation_details",
                        title="View Validation Details",
                        description="See detailed validation report",
                        action_type="user_guided",
                    ),
                    RecoveryAction(
                        action_id="ignore_validation_warnings",
                        title="Ignore Warnings",
                        description="Proceed despite validation warnings (not recommended)",
                        action_type="user_guided",
                    ),
                ]
            )

        elif category == ErrorCategory.PERMISSION:
            actions.extend(
                [
                    RecoveryAction(
                        action_id="run_as_admin",
                        title="Run as Administrator",
                        description="Restart the application with elevated privileges",
                        action_type="manual",
                    ),
                    RecoveryAction(
                        action_id="change_permissions",
                        title="Fix File Permissions",
                        description="Automatically fix file and folder permissions",
                        action_type="automatic",
                    ),
                ]
            )

        elif category == ErrorCategory.FILESYSTEM:
            actions.extend(
                [
                    RecoveryAction(
                        action_id="check_disk_space",
                        title="Check Disk Space",
                        description="Verify available disk space",
                        action_type="automatic",
                    ),
                    RecoveryAction(
                        action_id="clean_temp_files",
                        title="Clean Temporary Files",
                        description="Remove temporary files to free up space",
                        action_type="automatic",
                    ),
                ]
            )

        return actions

    def _get_help_url(self, category: ErrorCategory, error_type: str) -> Optional[str]:
        """Get help URL for error category"""
        base_url = "https://docs.example.com/troubleshooting"

        help_urls = {
            ErrorCategory.VALIDATION: f"{base_url}/validation-errors",
            ErrorCategory.DOWNLOAD: f"{base_url}/download-issues",
            ErrorCategory.INSTALLATION: f"{base_url}/installation-problems",
            ErrorCategory.NETWORK: f"{base_url}/network-connectivity",
            ErrorCategory.PERMISSION: f"{base_url}/permission-issues",
            ErrorCategory.DEPENDENCY: f"{base_url}/dependency-problems",
        }

        return help_urls.get(category)

    def load_error_patterns(self) -> None:
        """Load error patterns for better error recognition"""
        patterns_file = Path("config/error_patterns.json")
        if patterns_file.exists():
            try:
                with open(patterns_file, "r", encoding="utf-8") as f:
                    self.error_patterns = json.load(f)
                self.logger.info("Error patterns loaded")
            except Exception as e:
                self.logger.error(f"Error loading error patterns: {e}")

    def save_errors(self) -> None:
        """Save errors to disk"""
        try:
            # Convert errors to serializable format
            errors_data = {}
            for error_id, error in self.errors.items():
                errors_data[error_id] = {
                    "error_id": error.error_id,
                    "timestamp": error.timestamp,
                    "severity": error.severity.value,
                    "category": error.category.value,
                    "title": error.title,
                    "message": error.message,
                    "technical_details": error.technical_details,
                    "user_friendly_message": error.user_friendly_message,
                    "help_url": error.help_url,
                    "resolved": error.resolved,
                    "resolution_notes": error.resolution_notes,
                    "context": {
                        "module_name": error.context.module_name,
                        "operation": error.context.operation,
                        "file_path": error.context.file_path,
                        "user_action": error.context.user_action,
                        "system_state": error.context.system_state,
                        "additional_data": error.context.additional_data,
                    },
                    "recovery_actions": [
                        {
                            "action_id": action.action_id,
                            "title": action.title,
                            "description": action.description,
                            "action_type": action.action_type,
                            "parameters": action.parameters,
                        }
                        for action in error.recovery_actions
                    ],
                }

            with open(self.errors_file, "w", encoding="utf-8") as f:
                json.dump(errors_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Error saving errors: {e}")

    def load_errors(self) -> None:
        """Load errors from disk"""
        if not self.errors_file.exists():
            return

        try:
            with open(self.errors_file, "r", encoding="utf-8") as f:
                errors_data = json.load(f)

            for error_id, data in errors_data.items():
                # Reconstruct error context
                context = ErrorContext(
                    module_name=data["context"]["module_name"],
                    operation=data["context"]["operation"],
                    file_path=data["context"]["file_path"],
                    user_action=data["context"]["user_action"],
                    system_state=data["context"]["system_state"],
                    additional_data=data["context"]["additional_data"],
                )

                # Reconstruct recovery actions
                recovery_actions = []
                for action_data in data["recovery_actions"]:
                    recovery_actions.append(
                        RecoveryAction(
                            action_id=action_data["action_id"],
                            title=action_data["title"],
                            description=action_data["description"],
                            action_type=action_data["action_type"],
                            parameters=action_data["parameters"],
                        )
                    )

                # Reconstruct error
                error = ModuleError(
                    error_id=data["error_id"],
                    timestamp=data["timestamp"],
                    severity=ErrorSeverity(data["severity"]),
                    category=ErrorCategory(data["category"]),
                    title=data["title"],
                    message=data["message"],
                    technical_details=data["technical_details"],
                    context=context,
                    recovery_actions=recovery_actions,
                    user_friendly_message=data["user_friendly_message"],
                    help_url=data["help_url"],
                    resolved=data["resolved"],
                    resolution_notes=data["resolution_notes"],
                )

                self.errors[error_id] = error

            self.logger.info(f"Loaded {len(errors_data)} errors from disk")

        except Exception as e:
            self.logger.error(f"Error loading errors: {e}")
