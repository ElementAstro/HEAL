import hashlib
import platform
import sys
import traceback
from copy import deepcopy
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import psutil
from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget
from qfluentwidgets import InfoBar, InfoBarIcon, InfoBarPosition

from .i18n import tr
from .logging_config import get_logger, log_exception
from .setting import DEBUG

# 使用统一日志配置
app_logger = get_logger("exception_handler")

# 常量定义
CHECK_NETWORK_CONNECTION = "检查网络连接"


class ExceptionType:
    """异常类型枚举"""

    NETWORK_ERROR = "network_error"
    FILE_ERROR = "file_error"
    PROCESS_ERROR = "process_error"
    DOWNLOAD_ERROR = "download_error"
    CONFIG_ERROR = "config_error"
    PERMISSION_ERROR = "permission_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


class ExceptionSeverity:
    """异常严重级别"""

    LOW = "low"  # 轻微错误，不影响主要功能
    MEDIUM = "medium"  # 中等错误，影响部分功能
    HIGH = "high"  # 严重错误，影响核心功能
    CRITICAL = "critical"  # 致命错误，应用无法继续运行


class ExceptionInfo:
    """异常信息封装"""

    def __init__(
        self,
        exception: Exception,
        exc_type: str = ExceptionType.UNKNOWN_ERROR,
        severity: str = ExceptionSeverity.MEDIUM,
        user_message: Optional[str] = None,
        technical_details: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None,
        auto_retry: bool = False,
        retry_count: int = 0,
        max_retries: int = 3,
    ) -> None:
        self.exception = exception
        self.exc_type = exc_type
        self.severity = severity
        self.user_message = user_message or self._generate_user_message()
        self.technical_details = technical_details or str(exception)
        self.recovery_suggestions = recovery_suggestions or []
        self.auto_retry = auto_retry
        self.retry_count = retry_count
        self.max_retries = max_retries

        # 系统信息收集
        self.timestamp = datetime.now()
        self.system_info = self._collect_system_info()
        self.error_hash = self._generate_error_hash()

    def _generate_user_message(self) -> str:
        """生成用户友好的错误消息"""
        error_messages = {
            ExceptionType.NETWORK_ERROR: tr(
                "network_error", "网络连接出现问题，请检查网络设置"
            ),
            ExceptionType.FILE_ERROR: tr(
                "file_error", "文件操作失败，请检查文件权限和磁盘空间"
            ),
            ExceptionType.PROCESS_ERROR: tr(
                "process_error", "进程启动或管理失败，请检查系统资源"
            ),
            ExceptionType.DOWNLOAD_ERROR: tr(
                "download_error", "下载失败，请检查网络连接和存储空间"
            ),
            ExceptionType.CONFIG_ERROR: tr(
                "config_error", "配置文件错误，请检查配置设置"
            ),
            ExceptionType.PERMISSION_ERROR: tr(
                "permission_error", "权限不足，请以管理员身份运行"
            ),
            ExceptionType.VALIDATION_ERROR: tr(
                "validation_error", "输入数据无效，请检查输入内容"
            ),
            ExceptionType.UNKNOWN_ERROR: tr(
                "unknown_error", "发生未知错误，请查看详细信息"
            ),
        }
        return error_messages.get(self.exc_type, tr("unknown_error", "发生未知错误"))

    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息用于诊断"""
        try:
            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": {
                    path: {"total": usage.total, "used": usage.used, "free": usage.free}
                    for path, usage in [
                        (p.mountpoint, psutil.disk_usage(p.mountpoint))
                        for p in psutil.disk_partitions()
                        if p.fstype
                    ][:3]
                },
                "cpu_count": psutil.cpu_count(),
                "boot_time": psutil.boot_time(),
            }
        except Exception as e:
            app_logger.warning(f"无法收集系统信息: {e}")
            return {"error": str(e)}

    def _generate_error_hash(self) -> str:
        """生成错误哈希用于去重"""
        error_signature = f"{type(self.exception).__name__}:{str(self.exception)}"
        return hashlib.md5(
            error_signature.encode()
        ).hexdigest()  # Use full MD5 hash for better uniqueness

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "error_hash": self.error_hash,
            "exception_type": type(self.exception).__name__,
            "exc_type": self.exc_type,
            "severity": self.severity,
            "user_message": self.user_message,
            "technical_details": self.technical_details,
            "recovery_suggestions": self.recovery_suggestions,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "system_info": self.system_info,
            "traceback": traceback.format_exception(
                type(self.exception), self.exception, self.exception.__traceback__
            ),
        }


class ExceptionHandler(QObject):
    """全局异常处理器"""

    exception_occurred = Signal(object)  # ExceptionInfo
    critical_error = Signal(str)
    recovery_attempted = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.error_history: list[Any] = []
        self.error_counts: dict[str, Any] = {}
        self.recovery_callbacks: dict[str, Any] = {}
        self.auto_retry_timer = QTimer()
        self.auto_retry_timer.timeout.connect(self._process_auto_retry)
        self.pending_retries: list[Any] = []

        # 注意：全局异常处理器将在外部设置，避免重复设置
        # sys.excepthook = self.handle_exception

    def register_recovery_callback(self, exc_type: str, callback: Callable) -> None:
        """注册异常恢复回调函数"""
        self.recovery_callbacks[exc_type] = callback

    def handle_exception(self, exc_type: type, exc_value: Exception, exc_traceback: Any) -> None:
        """处理未捕获的异常"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # 创建异常信息
        exception_info = self._analyze_exception(exc_value, exc_traceback)

        # 记录异常
        self._log_exception(exception_info)

        # 发送信号
        self.exception_occurred.emit(exception_info)

        # 尝试恢复
        if exception_info.severity == ExceptionSeverity.CRITICAL:
            self.critical_error.emit(exception_info.user_message)
        else:
            self._attempt_recovery(exception_info)

    def handle_known_exception(
        self,
        exception: Exception,
        exc_type: str = ExceptionType.UNKNOWN_ERROR,
        severity: str = ExceptionSeverity.MEDIUM,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None,
        auto_retry: bool = False,
        parent_widget: Optional[QWidget] = None,
    ) -> ExceptionInfo:
        """处理已知异常"""
        exception_info = ExceptionInfo(
            exception=exception,
            exc_type=exc_type,
            severity=severity,
            user_message=user_message,
            recovery_suggestions=recovery_suggestions,
            auto_retry=auto_retry,
        )

        self._log_exception(exception_info)
        self._show_user_notification(exception_info, parent_widget)

        if auto_retry and exception_info.retry_count < exception_info.max_retries:
            self._schedule_retry(exception_info)
        else:
            self._attempt_recovery(exception_info)

        return exception_info

    def _analyze_exception(
        self, exception: Exception, traceback_obj: Any = None
    ) -> ExceptionInfo:
        """分析异常并确定类型和严重性"""
        exc_str = str(exception).lower()

        # 根据异常类型和消息确定分类
        if any(
            keyword in exc_str
            for keyword in ["network", "connection", "timeout", "dns"]
        ):
            exc_type = ExceptionType.NETWORK_ERROR
            severity = ExceptionSeverity.MEDIUM
            recovery_suggestions = [
                CHECK_NETWORK_CONNECTION,
                "尝试重新连接",
                "检查防火墙设置",
                "使用代理或镜像源",
            ]
        elif any(
            keyword in exc_str
            for keyword in ["file", "directory", "path", "permission denied"]
        ):
            exc_type = ExceptionType.FILE_ERROR
            severity = ExceptionSeverity.MEDIUM
            recovery_suggestions = [
                "检查文件路径是否正确",
                "确认文件权限",
                "检查磁盘空间",
                "以管理员身份运行",
            ]
        elif any(
            keyword in exc_str for keyword in ["process", "subprocess", "command"]
        ):
            exc_type = ExceptionType.PROCESS_ERROR
            severity = ExceptionSeverity.HIGH
            recovery_suggestions = [
                "检查进程是否正在运行",
                "重启相关服务",
                "检查系统资源",
                "更新系统组件",
            ]
        elif any(keyword in exc_str for keyword in ["download", "upload", "transfer"]):
            exc_type = ExceptionType.DOWNLOAD_ERROR
            severity = ExceptionSeverity.MEDIUM
            recovery_suggestions = [
                CHECK_NETWORK_CONNECTION,
                "重试下载",
                "更换下载源",
                "清理临时文件",
            ]
        elif any(
            keyword in exc_str for keyword in ["config", "configuration", "setting"]
        ):
            exc_type = ExceptionType.CONFIG_ERROR
            severity = ExceptionSeverity.MEDIUM
            recovery_suggestions = [
                "检查配置文件格式",
                "恢复默认配置",
                "重新生成配置",
                "验证配置项",
            ]
        elif "permission" in exc_str or "access" in exc_str:
            exc_type = ExceptionType.PERMISSION_ERROR
            severity = ExceptionSeverity.HIGH
            recovery_suggestions = [
                "以管理员身份运行",
                "检查文件权限",
                "修改安全设置",
                "联系系统管理员",
            ]
        else:
            exc_type = ExceptionType.UNKNOWN_ERROR
            severity = ExceptionSeverity.MEDIUM
            recovery_suggestions = [
                "重启应用程序",
                "检查系统日志",
                "更新软件版本",
                "联系技术支持",
            ]

        return ExceptionInfo(
            exception=exception,
            exc_type=exc_type,
            severity=severity,
            recovery_suggestions=recovery_suggestions,
            auto_retry=exc_type
            in [ExceptionType.NETWORK_ERROR, ExceptionType.DOWNLOAD_ERROR],
        )

    def _log_exception(self, exception_info: ExceptionInfo) -> None:
        """记录异常信息"""
        # 使用统一异常日志记录
        log_exception(
            exception_info.exception,
            f"Exception occurred: {exception_info.exc_type} | "
            f"Severity: {exception_info.severity} | "
            f"Message: {exception_info.user_message} | "
            f"Details: {exception_info.technical_details}",
            severity=exception_info.severity,
            exc_type=exception_info.exc_type,
        )

        app_logger.error(
            f"Exception occurred: {exception_info.exc_type} | "
            f"Severity: {exception_info.severity} | "
            f"Message: {exception_info.user_message} | "
            f"Details: {exception_info.technical_details}",
            exception=exception_info.exception,
        )

        # 添加到历史记录
        self.error_history.append(exception_info)

        # 统计错误次数
        self.error_counts[exception_info.exc_type] = (
            self.error_counts.get(exception_info.exc_type, 0) + 1
        )

        # 限制历史记录大小
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]

    def _show_user_notification(
        self, exception_info: ExceptionInfo, parent_widget: Optional[QWidget] = None
    ) -> None:
        """显示用户通知"""
        if not parent_widget:
            parent_widget = QApplication.activeWindow()

        if not parent_widget:
            # 如果没有活动窗口，使用消息框
            self._show_message_box(exception_info)
            return

        # 根据严重性选择图标和持续时间
        icon_map = {
            ExceptionSeverity.LOW: InfoBarIcon.INFORMATION,
            ExceptionSeverity.MEDIUM: InfoBarIcon.WARNING,
            ExceptionSeverity.HIGH: InfoBarIcon.ERROR,
            ExceptionSeverity.CRITICAL: InfoBarIcon.ERROR,
        }

        duration_map = {
            ExceptionSeverity.LOW: 3000,
            ExceptionSeverity.MEDIUM: 5000,
            ExceptionSeverity.HIGH: 8000,
            ExceptionSeverity.CRITICAL: -1,  # 不自动关闭
        }

        info_bar = InfoBar(
            icon=icon_map.get(exception_info.severity, InfoBarIcon.ERROR),
            title=exception_info.user_message,
            content=(
                exception_info.technical_details[:100] + "..."
                if len(exception_info.technical_details) > 100
                else exception_info.technical_details
            ),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=duration_map.get(exception_info.severity, 5000),
            parent=parent_widget,
        )

        # 添加恢复建议按钮
        if exception_info.recovery_suggestions:
            from qfluentwidgets import PushButton

            recovery_button = PushButton("查看解决方案")
            recovery_button.clicked.connect(
                lambda: self._show_recovery_dialog(exception_info, parent_widget)
            )
            info_bar.addWidget(recovery_button)

        info_bar.show()

    def _show_message_box(self, exception_info: ExceptionInfo) -> None:
        """显示消息框"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle("错误")
        msg_box.setText(exception_info.user_message)
        msg_box.setDetailedText(exception_info.technical_details)

        if exception_info.severity == ExceptionSeverity.CRITICAL:
            msg_box.setIcon(QMessageBox.Icon.Critical)
        elif exception_info.severity == ExceptionSeverity.HIGH:
            msg_box.setIcon(QMessageBox.Icon.Warning)
        else:
            msg_box.setIcon(QMessageBox.Icon.Information)

        msg_box.exec()

    def _show_recovery_dialog(
        self, exception_info: ExceptionInfo, parent_widget: QWidget
    ) -> None:
        """显示恢复建议对话框"""
        from qfluentwidgets import MessageBox

        suggestions_text = "\n".join(
            [f"• {suggestion}" for suggestion in exception_info.recovery_suggestions]
        )

        msg_box = MessageBox(
            title="错误恢复建议",
            content=f"错误类型：{exception_info.exc_type}\n\n建议解决方案：\n{suggestions_text}",
            parent=parent_widget,
        )

        if (
            exception_info.auto_retry
            and exception_info.retry_count < exception_info.max_retries
        ):
            msg_box.yesButton.setText("自动重试")
            msg_box.cancelButton.setText("手动处理")

            if msg_box.exec():
                self._schedule_retry(exception_info)
        else:
            msg_box.exec()

    def _attempt_recovery(self, exception_info: ExceptionInfo) -> None:
        """尝试异常恢复"""
        recovery_callback = self.recovery_callbacks.get(exception_info.exc_type)
        if recovery_callback:
            try:
                recovery_callback(exception_info)
                self.recovery_attempted.emit(f"尝试恢复: {exception_info.exc_type}")
                app_logger.info(f"Recovery attempted for {exception_info.exc_type}")
            except Exception as e:
                app_logger.error(f"Recovery failed for {exception_info.exc_type}: {e}")

    def _schedule_retry(self, exception_info: ExceptionInfo) -> None:
        """安排自动重试"""
        exception_info.retry_count += 1
        self.pending_retries.append(exception_info)

        if not self.auto_retry_timer.isActive():
            self.auto_retry_timer.start(2000)  # 2秒后重试

    def _process_auto_retry(self) -> None:
        """处理自动重试"""
        if not self.pending_retries:
            self.auto_retry_timer.stop()
            return

        exception_info = self.pending_retries.pop(0)

        app_logger.info(
            f"Auto retry attempt {exception_info.retry_count} for {exception_info.exc_type}"
        )

        # 尝试重新执行失败的操作
        self._attempt_recovery(exception_info)

        if not self.pending_retries:
            self.auto_retry_timer.stop()

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return {
            "total_errors": len(self.error_history),
            "error_counts": self.error_counts.copy(),
            "recent_errors": self.error_history[-10:] if self.error_history else [],
            "most_common_error": (
                max(self.error_counts.items(), key=lambda x: x[1])
                if self.error_counts
                else None
            ),
        }

    def clear_error_history(self) -> None:
        """清除错误历史"""
        self.error_history.clear()
        self.error_counts.clear()
        app_logger.info("Error history cleared")


# 全局异常处理器实例
global_exception_handler = ExceptionHandler()


def exception_handler(
    exc_type: str = ExceptionType.UNKNOWN_ERROR,
    severity: str = ExceptionSeverity.MEDIUM,
    user_message: Optional[str] = None,
    recovery_suggestions: Optional[List[str]] = None,
    auto_retry: bool = False,
    return_value: Any = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """异常处理装饰器"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 获取父组件
                parent_widget = None
                if args and hasattr(args[0], "parent"):
                    parent_widget = getattr(args[0], "parent", None)
                elif args and isinstance(args[0], QWidget):
                    parent_widget = args[0]

                global_exception_handler.handle_known_exception(
                    exception=e,
                    exc_type=exc_type,
                    severity=severity,
                    user_message=user_message,
                    recovery_suggestions=recovery_suggestions,
                    auto_retry=auto_retry,
                    parent_widget=parent_widget,
                )
                return return_value

        return wrapper

    return decorator


