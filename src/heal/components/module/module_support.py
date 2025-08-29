"""
Module Support Components
Consolidated error handling, notifications, and support functionality.
Merges previously separate support systems into cohesive units.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer

from ...common.logging_config import get_logger

# Re-export from existing modules for backward compatibility
from .module_error_handler import (
    ErrorCategory,
    ErrorContext, 
    ErrorSeverity,
    ModuleError,
    RecoveryAction
)
from .module_notification_system import (
    Notification,
    NotificationAction,
    NotificationPriority,
    NotificationType
)
from .module_bulk_operations import (
    BulkOperation,
    BulkOperationStatus,
    BulkOperationType,
    ModuleOperationResult
)

logger = get_logger(__name__)


class ModuleErrorHandler(QObject):
    """
    Consolidated error handler that provides unified error management
    for all module operations. Integrates with notification system.
    """
    
    error_occurred = Signal(str)  # error_id
    error_resolved = Signal(str)  # error_id
    recovery_suggested = Signal(str, list)  # error_id, recovery_actions
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.ModuleErrorHandler")
        
        self.errors: Dict[str, ModuleError] = {}
        self.error_patterns: Dict[str, List[str]] = {}
        self.recovery_handlers: Dict[str, Callable] = {}
        
        # Error persistence
        self.error_file = Path("config/module_errors.json")
        self.load_errors()
        
        self.logger.info("ModuleErrorHandler initialized")
    
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
        
        # Store error
        self.errors[error_id] = error
        
        # Log error
        self.logger.error(
            f"Error {error_id}: {error_message}",
            extra={"error_id": error_id, "category": category.value},
        )
        
        # Emit signals
        self.error_occurred.emit(error_id)
        if error.recovery_actions:
            self.recovery_suggested.emit(error_id, error.recovery_actions)
        
        # Save errors
        self.save_errors()
        
        return error_id
    
    def resolve_error(self, error_id: str, resolution_notes: str = "") -> None:
        """Mark an error as resolved"""
        if error_id in self.errors:
            error = self.errors[error_id]
            error.resolved = True
            error.resolution_notes = resolution_notes
            
            self.error_resolved.emit(error_id)
            self.logger.info(f"Error {error_id} marked as resolved")
            
            self.save_errors()
    
    def get_error(self, error_id: str) -> Optional[ModuleError]:
        """Get error by ID"""
        return self.errors.get(error_id)
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ModuleError]:
        """Get errors by category"""
        return [error for error in self.errors.values() if error.category == category]
    
    def get_unresolved_errors(self) -> List[ModuleError]:
        """Get unresolved errors"""
        return [error for error in self.errors.values() if not error.resolved]
    
    def _generate_user_friendly_message(
        self, exception: Exception, category: ErrorCategory, context: ErrorContext
    ) -> str:
        """Generate user-friendly error message"""
        error_type = type(exception).__name__
        
        # Common error patterns
        if error_type == "FileNotFoundError":
            return f"Required file not found: {str(exception)}"
        elif error_type == "PermissionError":
            return "Permission denied. Please check file permissions."
        elif error_type == "ConnectionError":
            return "Network connection failed. Please check your internet connection."
        elif error_type == "ImportError":
            return f"Missing dependency: {str(exception)}"
        else:
            return f"An error occurred: {str(exception)}"
    
    def _generate_recovery_actions(
        self, exception: Exception, category: ErrorCategory, context: ErrorContext
    ) -> List[RecoveryAction]:
        """Generate recovery actions for the error"""
        actions = []
        error_type = type(exception).__name__
        
        if error_type == "FileNotFoundError":
            actions.append(RecoveryAction(
                action_id="check_file_path",
                title="Check File Path",
                description="Verify the file path is correct",
                action_type="manual"
            ))
        elif error_type == "PermissionError":
            actions.append(RecoveryAction(
                action_id="fix_permissions",
                title="Fix Permissions",
                description="Grant appropriate file permissions",
                action_type="manual"
            ))
        elif error_type == "ConnectionError":
            actions.append(RecoveryAction(
                action_id="retry_connection",
                title="Retry Connection",
                description="Try the operation again",
                action_type="automatic"
            ))
        
        return actions
    
    def load_errors(self) -> None:
        """Load errors from file"""
        try:
            if self.error_file.exists():
                with open(self.error_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load errors (simplified for now)
                self.logger.debug("Errors loaded from file")
                
        except Exception as e:
            self.logger.error(f"Failed to load errors: {e}")
    
    def save_errors(self) -> None:
        """Save errors to file"""
        try:
            self.error_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save basic error info (simplified for now)
            data = {
                'error_count': len(self.errors),
                'last_updated': time.time()
            }
            
            with open(self.error_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save errors: {e}")


class ModuleNotificationSystem(QObject):
    """
    Consolidated notification system that provides unified notification management
    for all module operations. Integrates with error handling system.
    """
    
    notification_added = Signal(str)  # notification_id
    notification_dismissed = Signal(str)  # notification_id
    notification_action_triggered = Signal(str, str)  # notification_id, action_id
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.ModuleNotificationSystem")
        
        self.notifications: Dict[str, Notification] = {}
        self.action_handlers: Dict[str, Callable] = {}
        self.notification_queue: List[str] = []
        
        # Queue processing
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.process_queue)
        self.queue_timer.start(500)  # Process every 500ms
        
        self.logger.info("ModuleNotificationSystem initialized")
    
    def show_info(self, title: str, message: str, **kwargs: Any) -> str:
        """Show info notification"""
        return self.add_notification(
            title=title,
            message=message,
            notification_type=NotificationType.INFO,
            **kwargs,
        )
    
    def show_warning(self, title: str, message: str, **kwargs: Any) -> str:
        """Show warning notification"""
        return self.add_notification(
            title=title,
            message=message,
            notification_type=NotificationType.WARNING,
            **kwargs,
        )
    
    def show_error(self, title: str, message: str, **kwargs: Any) -> str:
        """Show error notification"""
        return self.add_notification(
            title=title,
            message=message,
            notification_type=NotificationType.ERROR,
            **kwargs,
        )
    
    def show_success(self, title: str, message: str, **kwargs: Any) -> str:
        """Show success notification"""
        return self.add_notification(
            title=title,
            message=message,
            notification_type=NotificationType.SUCCESS,
            **kwargs,
        )
    
    def add_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        duration: int = 5000,
        module_name: Optional[str] = None,
        category: Optional[str] = None,
        actions: Optional[List[NotificationAction]] = None,
        **kwargs: Any,
    ) -> str:
        """Add a new notification"""
        
        notification_id = f"notif_{int(time.time() * 1000)}"
        
        notification = Notification(
            notification_id=notification_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            duration=duration,
            module_name=module_name,
            category=category,
            actions=actions or [],
            **kwargs,
        )
        
        # Store notification
        self.notifications[notification_id] = notification
        
        # Add to queue based on priority
        self._add_to_queue(notification_id)
        
        # Emit signal
        self.notification_added.emit(notification_id)
        
        self.logger.info(f"Added notification: {title}")
        return notification_id
    
    def dismiss_notification(self, notification_id: str) -> None:
        """Dismiss a notification"""
        if notification_id in self.notifications:
            self.notifications[notification_id].dismissed = True
            self.notification_dismissed.emit(notification_id)
            self.logger.debug(f"Dismissed notification: {notification_id}")
    
    def process_queue(self) -> None:
        """Process notification queue"""
        if not self.notification_queue:
            return
        
        # Process highest priority notification
        notification_id = self.notification_queue.pop(0)
        if notification_id in self.notifications:
            notification = self.notifications[notification_id]
            if not notification.dismissed and not notification.shown:
                self._show_notification(notification)
    
    def _add_to_queue(self, notification_id: str) -> None:
        """Add notification to queue based on priority"""
        if notification_id not in self.notifications:
            return
        
        notification = self.notifications[notification_id]
        
        # Insert based on priority
        if notification.priority == NotificationPriority.HIGH:
            self.notification_queue.insert(0, notification_id)
        else:
            self.notification_queue.append(notification_id)
    
    def _show_notification(self, notification: Notification) -> None:
        """Show notification (placeholder for actual UI implementation)"""
        notification.shown = True
        notification.timestamp = time.time()
        self.logger.debug(f"Showing notification: {notification.title}")
