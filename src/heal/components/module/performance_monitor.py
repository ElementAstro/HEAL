"""
Performance Monitoring System
Provides real-time performance monitoring and metrics collection for modules.
"""

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

import psutil
from PySide6.QtCore import QObject, QTimer, Signal

from src.heal.common.logging_config import get_logger
from src.heal.common.resource_manager import register_timer

logger = get_logger(__name__)


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """指标值"""

    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMetric:
    """性能指标 - 增强版本，支持数据清理"""

    name: str
    type: MetricType
    description: str
    unit: str
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    max_age_seconds: float = field(default=24 * 3600)  # 默认保留24小时
    last_cleanup: float = field(default_factory=time.time)

    def add_value(self, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """添加指标值"""
        metric_value = MetricValue(value=value, timestamp=time.time(), tags=tags or {})
        self.values.append(metric_value)

        # 定期清理旧数据
        self._cleanup_old_data()

    def _cleanup_old_data(self) -> None:
        """清理过期数据"""
        current_time = time.time()

        # 每5分钟清理一次
        if current_time - self.last_cleanup < 300:
            return

        cutoff_time = current_time - self.max_age_seconds

        # 从左侧移除过期数据
        while self.values and self.values[0].timestamp < cutoff_time:
            self.values.popleft()

        self.last_cleanup = current_time

    @property
    def latest_value(self) -> Optional[float]:
        """获取最新值"""
        return self.values[-1].value if self.values else None

    @property
    def average_value(self) -> Optional[float]:
        """获取平均值"""
        if not self.values:
            return None
        return sum(v.value for v in self.values) / len(self.values)

    @property
    def max_value(self) -> Optional[float]:
        """获取最大值"""
        return max(v.value for v in self.values) if self.values else None

    @property
    def min_value(self) -> Optional[float]:
        """获取最小值"""
        return min(v.value for v in self.values) if self.values else None


class PerformanceAlert:
    """性能告警"""

    def __init__(
        self,
        name: str,
        condition: Callable[[float], bool],
        message: str,
        severity: str = "warning",
    ) -> None:
        self.name = name
        self.condition = condition
        self.message = message
        self.severity = severity
        self.triggered = False
        self.last_trigger_time = 0.0
        self.trigger_count = 0

    def check(self, value: float) -> bool:
        """检查是否触发告警"""
        if self.condition(value):
            if not self.triggered:
                self.triggered = True
                self.last_trigger_time = time.time()
                self.trigger_count += 1
                return True
        else:
            self.triggered = False
        return False


class SystemResourceMonitor:
    """系统资源监控器"""

    def __init__(self) -> None:
        self.process = psutil.Process()

    def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        return self.process.cpu_percent()

    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        memory_info = self.process.memory_info()
        return {
            "rss": memory_info.rss / 1024 / 1024,  # MB
            "vms": memory_info.vms / 1024 / 1024,  # MB
            "percent": self.process.memory_percent(),
        }

    def get_disk_io(self) -> Dict[str, float]:
        """获取磁盘IO"""
        try:
            io_counters = self.process.io_counters()
            return {
                "read_bytes": io_counters.read_bytes,
                "write_bytes": io_counters.write_bytes,
                "read_count": io_counters.read_count,
                "write_count": io_counters.write_count,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {
                "read_bytes": 0,
                "write_bytes": 0,
                "read_count": 0,
                "write_count": 0,
            }

    def get_thread_count(self) -> int:
        """获取线程数"""
        return self.process.num_threads()


class PerformanceMonitor(QObject):
    """性能监控器 - 增强版本，支持内存管理和数据清理"""

    # 信号
    metric_updated = Signal(str, float)
    alert_triggered = Signal(str, str, str)  # name, message, severity
    memory_cleanup_performed = Signal(int)  # cleaned_items_count

    def __init__(self, update_interval: int = 1000):  # ms
        super().__init__()
        self.update_interval = update_interval
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.alerts: Dict[str, PerformanceAlert] = {}
        self.system_monitor = SystemResourceMonitor()
        self.logger = logger.bind(component="PerformanceMonitor")

        # 线程安全锁
        self._metrics_lock = threading.RLock()

        # 内存管理配置
        self.max_memory_usage_mb = 100  # 最大内存使用量(MB)
        self.cleanup_threshold_mb = 80  # 清理阈值(MB)
        self.last_memory_check = time.time()

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_metrics)

        # 清理定时器
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._perform_cleanup)
        self.cleanup_timer.start(300000)  # 每5分钟清理一次

        # 注册定时器到资源管理器
        register_timer(
            f"performance_monitor_timer_{id(self)}", self.timer, "性能监控主定时器"
        )
        register_timer(
            f"performance_cleanup_timer_{id(self)}",
            self.cleanup_timer,
            "性能监控清理定时器",
        )

        # 运行状态
        self.running = False
        self.start_time = time.time()

        # 初始化系统指标
        self._init_system_metrics()

        # 初始化默认告警
        self._init_default_alerts()

    def _init_system_metrics(self) -> None:
        """初始化系统指标"""
        self.register_metric("cpu_usage", MetricType.GAUGE, "CPU使用率", "%")
        self.register_metric("memory_rss", MetricType.GAUGE, "内存使用量(RSS)", "MB")
        self.register_metric("memory_percent", MetricType.GAUGE, "内存使用率", "%")
        self.register_metric("thread_count", MetricType.GAUGE, "线程数", "count")
        self.register_metric("uptime", MetricType.GAUGE, "运行时间", "seconds")

        # 模块相关指标
        self.register_metric(
            "module_load_time", MetricType.HISTOGRAM, "模块加载时间", "ms"
        )
        self.register_metric(
            "module_operation_count", MetricType.COUNTER, "模块操作次数", "count"
        )
        self.register_metric(
            "module_error_count", MetricType.COUNTER, "模块错误次数", "count"
        )
        self.register_metric("module_success_rate", MetricType.GAUGE, "模块成功率", "%")

    def _init_default_alerts(self) -> None:
        """初始化默认告警"""
        # CPU使用率告警
        self.add_alert(
            "high_cpu_usage", lambda x: x > 80, "CPU使用率过高 (>80%)", "warning"
        )

        # 内存使用率告警
        self.add_alert(
            "high_memory_usage", lambda x: x > 85, "内存使用率过高 (>85%)", "warning"
        )

        # 线程数告警
        self.add_alert(
            "too_many_threads", lambda x: x > 100, "线程数过多 (>100)", "critical"
        )

    def register_metric(
        self, name: str, metric_type: MetricType, description: str, unit: str
    ):
        """注册性能指标"""
        self.metrics[name] = PerformanceMetric(
            name=name, type=metric_type, description=description, unit=unit
        )
        self.logger.debug(f"注册性能指标: {name}")

    def add_alert(
        self,
        name: str,
        condition: Callable[[float], bool],
        message: str,
        severity: str = "warning",
    ):
        """添加性能告警"""
        self.alerts[name] = PerformanceAlert(name, condition, message, severity)
        self.logger.debug(f"添加性能告警: {name}")

    def record_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """记录性能指标 - 线程安全版本"""
        with self._metrics_lock:
            if name in self.metrics:
                self.metrics[name].add_value(value, tags)
                self.metric_updated.emit(name, value)

                # 检查告警
                if name in self.alerts:
                    alert = self.alerts[name]
                    if alert.check(value):
                        self.alert_triggered.emit(
                            alert.name, alert.message, alert.severity
                        )
                        self.logger.warning(f"性能告警触发: {alert.message}")

        # 定期检查内存使用
        self._check_memory_usage()

    def start_monitoring(self) -> None:
        """开始监控"""
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.timer.start(self.update_interval)
            self.logger.info("开始性能监控")

    def stop_monitoring(self) -> None:
        """停止监控"""
        if self.running:
            self.running = False
            self.timer.stop()
            self.logger.info("停止性能监控")

    def _update_metrics(self) -> None:
        """更新系统指标"""
        try:
            # CPU使用率
            cpu_usage = self.system_monitor.get_cpu_usage()
            self.record_metric("cpu_usage", cpu_usage)

            # 内存使用情况
            memory_info = self.system_monitor.get_memory_usage()
            self.record_metric("memory_rss", memory_info["rss"])
            self.record_metric("memory_percent", memory_info["percent"])

            # 线程数
            thread_count = self.system_monitor.get_thread_count()
            self.record_metric("thread_count", thread_count)

            # 运行时间
            uptime = time.time() - self.start_time
            self.record_metric("uptime", uptime)

        except Exception as e:
            self.logger.error(f"更新性能指标时发生错误: {e}")

    def get_metric(self, name: str) -> Optional[PerformanceMetric]:
        """获取性能指标"""
        return self.metrics.get(name)

    def get_all_metrics(self) -> Dict[str, PerformanceMetric]:
        """获取所有性能指标"""
        return self.metrics.copy()

    def get_metric_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指标摘要"""
        metric = self.metrics.get(name)
        if not metric:
            return None

        return {
            "name": metric.name,
            "type": metric.type.value,
            "description": metric.description,
            "unit": metric.unit,
            "latest_value": metric.latest_value,
            "average_value": metric.average_value,
            "max_value": metric.max_value,
            "min_value": metric.min_value,
            "sample_count": len(metric.values),
        }

    def get_all_summaries(self) -> Dict[str, Dict[str, Any]]:
        """获取所有指标摘要"""
        summaries = {}
        for name in self.metrics:
            summary = self.get_metric_summary(name)
            if summary:
                summaries[name] = summary
        return summaries

    def export_metrics(self, filepath: str) -> None:
        """导出指标数据"""
        try:
            data: Dict[str, Any] = {"timestamp": time.time(), "metrics": {}}

            for name, metric in self.metrics.items():
                data["metrics"][name] = {
                    "name": metric.name,
                    "type": metric.type.value,
                    "description": metric.description,
                    "unit": metric.unit,
                    "values": [
                        {"value": v.value, "timestamp": v.timestamp, "tags": v.tags}
                        for v in metric.values
                    ],
                }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"指标数据已导出到: {filepath}")

        except Exception as e:
            self.logger.error(f"导出指标数据失败: {e}")

    def clear_metrics(self) -> None:
        """清除所有指标数据"""
        for metric in self.metrics.values():
            metric.values.clear()
        self.logger.info("已清除所有指标数据")

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        report: Dict[str, Any] = {
            "timestamp": time.time(),
            "monitoring_duration": time.time() - self.start_time if self.running else 0,
            "system_info": {
                "cpu_usage": self._get_metric_latest_value("cpu_usage"),
                "memory_usage": self._get_metric_latest_value("memory_percent"),
                "thread_count": self._get_metric_latest_value("thread_count"),
            },
            "module_metrics": {},
            "alerts": [],
        }

        # 添加模块相关指标
        module_metrics = [
            "module_load_time",
            "module_operation_count",
            "module_error_count",
            "module_success_rate",
        ]
        for metric_name in module_metrics:
            metric = self.metrics.get(metric_name)
            if metric:
                report["module_metrics"][metric_name] = {
                    "latest": metric.latest_value,
                    "average": metric.average_value,
                    "max": metric.max_value,
                    "min": metric.min_value,
                }

        # 添加告警信息
        for alert_name, alert in self.alerts.items():
            if alert.trigger_count > 0:
                report["alerts"].append(
                    {
                        "name": alert_name,
                        "message": alert.message,
                        "severity": alert.severity,
                        "trigger_count": alert.trigger_count,
                        "last_trigger_time": alert.last_trigger_time,
                    }
                )

        return report

    def _get_metric_latest_value(self, metric_name: str) -> Optional[float]:
        """安全地获取指标的最新值"""
        with self._metrics_lock:
            metric = self.metrics.get(metric_name)
            return metric.latest_value if metric else None

    def _check_memory_usage(self) -> None:
        """检查内存使用情况"""
        current_time = time.time()

        # 每分钟检查一次
        if current_time - self.last_memory_check < 60:
            return

        try:
            # 估算当前内存使用量
            memory_usage = self._estimate_memory_usage()

            if memory_usage > self.cleanup_threshold_mb:
                self.logger.warning(f"内存使用量过高: {memory_usage:.1f}MB, 开始清理")
                self._perform_aggressive_cleanup()

            self.last_memory_check = current_time

        except Exception as e:
            self.logger.error(f"检查内存使用时发生错误: {e}")

    def _estimate_memory_usage(self) -> float:
        """估算内存使用量(MB)"""
        total_values = 0

        with self._metrics_lock:
            for metric in self.metrics.values():
                total_values += len(metric.values)

        # 粗略估算：每个MetricValue约占用100字节
        estimated_mb = (total_values * 100) / (1024 * 1024)
        return estimated_mb

    def _perform_cleanup(self) -> None:
        """执行定期清理"""
        try:
            cleaned_count = 0

            with self._metrics_lock:
                for metric in self.metrics.values():
                    old_count = len(metric.values)
                    metric._cleanup_old_data()
                    cleaned_count += old_count - len(metric.values)

            if cleaned_count > 0:
                self.logger.debug(f"定期清理完成，清理了 {cleaned_count} 个过期数据点")
                self.memory_cleanup_performed.emit(cleaned_count)

        except Exception as e:
            self.logger.error(f"执行定期清理时发生错误: {e}")

    def _perform_aggressive_cleanup(self) -> None:
        """执行激进清理（内存压力大时）"""
        try:
            cleaned_count = 0

            with self._metrics_lock:
                for metric in self.metrics.values():
                    old_count = len(metric.values)

                    # 只保留最近1小时的数据
                    cutoff_time = time.time() - 3600
                    while metric.values and metric.values[0].timestamp < cutoff_time:
                        metric.values.popleft()

                    # 如果还是太多，只保留最近500个数据点
                    while len(metric.values) > 500:
                        metric.values.popleft()

                    cleaned_count += old_count - len(metric.values)

            self.logger.info(f"激进清理完成，清理了 {cleaned_count} 个数据点")
            self.memory_cleanup_performed.emit(cleaned_count)

        except Exception as e:
            self.logger.error(f"执行激进清理时发生错误: {e}")

    def configure_memory_limits(self, max_memory_mb: int, cleanup_threshold_mb: int) -> None:
        """配置内存限制"""
        self.max_memory_usage_mb = max_memory_mb
        self.cleanup_threshold_mb = cleanup_threshold_mb
        self.logger.info(
            f"内存限制已配置: 最大 {max_memory_mb}MB, 清理阈值 {cleanup_threshold_mb}MB"
        )

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        with self._metrics_lock:
            total_metrics = len(self.metrics)
            total_values = sum(len(metric.values) for metric in self.metrics.values())
            estimated_memory = self._estimate_memory_usage()

        return {
            "total_metrics": total_metrics,
            "total_values": total_values,
            "estimated_memory_mb": estimated_memory,
            "max_memory_mb": self.max_memory_usage_mb,
            "cleanup_threshold_mb": self.cleanup_threshold_mb,
            "memory_usage_percent": (estimated_memory / self.max_memory_usage_mb) * 100,
        }


class ModulePerformanceTracker:
    """模块性能跟踪器"""

    def __init__(self, monitor: PerformanceMonitor) -> None:
        self.monitor = monitor
        self.module_stats: Dict[str, Dict[str, Any]] = {}

    def track_module_load(self, module_name: str) -> None:
        """跟踪模块加载"""
        if module_name not in self.module_stats:
            self.module_stats[module_name] = {
                "load_count": 0,
                "operation_count": 0,
                "error_count": 0,
                "total_load_time": 0,
                "last_load_time": 0,
            }

        start_time = time.time()

        class LoadContext:
            def __enter__(self) -> None:
                return self

            def __exit__(self, exc_type, exc_val, exc_tb) -> None:
                end_time = time.time()
                load_time = (end_time - start_time) * 1000  # ms

                self.outer.module_stats[module_name]["load_count"] += 1
                self.outer.module_stats[module_name]["total_load_time"] += load_time
                self.outer.module_stats[module_name]["last_load_time"] = load_time

                self.outer.monitor.record_metric(
                    "module_load_time", load_time, {"module": module_name}
                )

                if exc_type is not None:
                    self.outer.track_module_error(module_name, str(exc_val))

            def __init__(self, outer) -> None:
                self.outer = outer

        return LoadContext(self)

    def track_module_operation(self, module_name: str, operation_name: str) -> None:
        """跟踪模块操作"""
        if module_name not in self.module_stats:
            self.module_stats[module_name] = {
                "load_count": 0,
                "operation_count": 0,
                "error_count": 0,
                "total_load_time": 0,
                "last_load_time": 0,
            }

        self.module_stats[module_name]["operation_count"] += 1
        self.monitor.record_metric(
            "module_operation_count",
            1,
            {"module": module_name, "operation": operation_name},
        )

    def track_module_error(self, module_name: str, error_message: str) -> None:
        """跟踪模块错误"""
        if module_name not in self.module_stats:
            self.module_stats[module_name] = {
                "load_count": 0,
                "operation_count": 0,
                "error_count": 0,
                "total_load_time": 0,
                "last_load_time": 0,
            }

        self.module_stats[module_name]["error_count"] += 1
        self.monitor.record_metric(
            "module_error_count", 1, {"module": module_name, "error": error_message}
        )

        # 更新成功率
        self._update_success_rate(module_name)

    def _update_success_rate(self, module_name: str) -> None:
        """更新模块成功率"""
        stats = self.module_stats[module_name]
        total_operations = stats["operation_count"]
        error_count = stats["error_count"]

        if total_operations > 0:
            success_rate = ((total_operations - error_count) / total_operations) * 100
            self.monitor.record_metric(
                "module_success_rate", success_rate, {"module": module_name}
            )

    def get_module_stats(self, module_name: str) -> Optional[Dict[str, Any]]:
        """获取模块统计信息"""
        return self.module_stats.get(module_name)

    def get_all_module_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模块统计信息"""
        return self.module_stats.copy()
