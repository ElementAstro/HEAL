"""
Performance Analyzer - 性能分析工具
识别和分析应用中的性能瓶颈
"""

import cProfile
import functools
import gc
import io
import pstats
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Union
from contextlib import _GeneratorContextManager

import psutil

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceIssue:
    """性能问题"""

    category: str  # 'io', 'memory', 'cpu', 'ui', 'network'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    location: str  # 函数或模块位置
    metric_value: float
    threshold: float
    suggestion: str
    detected_at: float = field(default_factory=time.time)


@dataclass
class FunctionProfile:
    """函数性能分析"""

    function_name: str
    call_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    max_time: float = 0.0
    min_time: float = float("inf")
    memory_usage: List[float] = field(default_factory=list)

    def add_call(self, execution_time: float, memory_usage: Optional[float] = None) -> None:
        """添加函数调用记录"""
        self.call_count += 1
        self.total_time += execution_time
        self.avg_time = self.total_time / self.call_count
        self.max_time = max(self.max_time, execution_time)
        self.min_time = min(self.min_time, execution_time)

        if memory_usage is not None:
            self.memory_usage.append(memory_usage)


class PerformanceAnalyzer:
    """性能分析器"""

    def __init__(self) -> None:
        self.logger = logger.bind(component="PerformanceAnalyzer")

        # 性能阈值配置
        self.thresholds = {
            "function_execution_time": 0.1,  # 100ms
            "io_operation_time": 0.5,  # 500ms
            "memory_usage_mb": 100,  # 100MB
            "cpu_usage_percent": 80,  # 80%
            "ui_block_time": 0.05,  # 50ms
            "network_timeout": 5.0,  # 5s
        }

        # 分析数据
        self.function_profiles: Dict[str, FunctionProfile] = {}
        self.performance_issues: List[PerformanceIssue] = []
        self.io_operations: List[Dict[str, Any]] = []
        self.memory_snapshots: List[Dict[str, Any]] = []

        # 分析状态
        self.is_profiling = False
        self.profiler: Optional[cProfile.Profile] = None
        self.analysis_lock = threading.Lock()

        self.logger.info("性能分析器已初始化")

    def start_profiling(self) -> None:
        """开始性能分析"""
        with self.analysis_lock:
            if self.is_profiling:
                self.logger.warning("性能分析已在进行中")
                return

            self.profiler = cProfile.Profile()
            self.profiler.enable()
            self.is_profiling = True

            self.logger.info("性能分析已开始")

    def stop_profiling(self) -> Optional[pstats.Stats]:
        """停止性能分析"""
        with self.analysis_lock:
            if not self.is_profiling or self.profiler is None:
                self.logger.warning("性能分析未在进行中")
                return None

            self.profiler.disable()
            self.is_profiling = False

            # 生成统计信息
            stats_stream = io.StringIO()
            stats = pstats.Stats(self.profiler, stream=stats_stream)
            stats.sort_stats("cumulative")

            self.logger.info("性能分析已停止")
            return stats

    def profile_function(self, threshold: Optional[float] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """函数性能分析装饰器"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                func_name = f"{func.__module__}.{func.__qualname__}"

                # 记录内存使用
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB

                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.perf_counter()
                    execution_time = end_time - start_time

                    # 记录内存使用
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    memory_delta = memory_after - memory_before

                    # 更新函数分析数据
                    with self.analysis_lock:
                        if func_name not in self.function_profiles:
                            self.function_profiles[func_name] = FunctionProfile(
                                func_name
                            )

                        self.function_profiles[func_name].add_call(
                            execution_time, memory_delta
                        )

                    # 检查性能问题
                    used_threshold = (
                        threshold or self.thresholds["function_execution_time"]
                    )
                    if execution_time > used_threshold:
                        self._report_performance_issue(
                            category="cpu",
                            severity=self._get_severity(execution_time, used_threshold),
                            description=f"函数执行时间过长: {execution_time:.3f}s",
                            location=func_name,
                            metric_value=execution_time,
                            threshold=used_threshold,
                            suggestion="考虑优化算法或使用异步处理",
                        )

                    # 检查内存使用
                    if memory_delta > self.thresholds["memory_usage_mb"]:
                        self._report_performance_issue(
                            category="memory",
                            severity=self._get_severity(
                                memory_delta, self.thresholds["memory_usage_mb"]
                            ),
                            description=f"函数内存使用过多: {memory_delta:.1f}MB",
                            location=func_name,
                            metric_value=memory_delta,
                            threshold=self.thresholds["memory_usage_mb"],
                            suggestion="检查内存泄漏或优化数据结构",
                        )

            return wrapper

        return decorator

    @contextmanager
    def profile_io_operation(self, operation_name: str) -> Generator[None, None, None]:
        """IO操作性能分析上下文管理器"""
        start_time = time.perf_counter()
        io_info = {
            "operation_name": operation_name,
            "start_time": start_time,
            "thread_id": threading.get_ident(),
        }

        try:
            yield
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            io_info.update({"end_time": end_time, "execution_time": execution_time})

            with self.analysis_lock:
                self.io_operations.append(io_info)

            # 检查IO性能
            if execution_time > self.thresholds["io_operation_time"]:
                self._report_performance_issue(
                    category="io",
                    severity=self._get_severity(
                        execution_time, self.thresholds["io_operation_time"]
                    ),
                    description=f"IO操作耗时过长: {execution_time:.3f}s",
                    location=operation_name,
                    metric_value=execution_time,
                    threshold=self.thresholds["io_operation_time"],
                    suggestion="考虑使用异步IO或缓存机制",
                )

    def take_memory_snapshot(self, label: str = "") -> Optional[Dict[str, Any]]:
        """获取内存快照"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            snapshot = {
                "label": label,
                "timestamp": time.time(),
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent(),
                "gc_objects": len(gc.get_objects()),
            }

            with self.analysis_lock:
                self.memory_snapshots.append(snapshot)

            return snapshot

        except Exception as e:
            self.logger.error(f"获取内存快照失败: {e}")
            return None

    def analyze_memory_growth(self) -> List[PerformanceIssue]:
        """分析内存增长"""
        issues: List[PerformanceIssue] = []

        if len(self.memory_snapshots) < 2:
            return issues

        # 分析内存增长趋势
        snapshots = sorted(self.memory_snapshots, key=lambda x: x["timestamp"])

        for i in range(1, len(snapshots)):
            prev_snapshot = snapshots[i - 1]
            curr_snapshot = snapshots[i]

            memory_growth = curr_snapshot["rss_mb"] - prev_snapshot["rss_mb"]
            time_delta = curr_snapshot["timestamp"] - prev_snapshot["timestamp"]

            if memory_growth > 10 and time_delta < 60:  # 1分钟内增长超过10MB
                issue = PerformanceIssue(
                    category="memory",
                    severity="high",
                    description=f"内存快速增长: {memory_growth:.1f}MB in {time_delta:.1f}s",
                    location=f"{prev_snapshot['label']} -> {curr_snapshot['label']}",
                    metric_value=memory_growth,
                    threshold=10.0,
                    suggestion="检查内存泄漏或优化数据管理",
                )
                issues.append(issue)

        return issues

    def get_top_slow_functions(self, limit: int = 10) -> List[FunctionProfile]:
        """获取最慢的函数"""
        with self.analysis_lock:
            sorted_functions = sorted(
                self.function_profiles.values(), key=lambda x: x.avg_time, reverse=True
            )
            return sorted_functions[:limit]

    def get_memory_heavy_functions(self, limit: int = 10) -> List[FunctionProfile]:
        """获取内存使用最多的函数"""
        with self.analysis_lock:
            memory_functions = [
                func for func in self.function_profiles.values() if func.memory_usage
            ]

            sorted_functions = sorted(
                memory_functions,
                key=lambda x: (
                    sum(x.memory_usage) / len(x.memory_usage) if x.memory_usage else 0
                ),
                reverse=True,
            )
            return sorted_functions[:limit]

    def get_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        with self.analysis_lock:
            return {
                "summary": {
                    "total_functions_profiled": len(self.function_profiles),
                    "total_performance_issues": len(self.performance_issues),
                    "total_io_operations": len(self.io_operations),
                    "memory_snapshots": len(self.memory_snapshots),
                },
                "top_slow_functions": [
                    {
                        "name": func.function_name,
                        "avg_time": func.avg_time,
                        "call_count": func.call_count,
                        "total_time": func.total_time,
                    }
                    for func in self.get_top_slow_functions(5)
                ],
                "performance_issues": [
                    {
                        "category": issue.category,
                        "severity": issue.severity,
                        "description": issue.description,
                        "location": issue.location,
                        "suggestion": issue.suggestion,
                    }
                    for issue in self.performance_issues
                ],
                "io_analysis": {
                    "total_operations": len(self.io_operations),
                    "avg_time": (
                        sum(op["execution_time"] for op in self.io_operations)
                        / len(self.io_operations)
                        if self.io_operations
                        else 0
                    ),
                    "slow_operations": [
                        op
                        for op in self.io_operations
                        if op["execution_time"] > self.thresholds["io_operation_time"]
                    ],
                },
            }

    def _report_performance_issue(self, **kwargs: Any) -> None:
        """报告性能问题"""
        issue = PerformanceIssue(**kwargs)

        with self.analysis_lock:
            self.performance_issues.append(issue)

        self.logger.warning(f"性能问题: {issue.description} at {issue.location}")

    def _get_severity(self, value: float, threshold: float) -> str:
        """根据值和阈值确定严重性"""
        ratio = value / threshold

        if ratio >= 5:
            return "critical"
        elif ratio >= 3:
            return "high"
        elif ratio >= 2:
            return "medium"
        else:
            return "low"

    def clear_data(self) -> None:
        """清理分析数据"""
        with self.analysis_lock:
            self.function_profiles.clear()
            self.performance_issues.clear()
            self.io_operations.clear()
            self.memory_snapshots.clear()

        self.logger.info("性能分析数据已清理")


