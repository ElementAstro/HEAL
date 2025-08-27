"""
Workflow Optimizer - 工作流优化工具
简化复杂的初始化流程和操作序列
"""

import time
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
class WorkflowStep:
    """工作流步骤"""
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

    def reset(self) -> None:
        """重置步骤状态"""
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None
        self.execution_time = 0.0


class WorkflowOptimizer:
    """工作流优化器 - 简化复杂的操作序列"""

    def __init__(self, name: str) -> None:
        self.name = name
        self.steps: Dict[str, WorkflowStep] = {}
        self.execution_order: List[str] = []
        self.logger = logger.bind(component="WorkflowOptimizer", workflow=name)

        # 执行统计
        self.execution_stats: Dict[str, Any] = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "step_success_rates": defaultdict(float)
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
        """执行单个步骤"""
        step.status = StepStatus.RUNNING
        start_time = time.time()

        try:
            self.logger.debug(f"执行步骤: {step.name}")
            step.result = step.func()
            step.status = StepStatus.COMPLETED
            step.execution_time = time.time() - start_time

            self.logger.debug(
                f"步骤 {step.name} 执行成功，耗时 {step.execution_time:.3f}s")
            return True

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = e
            step.execution_time = time.time() - start_time

            self.logger.error(f"步骤 {step.name} 执行失败: {e}")
            return False

    def _update_stats(self, execution_result: Dict[str, Any]) -> None:
        """更新执行统计"""
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

    def get_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        return dict(self.execution_stats)

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


def create_workflow(name: str) -> WorkflowOptimizer:
    """创建工作流"""
    if name in _workflow_registry:
        logger.warning(f"工作流 {name} 已存在，将被覆盖")

    workflow = WorkflowOptimizer(name)
    _workflow_registry[name] = workflow
    return workflow


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
