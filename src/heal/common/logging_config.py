import asyncio
import json
import os
import sys
import threading
import time
import uuid
from collections import defaultdict
from contextvars import ContextVar
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

# Type variable for preserving function signatures in decorators
F = TypeVar('F', bound=Callable[..., Any])

from loguru import logger

# 上下文变量用于log correlation
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
user_session: ContextVar[str] = ContextVar("user_session", default="")


class LogLevel(Enum):
    """日志级别枚举"""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogMetrics:
    """日志统计信息"""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.stats: defaultdict[str, int] = defaultdict(int)
        self.errors_by_module: defaultdict[str, int] = defaultdict(int)
        self.performance_data: defaultdict[str, list[Any]] = defaultdict(list)
        self.start_time = datetime.now()

    def record_log(self, level: str, module: str = "unknown") -> None:
        with self.lock:
            self.stats[f"level_{level.lower()}"] += 1
            self.stats[f"module_{module}"] += 1
            if level in ["ERROR", "CRITICAL"]:
                self.errors_by_module[module] += 1

    def record_performance(self, operation: str, duration: float) -> None:
        with self.lock:
            self.performance_data[operation].append(
                {"duration": duration, "timestamp": datetime.now()}
            )
            # 保留最近1000条记录
            if len(self.performance_data[operation]) > 1000:
                self.performance_data[operation] = self.performance_data[operation][
                    -1000:
                ]

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            uptime = datetime.now() - self.start_time
            return {
                "uptime_seconds": uptime.total_seconds(),
                "log_counts": dict(self.stats),
                "error_by_module": dict(self.errors_by_module),
                "performance_summary": {
                    op: {
                        "count": len(data),
                        "avg_duration": (
                            sum(d["duration"] for d in data) / len(data) if data else 0
                        ),
                        "max_duration": max(d["duration"] for d in data) if data else 0,
                    }
                    for op, data in self.performance_data.items()
                },
            }


