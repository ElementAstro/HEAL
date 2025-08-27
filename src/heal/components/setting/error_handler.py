"""
Settings Error Handling and Recovery System
Provides comprehensive error handling, validation, and recovery mechanisms
"""

import json
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from src.heal.common.json_utils import JsonUtils
from src.heal.common.logging_config import get_logger
from src.heal.models.config import Info


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """Recovery action types"""

    RETRY = "retry"
    USE_DEFAULT = "use_default"
    USE_BACKUP = "use_backup"
    SKIP = "skip"
    USER_INPUT = "user_input"


@dataclass
class SettingsError:
    """Settings error information"""

    error_id: str
    operation: str
    error_type: str
    message: str
    severity: ErrorSeverity
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False


@dataclass
class RecoveryStrategy:
    """Recovery strategy configuration"""

    action: RecoveryAction
    max_retries: int = 3
    retry_delay: float = 1.0
    fallback_value: Any | None = None
    custom_handler: Optional[Callable] = None


class SettingsValidator:
    """Validates settings data and operations"""

    def __init__(self) -> None:
        self.logger = get_logger("settings_validator", module="SettingsValidator")
        self.validation_rules: Dict[str, Callable] = {}

    def register_validation_rule(
        self, setting_key: str, validator: Callable[[Any], bool]
    ) -> None:
        """Register a validation rule for a setting"""
        self.validation_rules[setting_key] = validator
        self.logger.debug(f"Registered validation rule for: {setting_key}")

    def validate_setting(self, setting_key: str, value: Any) -> bool:
        """Validate a setting value"""
        validator = self.validation_rules.get(setting_key)
        if not validator:
            return True  # No validation rule, assume valid

        try:
            return bool(validator(value))
        except Exception as e:
            self.logger.error(f"Validation error for {setting_key}: {e}")
            return False

    def validate_config_file(self, file_path: str) -> List[str]:
        """Validate entire config file"""
        errors = []

        try:
            result = JsonUtils.load_json_file(file_path)
            if not result.success:
                errors.append(f"Failed to load config file: {result.error}")
                return errors

            data = result.data
            if not isinstance(data, dict):
                errors.append("Config file must contain a JSON object")
                return errors

            # Validate each setting
            for key, value in data.items():
                if not self.validate_setting(key, value):
                    errors.append(f"Invalid value for setting '{key}': {value}")

        except Exception as e:
            errors.append(f"Validation exception: {str(e)}")

        return errors


