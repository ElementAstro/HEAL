"""
Startup Error Handler
Enhanced error detection and reporting system for startup failures
"""

import time
import traceback
import sys
import psutil
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
from pathlib import Path

from .logging_config import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = 1          # 不影响核心功能
    MEDIUM = 2       # 影响部分功能
    HIGH = 3         # 影响主要功能
    CRITICAL = 4     # 阻止启动


class ErrorCategory(Enum):
    """错误类别"""
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    DEPENDENCY = "dependency"
    PERMISSION = "permission"
    NETWORK = "network"
    MEMORY = "memory"
    DISK = "disk"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class StartupError:
    """启动错误信息"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: str = ""
    exception: Optional[Exception] = None
    timestamp: float = field(default_factory=time.time)
    component: str = ""
    recovery_suggestions: List[str] = field(default_factory=list)
    system_info: Dict[str, Any] = field(default_factory=dict)
    
    # Recovery state
    is_recoverable: bool = True
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_error: Optional[str] = None


class StartupErrorDetector:
    """启动错误检测器"""
    
    def __init__(self):
        self.logger = logger.bind(component="StartupErrorDetector")
        self.detected_errors: List[StartupError] = []
        self.error_patterns: Dict[str, Callable[[Exception], Optional[StartupError]]] = {}
        self.system_checks: List[Callable[[], Optional[StartupError]]] = []
        
        # Error statistics
        self.error_stats = {
            "total_errors": 0,
            "critical_errors": 0,
            "recoverable_errors": 0,
            "recovery_attempts": 0,
            "successful_recoveries": 0
        }
        
        self._register_default_patterns()
        self._register_system_checks()
    
    def _register_default_patterns(self) -> None:
        """注册默认错误模式"""
        self.error_patterns.update({
            "FileNotFoundError": self._handle_file_not_found,
            "PermissionError": self._handle_permission_error,
            "ImportError": self._handle_import_error,
            "ModuleNotFoundError": self._handle_module_not_found,
            "ConnectionError": self._handle_connection_error,
            "MemoryError": self._handle_memory_error,
            "OSError": self._handle_os_error,
            "ValueError": self._handle_value_error,
            "TypeError": self._handle_type_error,
            "AttributeError": self._handle_attribute_error
        })
    
    def _register_system_checks(self) -> None:
        """注册系统检查"""
        self.system_checks.extend([
            self._check_memory_availability,
            self._check_disk_space,
            self._check_permissions,
            self._check_dependencies,
            self._check_configuration_files
        ])
    
    def detect_error(self, exception: Exception, component: str = "") -> Optional[StartupError]:
        """检测并分析错误"""
        error_type = type(exception).__name__
        
        # Try specific pattern handlers
        if error_type in self.error_patterns:
            error = self.error_patterns[error_type](exception)
            if error:
                error.component = component
                error.exception = exception
                self._collect_system_info(error)
                self.detected_errors.append(error)
                self.error_stats["total_errors"] += 1
                
                if error.severity == ErrorSeverity.CRITICAL:
                    self.error_stats["critical_errors"] += 1
                if error.is_recoverable:
                    self.error_stats["recoverable_errors"] += 1
                
                self.logger.error(f"Detected startup error: {error.error_id} - {error.message}")
                return error
        
        # Fallback to generic error handling
        return self._handle_generic_error(exception, component)
    
    def run_system_checks(self) -> List[StartupError]:
        """运行系统检查"""
        detected_errors = []
        
        for check in self.system_checks:
            try:
                error = check()
                if error:
                    self._collect_system_info(error)
                    detected_errors.append(error)
                    self.detected_errors.append(error)
                    self.error_stats["total_errors"] += 1
                    
                    if error.severity == ErrorSeverity.CRITICAL:
                        self.error_stats["critical_errors"] += 1
                    if error.is_recoverable:
                        self.error_stats["recoverable_errors"] += 1
                    
                    self.logger.warning(f"System check failed: {error.error_id}")
            except Exception as e:
                self.logger.error(f"System check failed with exception: {e}")
        
        return detected_errors
    
    def _collect_system_info(self, error: StartupError) -> None:
        """收集系统信息"""
        try:
            error.system_info = {
                "python_version": sys.version,
                "platform": sys.platform,
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent if sys.platform != 'win32' else psutil.disk_usage('C:').percent,
                "cpu_count": psutil.cpu_count(),
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.warning(f"Failed to collect system info: {e}")
    
    # Error pattern handlers
    def _handle_file_not_found(self, exception: Exception) -> Optional[StartupError]:
        """处理文件未找到错误"""
        filename = str(exception).split("'")[1] if "'" in str(exception) else "unknown"
        
        return StartupError(
            error_id=f"file_not_found_{int(time.time())}",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH if "config" in filename.lower() else ErrorSeverity.MEDIUM,
            message=f"Required file not found: {filename}",
            details=str(exception),
            recovery_suggestions=[
                f"Check if file {filename} exists",
                "Verify file permissions",
                "Restore file from backup if available",
                "Reinstall application if file is part of installation"
            ]
        )
    
    def _handle_permission_error(self, exception: PermissionError) -> Optional[StartupError]:
        """处理权限错误"""
        return StartupError(
            error_id=f"permission_error_{int(time.time())}",
            category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.HIGH,
            message="Permission denied during startup",
            details=str(exception),
            recovery_suggestions=[
                "Run application as administrator",
                "Check file and directory permissions",
                "Verify user has necessary access rights",
                "Check antivirus software blocking access"
            ]
        )
    
    def _handle_import_error(self, exception: ImportError) -> Optional[StartupError]:
        """处理导入错误"""
        module_name = str(exception).split("'")[1] if "'" in str(exception) else "unknown"
        
        return StartupError(
            error_id=f"import_error_{int(time.time())}",
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.CRITICAL,
            message=f"Failed to import required module: {module_name}",
            details=str(exception),
            recovery_suggestions=[
                f"Install missing module: {module_name}",
                "Check Python environment and PATH",
                "Verify all dependencies are installed",
                "Reinstall application dependencies"
            ]
        )
    
    def _handle_module_not_found(self, exception: Exception) -> Optional[StartupError]:
        """处理模块未找到错误"""
        module_name = str(exception).split("'")[1] if "'" in str(exception) else "unknown"
        
        return StartupError(
            error_id=f"module_not_found_{int(time.time())}",
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.CRITICAL,
            message=f"Required module not found: {module_name}",
            details=str(exception),
            recovery_suggestions=[
                f"Install missing module: pip install {module_name}",
                "Check virtual environment activation",
                "Verify PYTHONPATH configuration",
                "Reinstall application with all dependencies"
            ]
        )
    
    def _handle_connection_error(self, exception: Exception) -> Optional[StartupError]:
        """处理连接错误"""
        return StartupError(
            error_id=f"connection_error_{int(time.time())}",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Network connection failed during startup",
            details=str(exception),
            recovery_suggestions=[
                "Check internet connection",
                "Verify firewall settings",
                "Check proxy configuration",
                "Try starting in offline mode"
            ]
        )
    
    def _handle_memory_error(self, exception: MemoryError) -> Optional[StartupError]:
        """处理内存错误"""
        return StartupError(
            error_id=f"memory_error_{int(time.time())}",
            category=ErrorCategory.MEMORY,
            severity=ErrorSeverity.CRITICAL,
            message="Insufficient memory for startup",
            details=str(exception),
            recovery_suggestions=[
                "Close other applications to free memory",
                "Restart computer to clear memory",
                "Increase virtual memory/swap space",
                "Upgrade system RAM if possible"
            ],
            is_recoverable=False
        )
    
    def _handle_os_error(self, exception: OSError) -> Optional[StartupError]:
        """处理操作系统错误"""
        return StartupError(
            error_id=f"os_error_{int(time.time())}",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            message="Operating system error during startup",
            details=str(exception),
            recovery_suggestions=[
                "Check system resources availability",
                "Verify file system integrity",
                "Check for system updates",
                "Restart system if necessary"
            ]
        )
    
    def _handle_value_error(self, exception: ValueError) -> Optional[StartupError]:
        """处理值错误"""
        return StartupError(
            error_id=f"value_error_{int(time.time())}",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.MEDIUM,
            message="Invalid configuration value",
            details=str(exception),
            recovery_suggestions=[
                "Check configuration file syntax",
                "Verify configuration values are valid",
                "Reset configuration to defaults",
                "Restore configuration from backup"
            ]
        )
    
    def _handle_type_error(self, exception: TypeError) -> Optional[StartupError]:
        """处理类型错误"""
        return StartupError(
            error_id=f"type_error_{int(time.time())}",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.MEDIUM,
            message="Type mismatch in configuration or code",
            details=str(exception),
            recovery_suggestions=[
                "Check configuration data types",
                "Verify API compatibility",
                "Update configuration format",
                "Check for version mismatches"
            ]
        )
    
    def _handle_attribute_error(self, exception: AttributeError) -> Optional[StartupError]:
        """处理属性错误"""
        return StartupError(
            error_id=f"attribute_error_{int(time.time())}",
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.MEDIUM,
            message="Missing attribute or method",
            details=str(exception),
            recovery_suggestions=[
                "Check library versions compatibility",
                "Update dependencies to compatible versions",
                "Verify API documentation",
                "Check for breaking changes in dependencies"
            ]
        )
    
    def _handle_generic_error(self, exception: Exception, component: str) -> StartupError:
        """处理通用错误"""
        return StartupError(
            error_id=f"generic_error_{int(time.time())}",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            message=f"Unexpected error in {component or 'startup'}",
            details=f"{type(exception).__name__}: {str(exception)}",
            component=component,
            exception=exception,
            recovery_suggestions=[
                "Check application logs for details",
                "Restart application",
                "Check system resources",
                "Contact support if problem persists"
            ]
        )
    
    # System checks
    def _check_memory_availability(self) -> Optional[StartupError]:
        """检查内存可用性"""
        try:
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return StartupError(
                    error_id=f"low_memory_{int(time.time())}",
                    category=ErrorCategory.MEMORY,
                    severity=ErrorSeverity.HIGH,
                    message=f"Low memory available: {memory.percent:.1f}% used",
                    details=f"Available: {memory.available / 1024 / 1024:.1f} MB",
                    recovery_suggestions=[
                        "Close unnecessary applications",
                        "Restart computer to free memory",
                        "Increase virtual memory"
                    ]
                )
        except Exception as e:
            self.logger.warning(f"Memory check failed: {e}")
        return None
    
    def _check_disk_space(self) -> Optional[StartupError]:
        """检查磁盘空间"""
        try:
            disk_path = 'C:' if sys.platform == 'win32' else '/'
            disk = psutil.disk_usage(disk_path)
            if disk.percent > 95:
                return StartupError(
                    error_id=f"low_disk_space_{int(time.time())}",
                    category=ErrorCategory.DISK,
                    severity=ErrorSeverity.HIGH,
                    message=f"Low disk space: {disk.percent:.1f}% used",
                    details=f"Free space: {disk.free / 1024 / 1024 / 1024:.1f} GB",
                    recovery_suggestions=[
                        "Free up disk space",
                        "Delete temporary files",
                        "Move files to external storage",
                        "Clean up system cache"
                    ]
                )
        except Exception as e:
            self.logger.warning(f"Disk space check failed: {e}")
        return None
    
    def _check_permissions(self) -> Optional[StartupError]:
        """检查权限"""
        try:
            # Check write permissions in application directory
            app_dir = Path.cwd()
            test_file = app_dir / "test_write_permission.tmp"
            
            try:
                test_file.write_text("test")
                test_file.unlink()
            except PermissionError:
                return StartupError(
                    error_id=f"permission_check_{int(time.time())}",
                    category=ErrorCategory.PERMISSION,
                    severity=ErrorSeverity.HIGH,
                    message="Insufficient write permissions in application directory",
                    details=f"Cannot write to {app_dir}",
                    recovery_suggestions=[
                        "Run as administrator",
                        "Change directory permissions",
                        "Move application to user directory"
                    ]
                )
        except Exception as e:
            self.logger.warning(f"Permission check failed: {e}")
        return None
    
    def _check_dependencies(self) -> Optional[StartupError]:
        """检查依赖项"""
        try:
            # Check critical imports
            critical_modules = ['PySide6', 'qfluentwidgets', 'psutil']
            missing_modules = []
            
            for module in critical_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_modules.append(module)
            
            if missing_modules:
                return StartupError(
                    error_id=f"missing_dependencies_{int(time.time())}",
                    category=ErrorCategory.DEPENDENCY,
                    severity=ErrorSeverity.CRITICAL,
                    message=f"Missing critical dependencies: {', '.join(missing_modules)}",
                    details=f"Required modules not found: {missing_modules}",
                    recovery_suggestions=[
                        f"Install missing modules: pip install {' '.join(missing_modules)}",
                        "Check virtual environment",
                        "Reinstall application dependencies"
                    ]
                )
        except Exception as e:
            self.logger.warning(f"Dependency check failed: {e}")
        return None
    
    def _check_configuration_files(self) -> Optional[StartupError]:
        """检查配置文件"""
        try:
            config_dir = Path("config")
            if not config_dir.exists():
                return StartupError(
                    error_id=f"missing_config_dir_{int(time.time())}",
                    category=ErrorCategory.CONFIGURATION,
                    severity=ErrorSeverity.HIGH,
                    message="Configuration directory not found",
                    details=f"Directory {config_dir} does not exist",
                    recovery_suggestions=[
                        "Create configuration directory",
                        "Restore from backup",
                        "Reinstall application"
                    ]
                )
        except Exception as e:
            self.logger.warning(f"Configuration check failed: {e}")
        return None
    
    def get_error_report(self) -> Dict[str, Any]:
        """获取错误报告"""
        return {
            "total_errors": len(self.detected_errors),
            "error_stats": self.error_stats,
            "errors_by_category": self._group_errors_by_category(),
            "errors_by_severity": self._group_errors_by_severity(),
            "recent_errors": [
                {
                    "error_id": error.error_id,
                    "category": error.category.value,
                    "severity": error.severity.name,
                    "message": error.message,
                    "component": error.component,
                    "timestamp": error.timestamp,
                    "is_recoverable": error.is_recoverable,
                    "recovery_attempted": error.recovery_attempted
                }
                for error in self.detected_errors[-10:]  # Last 10 errors
            ]
        }
    
    def _group_errors_by_category(self) -> Dict[str, int]:
        """按类别分组错误"""
        categories = {}
        for error in self.detected_errors:
            category = error.category.value
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _group_errors_by_severity(self) -> Dict[str, int]:
        """按严重程度分组错误"""
        severities = {}
        for error in self.detected_errors:
            severity = error.severity.name
            severities[severity] = severities.get(severity, 0) + 1
        return severities
    
    def clear_errors(self) -> None:
        """清除错误记录"""
        self.detected_errors.clear()
        self.error_stats = {
            "total_errors": 0,
            "critical_errors": 0,
            "recoverable_errors": 0,
            "recovery_attempts": 0,
            "successful_recoveries": 0
        }


# Global startup error detector
startup_error_detector = StartupErrorDetector()


# Convenience functions
def detect_startup_error(exception: Exception, component: str = "") -> Optional[StartupError]:
    """检测启动错误"""
    return startup_error_detector.detect_error(exception, component)


def run_startup_system_checks() -> List[StartupError]:
    """运行启动系统检查"""
    return startup_error_detector.run_system_checks()


def get_startup_error_report() -> Dict[str, Any]:
    """获取启动错误报告"""
    return startup_error_detector.get_error_report()