# 全局性能分析器实例
global_performance_analyzer = PerformanceAnalyzer()


# 便捷装饰器
def profile_performance(threshold: Optional[float] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """性能分析装饰器"""
    return global_performance_analyzer.profile_function(threshold)


def profile_io(operation_name: str) -> _GeneratorContextManager[None]:
    """IO性能分析上下文管理器"""
    return global_performance_analyzer.profile_io_operation(operation_name)


def take_memory_snapshot(label: str = "") -> Optional[Dict[str, Any]]:
    """获取内存快照"""
    return global_performance_analyzer.take_memory_snapshot(label)


class PerformanceOptimizer:
    """性能优化建议器"""

    def __init__(self, analyzer: PerformanceAnalyzer) -> None:
        self.analyzer = analyzer
        self.logger = logger.bind(component="PerformanceOptimizer")

    def analyze_and_suggest(self) -> Dict[str, List[str]]:
        """分析性能并提供优化建议"""
        suggestions: Dict[str, List[str]] = {
            "io_optimizations": [],
            "memory_optimizations": [],
            "cpu_optimizations": [],
            "ui_optimizations": [],
            "general_optimizations": [],
        }

        # 分析IO操作
        slow_io_ops = [
            op
            for op in self.analyzer.io_operations
            if op["execution_time"] > self.analyzer.thresholds["io_operation_time"]
        ]

        if slow_io_ops:
            suggestions["io_optimizations"].extend(
                [
                    "考虑使用异步IO操作减少阻塞",
                    "实现文件缓存机制减少重复读取",
                    "使用连接池优化网络请求",
                    "批量处理IO操作减少系统调用",
                ]
            )

        # 分析内存使用
        memory_heavy_functions = self.analyzer.get_memory_heavy_functions(5)
        if memory_heavy_functions:
            suggestions["memory_optimizations"].extend(
                [
                    "使用生成器替代列表减少内存占用",
                    "实现对象池重用大对象",
                    "及时释放不需要的引用",
                    "使用__slots__优化类内存使用",
                ]
            )

        # 分析CPU密集操作
        slow_functions = self.analyzer.get_top_slow_functions(5)
        if slow_functions:
            suggestions["cpu_optimizations"].extend(
                [
                    "使用多线程处理CPU密集任务",
                    "优化算法复杂度",
                    "使用缓存避免重复计算",
                    "考虑使用C扩展优化关键路径",
                ]
            )

        # UI优化建议
        ui_blocking_issues = [
            issue
            for issue in self.analyzer.performance_issues
            if issue.category == "ui"
        ]

        if ui_blocking_issues:
            suggestions["ui_optimizations"].extend(
                [
                    "将耗时操作移到后台线程",
                    "使用QTimer分批处理大量数据",
                    "实现虚拟化列表减少UI元素",
                    "优化绘制操作减少重绘",
                ]
            )

        # 通用优化建议
        if self.analyzer.performance_issues:
            suggestions["general_optimizations"].extend(
                [
                    "启用性能监控持续跟踪",
                    "定期进行性能测试",
                    "使用性能分析工具定位瓶颈",
                    "建立性能基准和告警机制",
                ]
            )

        return suggestions

    def generate_optimization_plan(self) -> Dict[str, Any]:
        """生成优化计划"""
        suggestions = self.analyze_and_suggest()
        issues = self.analyzer.performance_issues

        # 按严重性分组问题
        critical_issues = [i for i in issues if i.severity == "critical"]
        high_issues = [i for i in issues if i.severity == "high"]
        medium_issues = [i for i in issues if i.severity == "medium"]

        return {
            "priority_levels": {
                "immediate": {
                    "description": "需要立即处理的关键性能问题",
                    "issues": critical_issues,
                    "actions": suggestions.get("general_optimizations", [])[:2],
                },
                "high": {
                    "description": "高优先级性能优化",
                    "issues": high_issues,
                    "actions": suggestions.get("cpu_optimizations", [])[:3],
                },
                "medium": {
                    "description": "中等优先级性能改进",
                    "issues": medium_issues,
                    "actions": suggestions.get("memory_optimizations", [])[:3],
                },
            },
            "optimization_areas": suggestions,
            "estimated_impact": self._estimate_optimization_impact(issues),
            "implementation_order": self._suggest_implementation_order(suggestions),
        }

    def _estimate_optimization_impact(
        self, issues: List[PerformanceIssue]
    ) -> Dict[str, str]:
        """估算优化影响"""
        if not issues:
            return {"overall": "low"}

        critical_count = sum(1 for i in issues if i.severity == "critical")
        high_count = sum(1 for i in issues if i.severity == "high")

        if critical_count > 0:
            return {
                "overall": "high",
                "description": "存在关键性能问题，优化后将显著提升性能",
            }
        elif high_count > 2:
            return {
                "overall": "medium",
                "description": "存在多个高优先级问题，优化后将明显改善性能",
            }
        else:
            return {
                "overall": "low",
                "description": "性能问题较少，优化后将适度提升性能",
            }

    def _suggest_implementation_order(
        self, suggestions: Dict[str, List[str]]
    ) -> List[str]:
        """建议实现顺序"""
        order = []

        # 优先处理影响最大的优化
        if suggestions.get("io_optimizations"):
            order.append("IO操作优化 - 通常能带来最明显的性能提升")

        if suggestions.get("memory_optimizations"):
            order.append("内存使用优化 - 提升应用稳定性和响应速度")

        if suggestions.get("ui_optimizations"):
            order.append("UI响应优化 - 直接改善用户体验")

        if suggestions.get("cpu_optimizations"):
            order.append("CPU密集操作优化 - 提升计算效率")

        return order


# 全局优化器实例
global_performance_optimizer = PerformanceOptimizer(global_performance_analyzer)