def safe_execute(func: Callable[..., Any], *args: Any, default_return: Any = None, **kwargs: Any) -> Any:
    """安全执行函数，捕获并处理异常"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        global_exception_handler.handle_known_exception(
            exception=e,
            exc_type=ExceptionType.UNKNOWN_ERROR,
            severity=ExceptionSeverity.MEDIUM,
        )
        return default_return


# 常用异常处理装饰器
def network_exception_handler(func: Any) -> None:
    return exception_handler(
        exc_type=ExceptionType.NETWORK_ERROR,
        severity=ExceptionSeverity.MEDIUM,
        user_message="网络操作失败",
        recovery_suggestions=[CHECK_NETWORK_CONNECTION, "重试操作", "使用代理"],
        auto_retry=True,
    )(func)


def file_exception_handler(func: Any) -> None:
    return exception_handler(
        exc_type=ExceptionType.FILE_ERROR,
        severity=ExceptionSeverity.MEDIUM,
        user_message="文件操作失败",
        recovery_suggestions=["检查文件权限", "确认路径正确", "检查磁盘空间"],
    )(func)


def process_exception_handler(func: Any) -> None:
    return exception_handler(
        exc_type=ExceptionType.PROCESS_ERROR,
        severity=ExceptionSeverity.HIGH,
        user_message="进程操作失败",
        recovery_suggestions=["检查进程状态", "重启服务", "检查系统资源"],
    )(func)


def download_exception_handler(func: Any) -> None:
    return exception_handler(
        exc_type=ExceptionType.DOWNLOAD_ERROR,
        severity=ExceptionSeverity.MEDIUM,
        user_message="下载失败",
        recovery_suggestions=[CHECK_NETWORK_CONNECTION, "重试下载", "更换下载源"],
        auto_retry=True,
    )(func)


# 兼容旧版异常处理器
def exception_handler_legacy(log: str, *default: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """decorator for exception handling (legacy compatibility)

    Parameters
    ----------
    log: str
        log file name without `.log` suffix

    *default:
        the default value returned when an exception occurs
    """

    def outer(func: Callable[..., Any]) -> Callable[..., Any]:
        def inner(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if DEBUG:
                    app_logger.error(
                        f"{e.__class__.__name__}: {traceback.format_exc()}"
                    )

                value = deepcopy(default)
                if len(value) == 0:
                    return None
                elif len(value) == 1:
                    return value[0]

                return value

        return inner

    return outer


def exception_traceback_handler_legacy(log: str, *default: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """decorator for exception handling (legacy compatibility)

    Parameters
    ----------
    log: str
        log file name without `.log` suffix

    *default:
        the default value returned when an exception occurs
    """

    def outer(func: Callable[..., Any]) -> Callable[..., Any]:
        def inner(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                app_logger.error(f"{e.__class__.__name__}: {traceback.format_exc()}")

                value = deepcopy(default)
                if len(value) == 0:
                    return None
                elif len(value) == 1:
                    return value[0]

                return value

        return inner

    return outer
