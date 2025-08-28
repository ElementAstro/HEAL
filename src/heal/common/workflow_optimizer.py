"""
Workflow Optimizer - 工作流优化工具
简化复杂的初始化流程和操作序列
Enhanced with detailed performance tracking and memory monitoring
"""

import time
import psutil
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from .logging_config import get_logger

logger = get_logger(__name__)


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PerformanceMetrics:
    """性能指标"""
    cpu_usage_before: float = 0.0
    cpu_usage_after: float = 0.0
    memory_usage_before: float = 0.0  # MB
    memory_usage_after: float = 0.0   # MB
    memory_delta: float = 0.0         # MB
    peak_memory: float = 0.0          # MB
    execution_time: float = 0.0       # seconds
    thread_count_before: int = 0
    thread_count_after: int = 0


@dataclass
class WorkflowStep:
    """工作流步骤 - Enhanced with performance tracking"""
    name: str
    func: Callable
    dependencies: List[str] = field(default_factory=list)
    optional: bool = False
    timeout: float = 30.0
    retry_count: int = 0
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    performance_metrics: Optional[PerformanceMetrics] = None
    start_timestamp: float = 0.0
    end_timestamp: float = 0.0

    def reset(self) -> None:
        """重置步骤状态"""
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None
        self.execution_time = 0.0
        self.performance_metrics = None
        self.start_timestamp = 0.0
        self.end_timestamp = 0.0


