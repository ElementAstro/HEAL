"""
Module Bulk Operations

Implements multi-select functionality for batch operations including bulk enable/disable,
validate, update modules with comprehensive progress tracking and error handling.
"""

import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from PySide6.QtCore import QMutex, QMutexLocker, QObject, QThread, Signal

from src.heal.common.logging_config import get_logger
from .module_error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    ModuleErrorHandler,
)
from .module_models import ModuleState
from .module_notification_system import (
    ModuleNotificationSystem,
    NotificationPriority,
    NotificationType,
)

logger = get_logger(__name__)


class BulkOperationType(Enum):
    """Types of bulk operations"""

    ENABLE = "enable"
    DISABLE = "disable"
    VALIDATE = "validate"
    UPDATE = "update"
    DELETE = "delete"
    INSTALL = "install"
    CONFIGURE = "configure"
    BACKUP = "backup"
    RESTORE = "restore"


class BulkOperationStatus(Enum):
    """Status of bulk operations"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


@dataclass
class ModuleOperationResult:
    """Result of a single module operation"""

    module_name: str
    success: bool
    message: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BulkOperationProgress:
    """Progress tracking for bulk operations"""

    total_modules: int
    completed_modules: int = 0
    successful_modules: int = 0
    failed_modules: int = 0
    current_module: Optional[str] = None
    overall_progress: float = 0.0
    estimated_time_remaining: float = 0.0
    start_time: float = field(default_factory=time.time)

    @property
    def completion_rate(self) -> float:
        """Calculate completion rate percentage"""
        if self.total_modules == 0:
            return 100.0
        return (self.completed_modules / self.total_modules) * 100.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.completed_modules == 0:
            return 100.0
        return (self.successful_modules / self.completed_modules) * 100.0


@dataclass
class BulkOperation:
    """Bulk operation definition"""

    operation_id: str
    operation_type: BulkOperationType
    module_names: List[str]
    status: BulkOperationStatus = BulkOperationStatus.PENDING
    progress: BulkOperationProgress | None = None
    results: List[ModuleOperationResult] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    notification_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.progress is None:
            self.progress = BulkOperationProgress(total_modules=len(self.module_names))


class BulkOperationWorker(QThread):
    """Worker thread for executing bulk operations"""

    progress_updated = Signal(str, dict)  # operation_id, progress_data
    operation_completed = Signal(str, bool)  # operation_id, success
    module_completed = Signal(
        str, str, bool, str
    )  # operation_id, module_name, success, message

    def __init__(
        self, operation: BulkOperation, operation_handler: Callable, parent: Any = None
    ) -> None:
        super().__init__(parent)
        self.operation = operation
        self.operation_handler = operation_handler
        self.cancelled = False
        self.mutex = QMutex()

    def run(self) -> None:
        """Execute the bulk operation"""
        try:
            self.operation.status = BulkOperationStatus.RUNNING
            self.operation.started_at = time.time()

            # Execute operations with thread pool for better performance
            max_workers = min(
                4, len(self.operation.module_names)
            )  # Limit concurrent operations

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all module operations
                future_to_module = {
                    executor.submit(
                        self._execute_single_operation, module_name
                    ): module_name
                    for module_name in self.operation.module_names
                }

                # Process completed operations
                for future in as_completed(future_to_module):
                    if self.cancelled:
                        break

                    module_name = future_to_module[future]

                    try:
                        result = future.result()
                        self.operation.results.append(result)

                        # Update progress
                        with QMutexLocker(self.mutex):
                            if self.operation.progress:
                                self.operation.progress.completed_modules += 1
                                if result.success:
                                    self.operation.progress.successful_modules += 1
                                else:
                                    self.operation.progress.failed_modules += 1

                                self.operation.progress.overall_progress = (
                                    self.operation.progress.completion_rate
                                )
                                self.operation.progress.current_module = module_name

                                # Estimate remaining time
                                elapsed_time = (
                                    time.time() - self.operation.progress.start_time
                                )
                                if self.operation.progress.completed_modules > 0:
                                    avg_time_per_module = (
                                        elapsed_time
                                        / self.operation.progress.completed_modules
                                    )
                                    remaining_modules = (
                                        self.operation.progress.total_modules
                                        - self.operation.progress.completed_modules
                                    )
                                    self.operation.progress.estimated_time_remaining = (
                                        avg_time_per_module * remaining_modules
                                    )

                        # Emit signals
                        self.module_completed.emit(
                            self.operation.operation_id,
                            module_name,
                            result.success,
                            result.message,
                        )

                        if self.operation.progress:
                            self.progress_updated.emit(
                                self.operation.operation_id,
                                {
                                    "completed": self.operation.progress.completed_modules,
                                    "total": self.operation.progress.total_modules,
                                    "successful": self.operation.progress.successful_modules,
                                    "failed": self.operation.progress.failed_modules,
                                    "progress": self.operation.progress.overall_progress,
                                    "current_module": module_name,
                                    "estimated_remaining": self.operation.progress.estimated_time_remaining,
                                },
                            )

                    except Exception as e:
                        logger.error(f"Error processing module {module_name}: {e}")

                        # Create failed result
                        failed_result = ModuleOperationResult(
                            module_name=module_name, success=False, error=str(e)
                        )
                        self.operation.results.append(failed_result)

                        with QMutexLocker(self.mutex):
                            if self.operation.progress:
                                self.operation.progress.completed_modules += 1
                                self.operation.progress.failed_modules += 1

            # Determine final status
            if self.cancelled:
                self.operation.status = BulkOperationStatus.CANCELLED
            elif self.operation.progress and self.operation.progress.failed_modules == 0:
                self.operation.status = BulkOperationStatus.COMPLETED
            elif self.operation.progress and self.operation.progress.successful_modules == 0:
                self.operation.status = BulkOperationStatus.FAILED
            else:
                self.operation.status = BulkOperationStatus.PARTIAL

            self.operation.completed_at = time.time()

            # Emit completion signal
            overall_success = self.operation.status in [
                BulkOperationStatus.COMPLETED,
                BulkOperationStatus.PARTIAL,
            ]
            self.operation_completed.emit(self.operation.operation_id, overall_success)

        except Exception as e:
            logger.error(f"Bulk operation {self.operation.operation_id} failed: {e}")
            self.operation.status = BulkOperationStatus.FAILED
            self.operation.completed_at = time.time()
            self.operation_completed.emit(self.operation.operation_id, False)

    def _execute_single_operation(self, module_name: str) -> ModuleOperationResult:
        """Execute operation on a single module"""
        start_time = time.time()

        try:
            # Call the operation handler
            success = self.operation_handler(
                module_name, self.operation.operation_type, self.operation.parameters
            )

            duration = time.time() - start_time

            return ModuleOperationResult(
                module_name=module_name,
                success=success,
                message=f"{self.operation.operation_type.value.title()} {'successful' if success else 'failed'}",
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return ModuleOperationResult(
                module_name=module_name, success=False, error=str(e), duration=duration
            )

    def cancel(self) -> None:
        """Cancel the operation"""
        self.cancelled = True


class ModuleBulkOperations(QObject):
    """Manager for bulk module operations"""

    # Signals
    operation_started = Signal(str)  # operation_id
    operation_progress = Signal(str, dict)  # operation_id, progress_data
    operation_completed = Signal(str, bool)  # operation_id, success
    module_operation_completed = Signal(
        str, str, bool, str
    )  # operation_id, module_name, success, message

    def __init__(
        self,
        error_handler: ModuleErrorHandler,
        notification_system: ModuleNotificationSystem,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self.logger = logger.bind(component="ModuleBulkOperations")
        self.error_handler = error_handler
        self.notification_system = notification_system

        # Active operations
        self.active_operations: Dict[str, BulkOperation] = {}
        self.operation_workers: Dict[str, BulkOperationWorker] = {}

        # Operation handlers
        self.operation_handlers: Dict[BulkOperationType, Callable] = {}

        # Selection tracking
        self.selected_modules: Set[str] = set()

        self.logger.info("Module Bulk Operations initialized")

    def register_operation_handler(
        self, operation_type: BulkOperationType, handler: Callable
    ) -> None:
        """Register handler for bulk operation type"""
        self.operation_handlers[operation_type] = handler
        self.logger.debug(f"Registered handler for operation: {operation_type.value}")

    def set_selected_modules(self, module_names: List[str]) -> None:
        """Set the currently selected modules"""
        self.selected_modules = set(module_names)
        self.logger.debug(f"Selected {len(module_names)} modules for bulk operations")

    def add_to_selection(self, module_name: str) -> None:
        """Add module to selection"""
        self.selected_modules.add(module_name)

    def remove_from_selection(self, module_name: str) -> None:
        """Remove module from selection"""
        self.selected_modules.discard(module_name)

    def clear_selection(self) -> None:
        """Clear module selection"""
        self.selected_modules.clear()

    def get_selected_modules(self) -> List[str]:
        """Get currently selected modules"""
        return list(self.selected_modules)

    def execute_bulk_operation(
        self,
        operation_type: BulkOperationType,
        module_names: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Execute a bulk operation"""

        # Use selected modules if none specified
        if module_names is None:
            module_names = self.get_selected_modules()

        if not module_names:
            self.logger.warning("No modules selected for bulk operation")
            return ""

        # Check if handler exists
        if operation_type not in self.operation_handlers:
            self.logger.error(
                f"No handler registered for operation: {operation_type.value}"
            )
            return ""

        # Create operation
        operation_id = f"bulk_{operation_type.value}_{int(time.time())}"
        operation = BulkOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            module_names=module_names.copy(),
            parameters=parameters or {},
        )

        # Store operation
        self.active_operations[operation_id] = operation

        # Show notification
        notification_id = self.notification_system.show_progress(
            title=f"Bulk {operation_type.value.title()}",
            message=f"Starting {operation_type.value} operation on {len(module_names)} modules...",
            progress=0,
            module_name="bulk_operation",
            category="bulk_operation",
        )
        operation.notification_id = notification_id

        # Create and start worker
        handler = self.operation_handlers[operation_type]
        worker = BulkOperationWorker(operation, handler)
        worker.progress_updated.connect(self._on_progress_updated)
        worker.operation_completed.connect(self._on_operation_completed)
        worker.module_completed.connect(self._on_module_completed)

        self.operation_workers[operation_id] = worker
        worker.start()

        # Emit signal
        self.operation_started.emit(operation_id)

        self.logger.info(
            f"Started bulk operation {operation_id}: {operation_type.value} on {len(module_names)} modules"
        )
        return operation_id

    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a running bulk operation"""
        if operation_id not in self.operation_workers:
            return False

        worker = self.operation_workers[operation_id]
        worker.cancel()

        # Update notification
        operation = self.active_operations.get(operation_id)
        if operation and operation.notification_id and operation.progress:
            self.notification_system.update_progress(
                operation.notification_id,
                operation.progress.overall_progress,
                "Operation cancelled by user",
            )
            self.notification_system.dismiss_notification(operation.notification_id)

        self.logger.info(f"Cancelled bulk operation {operation_id}")
        return True

    def get_operation(self, operation_id: str) -> Optional[BulkOperation]:
        """Get operation by ID"""
        return self.active_operations.get(operation_id)

    def get_active_operations(self) -> List[BulkOperation]:
        """Get all active operations"""
        return [
            op
            for op in self.active_operations.values()
            if op.status in [BulkOperationStatus.PENDING, BulkOperationStatus.RUNNING]
        ]

    def get_completed_operations(self) -> List[BulkOperation]:
        """Get completed operations"""
        return [
            op
            for op in self.active_operations.values()
            if op.status
            in [
                BulkOperationStatus.COMPLETED,
                BulkOperationStatus.FAILED,
                BulkOperationStatus.CANCELLED,
                BulkOperationStatus.PARTIAL,
            ]
        ]

    def cleanup_completed_operations(self, older_than_hours: int = 24) -> None:
        """Clean up old completed operations"""
        cutoff_time = time.time() - (older_than_hours * 3600)

        operations_to_remove = []
        for operation_id, operation in self.active_operations.items():
            if (
                operation.status
                in [
                    BulkOperationStatus.COMPLETED,
                    BulkOperationStatus.FAILED,
                    BulkOperationStatus.CANCELLED,
                    BulkOperationStatus.PARTIAL,
                ]
                and operation.completed_at
                and operation.completed_at < cutoff_time
            ):
                operations_to_remove.append(operation_id)

        for operation_id in operations_to_remove:
            del self.active_operations[operation_id]
            if operation_id in self.operation_workers:
                del self.operation_workers[operation_id]

        if operations_to_remove:
            self.logger.info(f"Cleaned up {len(operations_to_remove)} old operations")

    def _on_progress_updated(self, operation_id: str, progress_data: Dict[str, Any]) -> None:
        """Handle progress updates"""
        operation = self.active_operations.get(operation_id)
        if not operation:
            return

        # Update notification
        if operation.notification_id:
            progress_message = (
                f"Processing {progress_data.get('current_module', '...')} "
                f"({progress_data['completed']}/{progress_data['total']})"
            )

            if progress_data.get("estimated_remaining", 0) > 0:
                remaining_minutes = progress_data["estimated_remaining"] / 60
                progress_message += f" - ~{remaining_minutes:.1f}m remaining"

            self.notification_system.update_progress(
                operation.notification_id, progress_data["progress"], progress_message
            )

        # Emit signal
        self.operation_progress.emit(operation_id, progress_data)

    def _on_module_completed(
        self, operation_id: str, module_name: str, success: bool, message: str
    ) -> None:
        """Handle individual module completion"""
        self.module_operation_completed.emit(
            operation_id, module_name, success, message
        )

        # Log errors
        if not success:
            operation = self.active_operations.get(operation_id)
            if operation:
                context = ErrorContext(
                    module_name=module_name,
                    operation=f"bulk_{operation.operation_type.value}",
                    additional_data={"operation_id": operation_id},
                )

                self.error_handler.handle_error(
                    exception=Exception(message),
                    severity=ErrorSeverity.WARNING,
                    category=ErrorCategory.SYSTEM,
                    context=context,
                )

    def _on_operation_completed(self, operation_id: str, success: bool) -> None:
        """Handle operation completion"""
        operation = self.active_operations.get(operation_id)
        if not operation:
            return

        # Update notification
        if operation.notification_id and operation.progress:
            if success:
                success_count = operation.progress.successful_modules
                total_count = operation.progress.total_modules

                if operation.status == BulkOperationStatus.COMPLETED:
                    title = f"Bulk {operation.operation_type.value.title()} Completed"
                    message = f"Successfully {operation.operation_type.value}d all {total_count} modules"
                    notification_type = NotificationType.SUCCESS
                else:  # PARTIAL
                    failed_count = operation.progress.failed_modules
                    title = f"Bulk {operation.operation_type.value.title()} Partially Completed"
                    message = f"Completed {success_count}/{total_count} modules ({failed_count} failed)"
                    notification_type = NotificationType.WARNING

                # Dismiss progress notification and show result
                self.notification_system.dismiss_notification(operation.notification_id)
                self.notification_system.add_notification(
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    module_name="bulk_operation",
                    category="bulk_operation",
                )
            else:
                # Show error notification
                self.notification_system.dismiss_notification(operation.notification_id)
                failed_modules = operation.progress.failed_modules if operation.progress else 0
                self.notification_system.show_error(
                    title=f"Bulk {operation.operation_type.value.title()} Failed",
                    message=f"Operation failed on {failed_modules} modules",
                    module_name="bulk_operation",
                    category="bulk_operation",
                )

        # Clean up worker
        if operation_id in self.operation_workers:
            worker = self.operation_workers[operation_id]
            worker.deleteLater()
            del self.operation_workers[operation_id]

        # Emit signal
        self.operation_completed.emit(operation_id, success)

        self.logger.info(
            f"Bulk operation {operation_id} completed with status: {operation.status.value}"
        )

    # Convenience methods for common operations
    def enable_selected_modules(self) -> str:
        """Enable all selected modules"""
        return self.execute_bulk_operation(BulkOperationType.ENABLE)

    def disable_selected_modules(self) -> str:
        """Disable all selected modules"""
        return self.execute_bulk_operation(BulkOperationType.DISABLE)

    def validate_selected_modules(self) -> str:
        """Validate all selected modules"""
        return self.execute_bulk_operation(BulkOperationType.VALIDATE)

    def update_selected_modules(self) -> str:
        """Update all selected modules"""
        return self.execute_bulk_operation(BulkOperationType.UPDATE)

    def delete_selected_modules(self) -> str:
        """Delete all selected modules"""
        return self.execute_bulk_operation(BulkOperationType.DELETE)

    def backup_selected_modules(self) -> str:
        """Backup all selected modules"""
        return self.execute_bulk_operation(BulkOperationType.BACKUP)
