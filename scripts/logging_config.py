#!/usr/bin/env python3
"""
Comprehensive logging configuration for HEAL build system.
Provides structured logging with multiple handlers and formatters.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        # Add color to levelname
        if hasattr(record, 'levelname') and record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )

        return super().format(record)


class BuildLogger:
    """Centralized logging configuration for build processes."""

    def __init__(self, name: str = "heal-build", log_dir: Optional[Path] = None):
        self.name = name
        self.log_dir = log_dir or Path.cwd() / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self._base_logger = self.logger

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up logging handlers."""

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        console_formatter = ColoredFormatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        # File handler for all logs
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)

        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # Error file handler
        error_file = self.log_dir / f"{self.name}-errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file, maxBytes=5*1024*1024, backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)

        # JSON handler for structured logging
        json_file = self.log_dir / f"{self.name}.json"
        json_handler = logging.handlers.RotatingFileHandler(
            json_file, maxBytes=10*1024*1024, backupCount=3
        )
        json_handler.setLevel(logging.INFO)

        json_formatter = JsonFormatter()
        json_handler.setFormatter(json_formatter)

        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(json_handler)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger."""
        return self.logger

    def set_level(self, level: str) -> None:
        """Set logging level."""
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {level}')

        self.logger.setLevel(numeric_level)

        # Update console handler level
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                handler.setLevel(numeric_level)

    def add_context(self, **kwargs: Any) -> None:
        """Add context to all log messages."""
        for key, value in kwargs.items():
            # Create a new LoggerAdapter but keep the base logger for handler operations
            adapter = logging.LoggerAdapter(self._base_logger, {key: value})
            # Store context for future use
            setattr(self, f'_context_{key}', value)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                           'filename', 'module', 'lineno', 'funcName', 'created',
                           'msecs', 'relativeCreated', 'thread', 'threadName',
                           'processName', 'process', 'getMessage', 'exc_info',
                           'exc_text', 'stack_info']:
                log_entry[key] = value

        return json.dumps(log_entry)


class ContextManager:
    """Context manager for logging operations."""

    def __init__(self, logger: logging.Logger, operation: str, **context: Any):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time: Optional[datetime] = None

    def __enter__(self) -> 'ContextManager':
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.operation}", extra=self.context)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.start_time is not None:
            duration = datetime.now() - self.start_time
        else:
            duration = datetime.now() - datetime.now()  # Zero duration fallback

        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation} in {duration.total_seconds():.2f}s",
                extra={**self.context, 'duration': duration.total_seconds()}
            )
        else:
            self.logger.error(
                f"Failed {self.operation} after {duration.total_seconds():.2f}s: {exc_val}",
                extra={**self.context, 'duration': duration.total_seconds()},
                exc_info=True
            )

        # Don't suppress exceptions


def setup_logging(
    name: str = "heal-build",
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    enable_debug: bool = False
) -> logging.Logger:
    """Set up logging for build processes."""

    # Enable debug mode if requested
    if enable_debug or os.getenv('DEBUG', '').lower() in ('1', 'true', 'yes'):
        level = "DEBUG"

    # Create build logger
    build_logger = BuildLogger(name, log_dir)
    build_logger.set_level(level)

    logger = build_logger.get_logger()

    # Log startup information
    logger.info(f"Logging initialized for {name}")
    logger.debug(f"Log directory: {build_logger.log_dir}")
    logger.debug(f"Log level: {level}")

    return logger


def log_system_info(logger: logging.Logger) -> None:
    """Log system information for debugging."""
    import platform
    import sys

    logger.info("System Information", extra={
        'python_version': sys.version,
        'platform': platform.platform(),
        'architecture': platform.architecture(),
        'processor': platform.processor(),
        'python_executable': sys.executable,
    })


def log_environment_info(logger: logging.Logger) -> None:
    """Log relevant environment variables."""
    env_vars = [
        'PATH', 'PYTHONPATH', 'HOME', 'USER', 'SHELL',
        'CI', 'GITHUB_ACTIONS', 'GITHUB_WORKFLOW',
        'DEBUG', 'VERBOSE'
    ]

    env_info = {}
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Truncate long values
            if len(value) > 100:
                value = value[:97] + "..."
            env_info[var] = value

    if env_info:
        logger.debug("Environment Variables", extra=env_info)


class ErrorHandler:
    """Enhanced error handling with logging."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def handle_subprocess_error(self, e: Exception, command: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle subprocess errors with detailed logging."""
        context = context or {}

        error_info = {
            'command': command,
            'error_type': type(e).__name__,
            'return_code': getattr(e, 'returncode', None),
            **context
        }

        if hasattr(e, 'stdout') and e.stdout:
            error_info['stdout'] = e.stdout[:1000]  # Limit output

        if hasattr(e, 'stderr') and e.stderr:
            error_info['stderr'] = e.stderr[:1000]  # Limit output

        self.logger.error(
            f"Command failed: {command}", extra=error_info, exc_info=True)

    def handle_file_error(self, e: Exception, file_path: str, operation: str) -> None:
        """Handle file operation errors."""
        error_info = {
            'file_path': file_path,
            'operation': operation,
            'error_type': type(e).__name__,
        }

        self.logger.error(
            f"File {operation} failed: {file_path}", extra=error_info, exc_info=True)

    def handle_build_error(self, e: Exception, stage: str, platform: Optional[str] = None) -> None:
        """Handle build process errors."""
        error_info = {
            'stage': stage,
            'error_type': type(e).__name__,
        }

        if platform:
            error_info['platform'] = platform

        self.logger.error(
            f"Build failed at {stage}", extra=error_info, exc_info=True)


# Convenience functions
def get_logger(name: str = "heal-build") -> logging.Logger:
    """Get or create a logger with default configuration."""
    return setup_logging(name)


def log_operation(logger: logging.Logger, operation: str, **context: Any) -> ContextManager:
    """Context manager for logging operations."""
    return ContextManager(logger, operation, **context)


# Example usage
if __name__ == "__main__":
    # Set up logging
    logger = setup_logging("test-logger", "DEBUG")

    # Log system info
    log_system_info(logger)
    log_environment_info(logger)

    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Test context manager
    with log_operation(logger, "test operation", component="test"):
        logger.info("Doing some work...")

    # Test error handling
    error_handler = ErrorHandler(logger)
    try:
        raise ValueError("Test error")
    except ValueError as e:
        error_handler.handle_build_error(e, "test_stage", "test_platform")
