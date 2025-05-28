import sys
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger
from enum import Enum
from functools import wraps


class LogLevel(Enum):
    """日志级别枚举"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO" 
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingConfig:
    """统一日志配置类"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.handlers: List[int] = []
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        # 移除默认处理器
        logger.remove()
        
        # 控制台输出处理器
        console_handler = logger.add(
            sys.stderr,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        self.handlers.append(console_handler)
        
        # 主应用日志文件
        main_handler = logger.add(
            self.log_dir / "application.log",
            rotation="10 MB",
            retention="30 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            backtrace=True,
            diagnose=True,
            encoding="utf-8"
        )
        self.handlers.append(main_handler)
        
        # 错误专用日志文件
        error_handler = logger.add(
            self.log_dir / "errors.log",
            rotation="5 MB",
            retention="60 days",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
            backtrace=True,
            diagnose=True,
            encoding="utf-8"
        )
        self.handlers.append(error_handler)
        
        # 性能监控日志
        performance_handler = logger.add(
            self.log_dir / "performance.log",
            rotation="5 MB",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            filter=lambda record: "PERFORMANCE" in record["extra"],
            encoding="utf-8"
        )
        self.handlers.append(performance_handler)
        
        # 下载进程专用日志
        download_handler = logger.add(
            self.log_dir / "downloads.log",
            rotation="5 MB",
            retention="14 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
            filter=lambda record: "DOWNLOAD" in record["extra"],
            encoding="utf-8"
        )
        self.handlers.append(download_handler)
        
        # 网络请求日志
        network_handler = logger.add(
            self.log_dir / "network.log",
            rotation="5 MB",
            retention="7 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            filter=lambda record: "NETWORK" in record["extra"],
            encoding="utf-8"
        )
        self.handlers.append(network_handler)
        
        logger.info("统一日志配置已初始化")
    
    def add_module_logger(self, module_name: str, level: str = "DEBUG") -> int:
        """为特定模块添加专用日志处理器"""
        handler = logger.add(
            self.log_dir / f"{module_name}.log",
            rotation="2 MB",
            retention="14 days",
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            filter=lambda record: record["extra"].get("module") == module_name,
            backtrace=True,
            diagnose=True,
            encoding="utf-8"
        )
        self.handlers.append(handler)
        logger.bind(module=module_name).info(f"模块 {module_name} 日志处理器已添加")
        return handler
    
    def cleanup(self):
        """清理日志处理器"""
        for handler_id in self.handlers:
            logger.remove(handler_id)
        self.handlers.clear()
        logger.info("日志处理器已清理")


# 全局日志配置实例
_logging_config = None


def setup_logging():
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


def get_logger(name: Optional[str] = None, module: Optional[str] = None):
    """获取配置好的logger实例"""
    bound_logger = logger
    
    if name:
        bound_logger = bound_logger.bind(name=name)
    
    if module:
        bound_logger = bound_logger.bind(module=module)
    
    return bound_logger


def log_performance(func_name: str, duration: float, **kwargs):
    """记录性能日志"""
    logger.bind(PERFORMANCE=True).info(
        f"函数 {func_name} 执行时间: {duration:.3f}s",
        extra={"function": func_name, "duration": duration, **kwargs}
    )


def log_download(message: str, **kwargs):
    """记录下载日志"""
    logger.bind(DOWNLOAD=True).info(message, extra=kwargs)


def log_network(message: str, **kwargs):
    """记录网络日志"""
    logger.bind(NETWORK=True).info(message, extra=kwargs)


# 装饰器用于自动性能监控
def monitor_performance(func):
    """性能监控装饰器"""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            log_performance(func.__name__, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            log_performance(func.__name__, duration, error=str(e))
            raise
    
    return wrapper