class SettingsBackupManager:
    """Manages backups of settings files"""

    def __init__(self, backup_dir: str = "config/backups") -> None:
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("settings_backup", module="SettingsBackupManager")
        self.max_backups = 10

    def create_backup(self, file_path: str) -> Optional[str]:
        """Create a backup of a settings file"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return None

            timestamp = int(time.time())
            backup_name = f"{source_path.stem}_{timestamp}.json"
            backup_path = self.backup_dir / backup_name

            # Copy file
            import shutil

            shutil.copy2(source_path, backup_path)

            # Clean old backups
            self._cleanup_old_backups(source_path.stem)

            self.logger.info(f"Created backup: {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"Failed to create backup for {file_path}: {e}")
            return None

    def restore_backup(self, file_path: str, backup_path: Optional[str] = None) -> bool:
        """Restore a settings file from backup"""
        try:
            source_path = Path(file_path)

            if backup_path:
                backup_file = Path(backup_path)
            else:
                # Find latest backup
                backup_file_result = self._find_latest_backup(source_path.stem)
                if not backup_file_result:
                    self.logger.warning(f"No backup found for {file_path}")
                    return False
                backup_file = backup_file_result

            if not backup_file.exists():
                self.logger.error(f"Backup file not found: {backup_file}")
                return False

            # Restore file
            import shutil

            shutil.copy2(backup_file, source_path)

            self.logger.info(f"Restored {file_path} from backup: {backup_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore backup for {file_path}: {e}")
            return False

    def _find_latest_backup(self, file_stem: str) -> Optional[Path]:
        """Find the latest backup for a file"""
        backups = list(self.backup_dir.glob(f"{file_stem}_*.json"))
        if not backups:
            return None

        # Sort by timestamp (newest first)
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return backups[0]

    def _cleanup_old_backups(self, file_stem: str) -> None:
        """Remove old backups, keeping only the most recent ones"""
        backups = list(self.backup_dir.glob(f"{file_stem}_*.json"))
        if len(backups) <= self.max_backups:
            return

        # Sort by timestamp (oldest first)
        backups.sort(key=lambda p: p.stat().st_mtime)

        # Remove excess backups
        for backup in backups[: -self.max_backups]:
            try:
                backup.unlink()
                self.logger.debug(f"Removed old backup: {backup}")
            except Exception as e:
                self.logger.error(f"Failed to remove old backup {backup}: {e}")


class SettingsErrorHandler(QObject):
    """Comprehensive error handling and recovery system"""

    # Signals
    error_occurred = Signal(SettingsError)
    recovery_attempted = Signal(str, str)  # error_id, action
    recovery_completed = Signal(str, bool)  # error_id, success

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(
            "settings_error_handler", module="SettingsErrorHandler"
        )
        self.validator = SettingsValidator()
        self.backup_manager = SettingsBackupManager()

        # Error tracking
        self.errors: Dict[str, SettingsError] = {}
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}

        # Default recovery strategies
        self._setup_default_strategies()

        # Error statistics
        self.error_stats = {
            "total_errors": 0,
            "recovered_errors": 0,
            "critical_errors": 0,
        }

        self.logger.info("Settings error handler initialized")

    def _setup_default_strategies(self) -> None:
        """Setup default recovery strategies"""
        # File I/O errors
        self.recovery_strategies["file_not_found"] = RecoveryStrategy(
            action=RecoveryAction.USE_BACKUP, max_retries=1
        )

        self.recovery_strategies["json_decode_error"] = RecoveryStrategy(
            action=RecoveryAction.USE_BACKUP, max_retries=1
        )

        self.recovery_strategies["permission_error"] = RecoveryStrategy(
            action=RecoveryAction.RETRY, max_retries=3, retry_delay=2.0
        )

        # Validation errors
        self.recovery_strategies["validation_error"] = RecoveryStrategy(
            action=RecoveryAction.USE_DEFAULT, max_retries=1
        )

        # Network errors
        self.recovery_strategies["network_error"] = RecoveryStrategy(
            action=RecoveryAction.RETRY, max_retries=5, retry_delay=1.0
        )

    def handle_error(
        self,
        operation: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    ) -> Optional[Any]:
        """Handle an error with automatic recovery"""
        error_id = f"{operation}_{int(time.time())}"

        settings_error = SettingsError(
            error_id=error_id,
            operation=operation,
            error_type=type(error).__name__,
            message=str(error),
            severity=severity,
            context=context or {},
            stack_trace=traceback.format_exc(),
        )

        self.errors[error_id] = settings_error
        self.error_stats["total_errors"] += 1

        if severity == ErrorSeverity.CRITICAL:
            self.error_stats["critical_errors"] += 1

        self.logger.error(f"Settings error in {operation}: {error}")
        self.error_occurred.emit(settings_error)

        # Attempt recovery
        recovery_result = self._attempt_recovery(settings_error)

        return recovery_result

    def _attempt_recovery(self, error: SettingsError) -> Optional[Any]:
        """Attempt to recover from an error"""
        strategy = self._get_recovery_strategy(error)
        if not strategy:
            self.logger.warning(f"No recovery strategy for error: {error.error_type}")
            return None

        error.recovery_attempted = True
        self.recovery_attempted.emit(error.error_id, strategy.action.value)

        recovery_result = None

        try:
            if strategy.action == RecoveryAction.RETRY:
                recovery_result = self._retry_operation(error, strategy)
            elif strategy.action == RecoveryAction.USE_DEFAULT:
                recovery_result = self._use_default_value(error, strategy)
            elif strategy.action == RecoveryAction.USE_BACKUP:
                recovery_result = self._restore_from_backup(error, strategy)
            elif strategy.action == RecoveryAction.USER_INPUT:
                recovery_result = self._request_user_input(error, strategy)
            elif strategy.custom_handler:
                recovery_result = strategy.custom_handler(error)

            if recovery_result is not None:
                error.recovery_successful = True
                self.error_stats["recovered_errors"] += 1
                self.logger.info(f"Successfully recovered from error: {error.error_id}")

        except Exception as recovery_error:
            self.logger.error(f"Recovery failed for {error.error_id}: {recovery_error}")

        self.recovery_completed.emit(error.error_id, error.recovery_successful)
        return recovery_result

    def _get_recovery_strategy(
        self, error: SettingsError
    ) -> Optional[RecoveryStrategy]:
        """Get recovery strategy for an error"""
        # Try specific error type first
        strategy = self.recovery_strategies.get(error.error_type.lower())
        if strategy:
            return strategy

        # Try operation-based strategy
        strategy = self.recovery_strategies.get(error.operation)
        if strategy:
            return strategy

        # Default strategy based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy(action=RecoveryAction.USE_BACKUP)
        elif error.severity == ErrorSeverity.HIGH:
            return RecoveryStrategy(action=RecoveryAction.RETRY, max_retries=2)
        else:
            return RecoveryStrategy(action=RecoveryAction.USE_DEFAULT)

    def _retry_operation(
        self, error: SettingsError, strategy: RecoveryStrategy
    ) -> Optional[Any]:
        """Retry the failed operation"""
        operation_func = error.context.get("operation_func")
        if not operation_func:
            return None

        for attempt in range(strategy.max_retries):
            try:
                time.sleep(strategy.retry_delay * (attempt + 1))
                result = operation_func()
                self.logger.info(
                    f"Retry successful for {error.error_id} on attempt {attempt + 1}"
                )
                return result
            except Exception as e:
                self.logger.warning(
                    f"Retry {attempt + 1} failed for {error.error_id}: {e}"
                )

        return None

    def _use_default_value(
        self, error: SettingsError, strategy: RecoveryStrategy
    ) -> Any:
        """Use default value for recovery"""
        default_value = strategy.fallback_value or error.context.get("default_value")
        self.logger.info(f"Using default value for recovery: {error.error_id}")
        return default_value

    def _restore_from_backup(
        self, error: SettingsError, strategy: RecoveryStrategy
    ) -> Optional[Any]:
        """Restore from backup for recovery"""
        file_path = error.context.get("file_path")
        if not file_path:
            return None

        success = self.backup_manager.restore_backup(file_path)
        if success:
            self.logger.info(f"Restored from backup for recovery: {error.error_id}")
            # Try to reload the data
            try:
                result = JsonUtils.load_json_file(file_path)
                return result.data if result.success else None
            except Exception:
                return None

        return None

    def _request_user_input(
        self, error: SettingsError, strategy: RecoveryStrategy
    ) -> Optional[Any]:
        """Request user input for recovery"""
        # This would show a dialog to the user
        # For now, return None (skip)
        self.logger.info(f"User input required for recovery: {error.error_id}")
        return None

    def register_recovery_strategy(self, error_type: str, strategy: RecoveryStrategy) -> None:
        """Register a custom recovery strategy"""
        self.recovery_strategies[error_type] = strategy
        self.logger.debug(f"Registered recovery strategy for: {error_type}")

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            **self.error_stats,
            "recovery_rate": (
                self.error_stats["recovered_errors"]
                / max(1, self.error_stats["total_errors"])
            )
            * 100,
            "active_errors": len(
                [e for e in self.errors.values() if not e.recovery_successful]
            ),
        }

    def clear_resolved_errors(self) -> None:
        """Clear resolved errors from memory"""
        resolved_errors = [
            eid for eid, error in self.errors.items() if error.recovery_successful
        ]

        for error_id in resolved_errors:
            del self.errors[error_id]

        self.logger.info(f"Cleared {len(resolved_errors)} resolved errors")


def settings_error_handler(
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for automatic error handling in settings operations"""

    def decorator(func: Any) -> Any:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = SettingsErrorHandler()
                recovery_context = context or {}
                recovery_context["operation_func"] = lambda: func(*args, **kwargs)

                return handler.handle_error(operation, e, recovery_context, severity)

        return wrapper

    return decorator


# Global error handler instance
_error_handler: Optional[SettingsErrorHandler] = None


def get_error_handler() -> SettingsErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = SettingsErrorHandler()
    return _error_handler