class WorkflowOptimizer:
    """工作流优化器 - Enhanced with detailed performance monitoring"""

    def __init__(self, name: str, enable_performance_tracking: bool = True) -> None:
        self.name = name
        self.steps: Dict[str, WorkflowStep] = {}
        self.execution_order: List[str] = []
        self.logger = logger.bind(component="WorkflowOptimizer", workflow=name)
        self.enable_performance_tracking = enable_performance_tracking
        self._performance_lock = threading.Lock()

        # Enhanced execution statistics
        self.execution_stats: Dict[str, Any] = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "step_success_rates": defaultdict(float),
            "performance_history": [],
            "memory_usage_history": [],
            "cpu_usage_history": [],
            "bottleneck_steps": [],
            "optimization_suggestions": []
        }

    def add_step(
        self,
        name: str,
        func: Callable,
        dependencies: Optional[List[str]] = None,
        optional: bool = False,
        timeout: float = 30.0
    ) -> 'WorkflowOptimizer':
        """添加工作流步骤"""
        step = WorkflowStep(
            name=name,
            func=func,
            dependencies=dependencies or [],
            optional=optional,
            timeout=timeout
        )

        self.steps[name] = step
        self.logger.debug(f"添加工作流步骤: {name}")
        return self

    def remove_step(self, name: str) -> bool:
        """移除工作流步骤"""
        if name in self.steps:
            del self.steps[name]
            if name in self.execution_order:
                self.execution_order.remove(name)
            self.logger.debug(f"移除工作流步骤: {name}")
            return True
        return False

    def _resolve_dependencies(self) -> List[str]:
        """解析依赖关系，返回执行顺序"""
        # 使用拓扑排序解析依赖
        in_degree: Dict[str, int] = defaultdict(int)
        graph: Dict[str, List[str]] = defaultdict(list)

        # 构建依赖图
        for step_name, step in self.steps.items():
            for dep in step.dependencies:
                if dep in self.steps:
                    graph[dep].append(step_name)
                    in_degree[step_name] += 1
                else:
                    self.logger.warning(f"步骤 {step_name} 的依赖 {dep} 不存在")

        # 拓扑排序
        queue = deque([name for name in self.steps.keys()
                      if in_degree[name] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # 检查循环依赖
        if len(result) != len(self.steps):
            remaining = set(self.steps.keys()) - set(result)
            raise ValueError(f"检测到循环依赖: {remaining}")

        return result

    def execute(self, skip_optional_on_failure: bool = True) -> Dict[str, Any]:
        """执行工作流"""
        start_time = time.time()
        execution_result: Dict[str, Any] = {
            "success": False,
            "total_time": 0.0,
            "completed_steps": [],
            "failed_steps": [],
            "skipped_steps": [],
            "results": {}
        }

        try:
            # 解析执行顺序
            self.execution_order = self._resolve_dependencies()
            self.logger.info(
                f"开始执行工作流 {self.name}，共 {len(self.execution_order)} 个步骤")

            # 重置所有步骤状态
            for step in self.steps.values():
                step.reset()

            # 按顺序执行步骤
            for step_name in self.execution_order:
                step = self.steps[step_name]

                # 检查依赖是否都已完成
                if not self._check_dependencies(step):
                    if step.optional or skip_optional_on_failure:
                        step.status = StepStatus.SKIPPED
                        execution_result["skipped_steps"].append(step_name)
                        self.logger.info(f"跳过步骤 {step_name}（依赖未满足）")
                        continue
                    else:
                        raise RuntimeError(f"步骤 {step_name} 的依赖未满足")

                # 执行步骤
                success = self._execute_step(step)

                if success:
                    execution_result["completed_steps"].append(step_name)
                    execution_result["results"][step_name] = step.result
                else:
                    execution_result["failed_steps"].append(step_name)

                    if not step.optional:
                        # 必需步骤失败，终止执行
                        self.logger.error(f"必需步骤 {step_name} 执行失败，终止工作流")
                        break

            # 计算执行结果
            total_steps = len(self.execution_order)
            completed_steps = len(execution_result["completed_steps"])
            execution_result["success"] = completed_steps == total_steps or all(
                self.steps[name].optional or name in execution_result["completed_steps"]
                for name in execution_result["failed_steps"]
            )

            execution_result["total_time"] = time.time() - start_time

            # 更新统计信息
            self._update_stats(execution_result)

            self.logger.info(
                f"工作流 {self.name} 执行完成: "
                f"成功={execution_result['success']}, "
                f"完成步骤={completed_steps}/{total_steps}, "
                f"耗时={execution_result['total_time']:.2f}s"
            )

            return execution_result

        except Exception as e:
            execution_result["total_time"] = time.time() - start_time
            self.logger.error(f"工作流 {self.name} 执行失败: {e}")
            raise

    def _check_dependencies(self, step: WorkflowStep) -> bool:
        """检查步骤依赖是否满足"""
        for dep_name in step.dependencies:
            dep_step = self.steps.get(dep_name)
            if not dep_step or dep_step.status != StepStatus.COMPLETED:
                return False
        return True

    def _execute_step(self, step: WorkflowStep) -> bool:
        """执行单个步骤 - Enhanced with performance monitoring"""
        step.status = StepStatus.RUNNING
        step.start_timestamp = time.time()

        # Initialize performance metrics if tracking is enabled
        if self.enable_performance_tracking:
            step.performance_metrics = PerformanceMetrics()
            self._capture_pre_execution_metrics(step)

        try:
            self.logger.debug(f"执行步骤: {step.name}")
            step.result = step.func()
            step.status = StepStatus.COMPLETED
            step.end_timestamp = time.time()
            step.execution_time = step.end_timestamp - step.start_timestamp

            # Capture post-execution metrics
            if self.enable_performance_tracking:
                self._capture_post_execution_metrics(step)
                self._analyze_step_performance(step)

            self.logger.debug(
                f"步骤 {step.name} 执行成功，耗时 {step.execution_time:.3f}s")

            if step.performance_metrics:
                self.logger.debug(
                    f"步骤 {step.name} 性能指标: "
                    f"内存增量={step.performance_metrics.memory_delta:.1f}MB, "
                    f"峰值内存={step.performance_metrics.peak_memory:.1f}MB"
                )

            return True

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = e
            step.end_timestamp = time.time()
            step.execution_time = step.end_timestamp - step.start_timestamp

            # Still capture metrics for failed steps
            if self.enable_performance_tracking and step.performance_metrics:
                self._capture_post_execution_metrics(step)

            self.logger.error(f"步骤 {step.name} 执行失败: {e}")
            return False

    def _capture_pre_execution_metrics(self, step: WorkflowStep) -> None:
        """捕获执行前的性能指标"""
        if not step.performance_metrics:
            return

        try:
            process = psutil.Process()
            step.performance_metrics.cpu_usage_before = process.cpu_percent()
            step.performance_metrics.memory_usage_before = process.memory_info().rss / 1024 / 1024  # MB
            step.performance_metrics.thread_count_before = process.num_threads()
        except Exception as e:
            self.logger.warning(f"无法捕获步骤 {step.name} 的执行前指标: {e}")

    def _capture_post_execution_metrics(self, step: WorkflowStep) -> None:
        """捕获执行后的性能指标"""
        if not step.performance_metrics:
            return

        try:
            process = psutil.Process()
            step.performance_metrics.cpu_usage_after = process.cpu_percent()
            step.performance_metrics.memory_usage_after = process.memory_info().rss / 1024 / 1024  # MB
            step.performance_metrics.thread_count_after = process.num_threads()
            step.performance_metrics.execution_time = step.execution_time

            # Calculate memory delta
            step.performance_metrics.memory_delta = (
                step.performance_metrics.memory_usage_after -
                step.performance_metrics.memory_usage_before
            )

            # Peak memory is the higher of before/after
            step.performance_metrics.peak_memory = max(
                step.performance_metrics.memory_usage_before,
                step.performance_metrics.memory_usage_after
            )

        except Exception as e:
            self.logger.warning(f"无法捕获步骤 {step.name} 的执行后指标: {e}")

    def _analyze_step_performance(self, step: WorkflowStep) -> None:
        """分析步骤性能并生成建议"""
        if not step.performance_metrics:
            return

        metrics = step.performance_metrics
        suggestions = []

        # Memory usage analysis
        if metrics.memory_delta > 50:  # More than 50MB increase
            suggestions.append(f"步骤 {step.name} 内存使用量增加 {metrics.memory_delta:.1f}MB，考虑优化内存使用")

        # Execution time analysis
        if metrics.execution_time > 5.0:  # More than 5 seconds
            suggestions.append(f"步骤 {step.name} 执行时间 {metrics.execution_time:.2f}s 较长，考虑优化算法或异步处理")

        # Thread count analysis
        thread_delta = metrics.thread_count_after - metrics.thread_count_before
        if thread_delta > 5:
            suggestions.append(f"步骤 {step.name} 创建了 {thread_delta} 个线程，注意线程管理")

        # Store suggestions
        if suggestions:
            with self._performance_lock:
                self.execution_stats["optimization_suggestions"].extend(suggestions)

    def _update_stats(self, execution_result: Dict[str, Any]) -> None:
        """更新执行统计 - Enhanced with performance data"""
        self.execution_stats["total_executions"] += 1

        if execution_result["success"]:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1

        # 更新平均执行时间
        total_time = execution_result["total_time"]
        current_avg = self.execution_stats["average_execution_time"]
        total_executions = self.execution_stats["total_executions"]

        self.execution_stats["average_execution_time"] = (
            (current_avg * (total_executions - 1) + total_time) / total_executions
        )

        # 更新步骤成功率
        for step_name in execution_result["completed_steps"]:
            current_rate = self.execution_stats["step_success_rates"][step_name]
            self.execution_stats["step_success_rates"][step_name] = (
                (current_rate * (total_executions - 1) + 1.0) / total_executions
            )

        # Update performance history
        if self.enable_performance_tracking:
            self._update_performance_history(execution_result)

    def _update_performance_history(self, execution_result: Dict[str, Any]) -> None:
        """更新性能历史记录"""
        performance_snapshot = {
            "timestamp": time.time(),
            "total_time": execution_result["total_time"],
            "success": execution_result["success"],
            "step_metrics": {}
        }

        # Collect step-level metrics
        for step_name in execution_result["completed_steps"] + execution_result["failed_steps"]:
            step = self.steps.get(step_name)
            if step and step.performance_metrics:
                performance_snapshot["step_metrics"][step_name] = {
                    "execution_time": step.execution_time,
                    "memory_delta": step.performance_metrics.memory_delta,
                    "peak_memory": step.performance_metrics.peak_memory,
                    "cpu_usage_before": step.performance_metrics.cpu_usage_before,
                    "cpu_usage_after": step.performance_metrics.cpu_usage_after
                }

        # Store in history (keep last 100 executions)
        with self._performance_lock:
            self.execution_stats["performance_history"].append(performance_snapshot)
            if len(self.execution_stats["performance_history"]) > 100:
                self.execution_stats["performance_history"].pop(0)

        # Identify bottleneck steps
        self._identify_bottlenecks()

    def _identify_bottlenecks(self) -> None:
        """识别性能瓶颈步骤"""
        if not self.execution_stats["performance_history"]:
            return

        # Analyze recent performance data
        recent_history = self.execution_stats["performance_history"][-10:]  # Last 10 executions
        step_times = defaultdict(list)

        for snapshot in recent_history:
            for step_name, metrics in snapshot["step_metrics"].items():
                step_times[step_name].append(metrics["execution_time"])

        # Find steps with consistently high execution times
        bottlenecks = []
        for step_name, times in step_times.items():
            if times and sum(times) / len(times) > 2.0:  # Average > 2 seconds
                bottlenecks.append({
                    "step_name": step_name,
                    "average_time": sum(times) / len(times),
                    "max_time": max(times),
                    "executions": len(times)
                })

        # Sort by average time
        bottlenecks.sort(key=lambda x: x["average_time"], reverse=True)

        with self._performance_lock:
            self.execution_stats["bottleneck_steps"] = bottlenecks[:5]  # Top 5 bottlenecks

    def get_stats(self) -> Dict[str, Any]:
        """获取执行统计 - Enhanced with performance data"""
        with self._performance_lock:
            return dict(self.execution_stats)

    def get_performance_report(self) -> Dict[str, Any]:
        """获取详细的性能报告"""
        if not self.enable_performance_tracking:
            return {"error": "Performance tracking is disabled"}

        with self._performance_lock:
            recent_history = self.execution_stats["performance_history"][-10:]

            if not recent_history:
                return {"error": "No performance data available"}

            # Calculate aggregate metrics
            total_times = [h["total_time"] for h in recent_history]
            success_rate = sum(1 for h in recent_history if h["success"]) / len(recent_history)

            return {
                "workflow_name": self.name,
                "recent_executions": len(recent_history),
                "average_total_time": sum(total_times) / len(total_times),
                "min_total_time": min(total_times),
                "max_total_time": max(total_times),
                "success_rate": success_rate,
                "bottleneck_steps": self.execution_stats["bottleneck_steps"],
                "optimization_suggestions": self.execution_stats["optimization_suggestions"][-10:],  # Last 10 suggestions
                "performance_trend": "improving" if len(total_times) >= 2 and total_times[-1] < total_times[0] else "stable"
            }

    def optimize(self) -> Dict[str, Any]:
        """优化工作流"""
        optimization_result: Dict[str, List[Any]] = {
            "removed_redundant_steps": [],
            "optimized_dependencies": [],
            "performance_improvements": []
        }

        # 移除从未成功执行的可选步骤
        steps_to_remove = []
        for step_name, success_rate in self.execution_stats["step_success_rates"].items():
            step = self.steps.get(step_name)
            if step and step.optional and success_rate < 0.1:  # 成功率低于10%
                steps_to_remove.append(step_name)

        for step_name in steps_to_remove:
            self.remove_step(step_name)
            optimization_result["removed_redundant_steps"].append(step_name)

        self.logger.info(f"工作流优化完成: {optimization_result}")
        return optimization_result


# 全局工作流管理器
_workflow_registry: Dict[str, WorkflowOptimizer] = {}


def create_workflow(name: str, enable_performance_tracking: bool = True) -> WorkflowOptimizer:
    """创建工作流 - Enhanced with performance tracking option"""
    if name in _workflow_registry:
        logger.warning(f"工作流 {name} 已存在，将被覆盖")

    workflow = WorkflowOptimizer(name, enable_performance_tracking)
    _workflow_registry[name] = workflow
    return workflow


def get_workflow_performance_report(name: str) -> Dict[str, Any]:
    """获取工作流性能报告"""
    workflow = _workflow_registry.get(name)
    if not workflow:
        return {"error": f"工作流 {name} 不存在"}

    return workflow.get_performance_report()


def get_all_workflow_performance() -> Dict[str, Any]:
    """获取所有工作流的性能概览"""
    performance_overview = {
        "total_workflows": len(_workflow_registry),
        "workflows": {}
    }

    for name, workflow in _workflow_registry.items():
        try:
            performance_overview["workflows"][name] = workflow.get_performance_report()
        except Exception as e:
            performance_overview["workflows"][name] = {"error": str(e)}

    return performance_overview


def get_workflow(name: str) -> Optional[WorkflowOptimizer]:
    """获取工作流"""
    return _workflow_registry.get(name)


def execute_workflow(name: str, **kwargs: Any) -> Dict[str, Any]:
    """执行工作流"""
    workflow = _workflow_registry.get(name)
    if not workflow:
        raise ValueError(f"工作流 {name} 不存在")

    return workflow.execute(**kwargs)


def optimize_all_workflows() -> Dict[str, Any]:
    """优化所有工作流"""
    results = {}
    for name, workflow in _workflow_registry.items():
        try:
            results[name] = workflow.optimize()
        except Exception as e:
            logger.error(f"优化工作流 {name} 失败: {e}")
            results[name] = {"error": str(e)}

    return results