class LoggingConfig:
    """统一日志配置类 - 增强版"""

    def __init__(self) -> None:
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.handlers: List[int] = []
        self.metrics = LogMetrics()
        self.config_lock = threading.Lock()
        self.dynamic_levels: Dict[str, str] = {}
        self.filters: Dict[str, Callable] = {}
        self.alerting_callbacks: List[Callable] = []
        self._setup_logging()

    def _create_custom_format(self, include_correlation: bool = True) -> str:
        """创建自定义日志格式"""
        base_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line}"
        )

        if include_correlation:
            # 添加correlation ID和session信息
            correlation_format = (
                " | CID:{extra[correlation_id]} | SID:{extra[session_id]}"
            )
            base_format += correlation_format

        return base_format + " | {message}"

    def _correlation_filter(self, record: Any) -> None:
        """添加correlation信息到日志记录"""
        record["extra"]["correlation_id"] = (
            correlation_id.get("")[:8] if correlation_id.get() else "--------"
        )
        record["extra"]["session_id"] = (
            user_session.get("")[:8] if user_session.get() else "--------"
        )

    def _metrics_filter(self, record: Any) -> None:
        """记录日志统计信息"""
        module_name = record.get("name", "unknown")
        level = record["level"].name if hasattr(record["level"], "name") else "INFO"
        self.metrics.record_log(level, module_name)

    def _alerting_filter(self, record: Any) -> None:
        """触发告警回调"""
        level = record["level"].name if hasattr(record["level"], "name") else "INFO"
        if level in ["ERROR", "CRITICAL"] and self.alerting_callbacks:
            for callback in self.alerting_callbacks:
                try:
                    callback(record)
                except Exception:
                    pass  # 不让alerting影响主日志功能

    def _combined_filter(self, record: Any, extra_key: Optional[str] = None) -> bool:
        """组合过滤器"""
        # 添加基础信息
        self._correlation_filter(record)
        self._metrics_filter(record)
        self._alerting_filter(record)

        # 检查特定的extra键
        if extra_key:
            return extra_key in record["extra"]
        return True

    def _setup_logging(self) -> None:
        """设置日志配置 - 增强版"""
        # 移除默认处理器
        logger.remove()

        # 控制台输出处理器 - 增强格式
        console_handler = logger.add(
            sys.stderr,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<yellow>CID:{extra[correlation_id]}</yellow> | "
            "<level>{message}</level>",
            colorize=True,
            backtrace=True,
            diagnose=True,
            filter=lambda record: self._combined_filter(record),
        )
        self.handlers.append(console_handler)

        # 主应用日志文件 - 结构化格式
        main_handler = logger.add(
            self.log_dir / "application.log",
            rotation="10 MB",
            retention="30 days",
            level="DEBUG",
            format=self._create_custom_format(True),
            backtrace=True,
            diagnose=True,
            encoding="utf-8",
            enqueue=True,  # 异步写入
            filter=lambda record: self._combined_filter(record),
        )
        self.handlers.append(main_handler)

        # 错误专用日志文件 - 详细异常信息
        error_handler = logger.add(
            self.log_dir / "errors.log",
            rotation="5 MB",
            retention="60 days",
            level="ERROR",
            format=self._create_custom_format(True) + "\n{exception}",
            backtrace=True,
            diagnose=True,
            encoding="utf-8",
            enqueue=True,
            filter=lambda record: self._combined_filter(record),
        )
        self.handlers.append(error_handler)

        # 性能监控日志 - JSON格式便于分析
        performance_handler = logger.add(
            self.log_dir / "performance.log",
            rotation="5 MB",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
            filter=lambda record: self._combined_filter(record, "PERFORMANCE"),
            encoding="utf-8",
            serialize=True,  # JSON序列化
            enqueue=True,
        )
        self.handlers.append(performance_handler)

        # 下载进程专用日志
        download_handler = logger.add(
            self.log_dir / "downloads.log",
            rotation="5 MB",
            retention="14 days",
            level="DEBUG",
            format=self._create_custom_format(True),
            filter=lambda record: self._combined_filter(record, "DOWNLOAD"),
            encoding="utf-8",
            enqueue=True,
        )
        self.handlers.append(download_handler)

        # 网络请求日志
        network_handler = logger.add(
            self.log_dir / "network.log",
            rotation="5 MB",
            retention="7 days",
            level="DEBUG",
            format=self._create_custom_format(True),
            filter=lambda record: self._combined_filter(record, "NETWORK"),
            encoding="utf-8",
            enqueue=True,
        )
        self.handlers.append(network_handler)

        # 异常专用日志 - 包含完整堆栈和系统信息
        exception_handler = logger.add(
            self.log_dir / "exceptions.log",
            rotation="10 MB",
            retention="90 days",
            level="ERROR",
            format=self._create_custom_format(True)
            + "\n--- Stack Trace ---\n{exception}\n--- End Stack Trace ---",
            filter=lambda record: self._combined_filter(record, "EXCEPTION"),
            encoding="utf-8",
            enqueue=True,
        )
        self.handlers.append(exception_handler)

        logger.info("统一日志配置已初始化 - Enhanced Version")

    def add_module_logger(self, module_name: str, level: str = "DEBUG") -> int:
        """为特定模块添加专用日志处理器"""
        handler: int = logger.add(
            self.log_dir / f"{module_name}.log",
            rotation="2 MB",
            retention="14 days",
            level=level,
            format=self._create_custom_format(True),
            filter=lambda record: (
                record["extra"].get("module") == module_name
                and self._combined_filter(record)
            ),
            backtrace=True,
            diagnose=True,
            encoding="utf-8",
            enqueue=True,
        )
        self.handlers.append(handler)
        logger.bind(module=module_name).info(f"模块 {module_name} 日志处理器已添加")
        return handler

    def set_dynamic_level(self, module_name: str, level: str) -> None:
        """动态设置模块日志级别"""
        with self.config_lock:
            self.dynamic_levels[module_name] = level
            logger.info(f"模块 {module_name} 日志级别已设置为 {level}")

    def add_alerting_callback(self, callback: Callable) -> None:
        """添加告警回调函数"""
        self.alerting_callbacks.append(callback)
        logger.info("告警回调已添加")

    def get_metrics(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        return self.metrics.get_stats()

    def archive_old_logs(self, days_old: int = 30) -> None:
        """归档旧日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            archived_count = 0

            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    archive_dir = self.log_dir / "archive"
                    archive_dir.mkdir(exist_ok=True)
                    archive_path = (
                        archive_dir
                        / f"{cutoff_date.strftime('%Y%m%d')}_{log_file.name}"
                    )
                    log_file.rename(archive_path)
                    archived_count += 1

            logger.info(f"已归档 {archived_count} 个旧日志文件")
        except Exception as e:
            logger.error(f"归档日志文件失败: {e}")

    def cleanup_logs(self, max_size_mb: int = 100) -> None:
        """清理过大的日志目录"""
        try:
            total_size = sum(
                f.stat().st_size for f in self.log_dir.rglob("*") if f.is_file()
            )
            total_size_mb = total_size / (1024 * 1024)

            if total_size_mb > max_size_mb:
                # 删除最旧的文件直到满足大小限制
                files = [
                    (f, f.stat().st_mtime)
                    for f in self.log_dir.rglob("*")
                    if f.is_file()
                ]
                files.sort(key=lambda x: x[1])  # 按修改时间排序

                deleted_count = 0
                for file_path, _ in files:
                    if total_size_mb <= max_size_mb:
                        break
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    file_path.unlink()
                    total_size_mb -= file_size_mb
                    deleted_count += 1

                logger.info(f"已清理 {deleted_count} 个旧日志文件，释放空间")
        except Exception as e:
            logger.error(f"清理日志文件失败: {e}")

    def health_check(self) -> Dict[str, Any]:
        """日志系统健康检查"""
        try:
            health_status = {
                "status": "healthy",
                "handlers_count": len(self.handlers),
                "log_directory_exists": self.log_dir.exists(),
                "writable": os.access(self.log_dir, os.W_OK),
                "disk_space_mb": self._get_disk_space(),
                "metrics": self.get_metrics(),
            }

            # 检查日志文件是否可写
            test_file = self.log_dir / "health_check.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
                health_status["write_test"] = True
            except Exception:
                health_status["write_test"] = False
                health_status["status"] = "unhealthy"

            return health_status
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _get_disk_space(self) -> float:
        """获取磁盘可用空间(MB)"""
        try:
            import shutil

            total, used, free = shutil.disk_usage(self.log_dir)
            return free / (1024 * 1024)
        except Exception:
            return -1

    def cleanup(self) -> None:
        """清理日志处理器"""
        for handler_id in self.handlers:
            logger.remove(handler_id)
        self.handlers.clear()
        logger.info("日志处理器已清理")


# 全局日志配置实例
_logging_config: Optional[LoggingConfig] = None


def setup_logging() -> LoggingConfig:
    """初始化全局日志配置"""
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()
        logger.info("全局日志系统已初始化")
    return _logging_config


def get_logging_config() -> LoggingConfig:
    """获取日志配置实例"""
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()
    return _logging_config


# 自动初始化
_logging_config = LoggingConfig()


def get_logger(name: Optional[str] = None, module: Optional[str] = None) -> Any:
    """获取配置好的logger实例"""
    bound_logger = logger

    if name:
        bound_logger = bound_logger.bind(name=name)

    if module:
        bound_logger = bound_logger.bind(module=module)

    return bound_logger


# 性能监控装饰器
def log_performance(operation_name: Optional[str] = None) -> Callable[[F], F]:
    """性能监控装饰器"""

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()

            # 生成correlation ID
            cid = str(uuid.uuid4())
            correlation_id.set(cid)

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # 记录性能指标
                global _logging_config
                if _logging_config is not None:
                    _logging_config.metrics.record_performance(op_name, duration)

                logger.bind(PERFORMANCE=True, correlation_id=cid).info(
                    f"Operation {op_name} completed",
                    extra={
                        "operation": op_name,
                        "duration": duration,
                        "status": "success",
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.bind(PERFORMANCE=True, correlation_id=cid).error(
                    f"Operation {op_name} failed",
                    extra={
                        "operation": op_name,
                        "duration": duration,
                        "status": "error",
                        "error": str(e),
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                )
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()

            # 生成correlation ID
            cid = str(uuid.uuid4())
            correlation_id.set(cid)

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # 记录性能指标
                global _logging_config
                if _logging_config is not None:
                    _logging_config.metrics.record_performance(op_name, duration)

                logger.bind(PERFORMANCE=True, correlation_id=cid).info(
                    f"Operation {op_name} completed",
                    extra={
                        "operation": op_name,
                        "duration": duration,
                        "status": "success",
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.bind(PERFORMANCE=True, correlation_id=cid).error(
                    f"Operation {op_name} failed",
                    extra={
                        "operation": op_name,
                        "duration": duration,
                        "status": "error",
                        "error": str(e),
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper  # type: ignore

    return decorator


def with_correlation_id(cid: Optional[str] = None) -> Any:
    """设置correlation ID上下文管理器"""

    class CorrelationContext:
        def __init__(self, correlation_id_value: str) -> None:
            self.correlation_id_value = correlation_id_value or str(uuid.uuid4())
            self.token: Any = None

        def __enter__(self) -> str:
            self.token = correlation_id.set(self.correlation_id_value)
            return self.correlation_id_value

        def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            if self.token:
                correlation_id.reset(self.token)

    return CorrelationContext(cid or str(uuid.uuid4()))


def log_download(message: str, **kwargs: Any) -> None:
    """记录下载日志"""
    logger.bind(DOWNLOAD=True).info(message, extra=kwargs)


def log_network(message: str, **kwargs: Any) -> None:
    """记录网络日志"""
    logger.bind(NETWORK=True).info(message, extra=kwargs)


def log_exception(exception: Exception, message: Optional[str] = None, **kwargs: Any) -> None:
    """记录异常日志"""
    logger.bind(EXCEPTION=True).error(
        message or f"Exception occurred: {type(exception).__name__}",
        extra={
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            **kwargs,
        },
    )


def get_log_stats() -> Dict[str, Any]:
    """获取日志统计信息"""
    global _logging_config
    if _logging_config is None:
        setup_logging()
    if _logging_config is not None:
        return _logging_config.get_metrics()
    return {}


def health_check() -> Dict[str, Any]:
    """日志系统健康检查"""
    global _logging_config
    if _logging_config is None:
        setup_logging()
    if _logging_config is not None:
        return _logging_config.health_check()
    return {"status": "error", "error": "Logging config not initialized"}


def archive_logs(days_old: int = 30) -> None:
    """归档旧日志"""
    global _logging_config
    if _logging_config is None:
        setup_logging()
    if _logging_config is not None:
        _logging_config.archive_old_logs(days_old)


def cleanup_logs(max_size_mb: int = 100) -> None:
    """清理日志文件"""
    global _logging_config
    if _logging_config is None:
        setup_logging()
    if _logging_config is not None:
        _logging_config.cleanup_logs(max_size_mb)


# 向后兼容的函数
def log_performance_legacy(func_name: str, duration: float, **kwargs: Any) -> None:
    """记录性能日志 - 向后兼容版本"""
    global _logging_config
    if _logging_config is None:
        setup_logging()
    if _logging_config is not None:
        _logging_config.metrics.record_performance(func_name, duration)
    logger.bind(PERFORMANCE=True).info(
        f"函数 {func_name} 执行时间: {duration:.3f}s",
        extra={"function": func_name, "duration": duration, **kwargs},
    )


# 装饰器用于简单的性能监控
def monitor_performance(func: F) -> F:
    """简单的性能监控装饰器"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            log_performance_legacy(func.__name__, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            log_performance_legacy(func.__name__, duration, error=str(e))
            raise

    return wrapper  # type: ignore
