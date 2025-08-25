"""
Module Metrics Manager
Handles performance metrics collection and management for modules
"""

import time
from typing import Any, Dict, Optional

from src.heal.common.logging_config import get_logger
from .module_models import ModuleMetrics


class ModuleMetricsManager:
    """模块性能指标管理器"""

    def __init__(self) -> None:
        self.logger = get_logger(
            "module_metrics_manager", module="ModuleMetricsManager"
        )
        self.module_metrics: Dict[str, ModuleMetrics] = {}

    def initialize_metrics(self, module_name: str) -> ModuleMetrics:
        """初始化模块指标"""
        if module_name not in self.module_metrics:
            self.module_metrics[module_name] = ModuleMetrics()
        return self.module_metrics[module_name]

    def update_metrics(self, module_name: str, **kwargs) -> bool:
        """更新模块指标"""
        try:
            if module_name not in self.module_metrics:
                self.initialize_metrics(module_name)

            metrics = self.module_metrics[module_name]

            for key, value in kwargs.items():
                if hasattr(metrics, key):
                    setattr(metrics, key, value)
                else:
                    self.logger.warning(f"未知的指标属性: {key}")

            return True
        except Exception as e:
            self.logger.error(f"更新模块指标失败: {e}")
            return False

    def record_operation(self, module_name: str, success: bool = True) -> None:
        """记录操作"""
        try:
            metrics = self.initialize_metrics(module_name)
            metrics.operations_count += 1

            if not success:
                metrics.error_count += 1

            # 计算成功率
            if metrics.operations_count > 0:
                success_count = metrics.operations_count - metrics.error_count
                metrics.success_rate = (success_count / metrics.operations_count) * 100

        except Exception as e:
            self.logger.error(f"记录操作失败: {e}")

    def record_error(self, module_name: str, error_message: str) -> None:
        """记录错误"""
        try:
            metrics = self.initialize_metrics(module_name)
            metrics.error_count += 1
            metrics.last_error = error_message

            # 重新计算成功率
            if metrics.operations_count > 0:
                success_count = metrics.operations_count - metrics.error_count
                metrics.success_rate = (success_count / metrics.operations_count) * 100

        except Exception as e:
            self.logger.error(f"记录错误失败: {e}")

    def record_load_time(self, module_name: str, load_time: float) -> None:
        """记录加载时间"""
        self.update_metrics(module_name, load_time=load_time)

    def update_resource_usage(
        self, module_name: str, cpu_usage: float = 0.0, memory_usage: float = 0.0
    ):
        """更新资源使用情况"""
        self.update_metrics(module_name, cpu_usage=cpu_usage, memory_usage=memory_usage)

    def get_metrics(self, module_name: str) -> Optional[ModuleMetrics]:
        """获取模块性能指标"""
        return self.module_metrics.get(module_name)

    def get_all_metrics(self) -> Dict[str, ModuleMetrics]:
        """获取所有模块性能指标"""
        return self.module_metrics.copy()

    def reset_metrics(self, module_name: str) -> bool:
        """重置模块指标"""
        try:
            if module_name in self.module_metrics:
                self.module_metrics[module_name] = ModuleMetrics()
                return True
            return False
        except Exception as e:
            self.logger.error(f"重置模块指标失败: {e}")
            return False

    def export_metrics(self, filepath: str) -> bool:
        """导出性能指标"""
        try:
            import json

            data: Dict[str, Any] = {"timestamp": time.time(), "metrics": {}}

            for name, metrics in self.module_metrics.items():
                data["metrics"][name] = {
                    "load_time": metrics.load_time,
                    "memory_usage": metrics.memory_usage,
                    "cpu_usage": metrics.cpu_usage,
                    "error_count": metrics.error_count,
                    "operations_count": metrics.operations_count,
                    "success_rate": metrics.success_rate,
                    "last_error": metrics.last_error,
                }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"性能指标已导出到: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"导出性能指标失败: {e}")
            return False

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        total_modules = len(self.module_metrics)
        total_operations = sum(m.operations_count for m in self.module_metrics.values())
        total_errors = sum(m.error_count for m in self.module_metrics.values())
        avg_success_rate = (
            sum(m.success_rate for m in self.module_metrics.values()) / total_modules
            if total_modules > 0
            else 100.0
        )

        return {
            "total_modules": total_modules,
            "total_operations": total_operations,
            "total_errors": total_errors,
            "average_success_rate": avg_success_rate,
            "modules_with_errors": len(
                [m for m in self.module_metrics.values() if m.error_count > 0]
            ),
        }
