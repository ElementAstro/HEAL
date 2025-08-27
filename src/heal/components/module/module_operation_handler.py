"""
Module Operation Handler
Handles module operations like load, unload, reload, validate
"""

import threading
import time
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Signal

from src.heal.common.logging_config import get_logger
from .module_config_manager import ModuleConfigManager
from .module_event_manager import ModuleEventManager
from .module_metrics_manager import ModuleMetricsManager
from .module_models import ModuleConfig, ModuleMetrics, ModuleState


class ModuleOperationHandler(QObject):
    """模块操作处理器"""

    # 信号
    # operation, module_name, success
    operation_completed = Signal(str, str, bool)
    state_changed = Signal(str, str)  # module_name, new_state

    def __init__(
        self,
        event_manager: ModuleEventManager,
        config_manager: ModuleConfigManager,
        metrics_manager: ModuleMetricsManager,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)

        self.logger = get_logger(
            "module_operation_handler", module="ModuleOperationHandler"
        )
        self.event_manager = event_manager
        self.config_manager = config_manager
        self.metrics_manager = metrics_manager

        # 操作队列 - 添加线程安全保护
        self.operation_queue: List[Dict[str, Any]] = []
        self.is_processing = False
        self._queue_lock = threading.Lock()  # 队列操作锁
        self._processing_lock = threading.Lock()  # 处理状态锁

        # 模块状态跟踪
        self.module_states: Dict[str, ModuleState] = {}
        self._state_lock = threading.Lock()  # 状态操作锁

    def handle_operation(self, operation: str, module_name: str, **kwargs: Any) -> None:
        """处理模块操作请求 - 线程安全版本"""
        try:
            self.logger.info(f"处理操作请求: {operation} for {module_name}")

            # 线程安全地添加到操作队列
            operation_data = {
                "operation": operation,
                "module_name": module_name,
                "timestamp": time.time(),
                "kwargs": kwargs,
            }

            with self._queue_lock:
                self.operation_queue.append(operation_data)

            # 线程安全地检查并开始处理
            with self._processing_lock:
                if not self.is_processing:
                    self._process_queue()

        except Exception as e:
            self.logger.error(f"处理操作请求失败: {e}")

    def _process_queue(self) -> None:
        """处理操作队列 - 线程安全版本"""
        # 检查是否需要处理（在锁外进行初步检查以提高性能）
        with self._queue_lock:
            if not self.operation_queue:
                return

        with self._processing_lock:
            if self.is_processing:
                return
            self.is_processing = True

        try:
            while True:
                # 线程安全地获取下一个操作
                with self._queue_lock:
                    if not self.operation_queue:
                        break
                    operation_data = self.operation_queue.pop(0)

                # 执行操作（在锁外执行以避免长时间持有锁）
                self._execute_operation(operation_data)

        finally:
            with self._processing_lock:
                self.is_processing = False

    def _execute_operation(self, operation_data: Dict[str, Any]) -> None:
        """执行单个操作"""
        operation = operation_data["operation"]
        module_name = operation_data["module_name"]
        kwargs = operation_data.get("kwargs", {})

        success = False
        start_time = time.time()

        try:
            if operation == "load":
                success = self._load_module(module_name, **kwargs)
            elif operation == "unload":
                success = self._unload_module(module_name, **kwargs)
            elif operation == "reload":
                success = self._reload_module(module_name, **kwargs)
            elif operation == "validate":
                success = self._validate_module(module_name, **kwargs)
            else:
                self.logger.warning(f"未知操作: {operation}")

        except Exception as e:
            self.logger.error(f"执行操作 {operation} 失败: {e}")
            self.metrics_manager.record_error(module_name, str(e))

        finally:
            # 记录操作时间和结果
            execution_time = time.time() - start_time
            self.metrics_manager.record_operation(module_name, success)

            # 发出完成信号
            self.operation_completed.emit(operation, module_name, success)

    def _load_module(self, module_name: str, force: bool = False) -> bool:
        """加载模块"""
        try:
            start_time = time.time()

            # 检查模块是否已加载（除非强制加载）
            current_state = self.module_states.get(
                module_name, ModuleState.IDLE)
            if current_state == ModuleState.LOADED and not force:
                self.logger.info(f"模块 {module_name} 已加载，跳过")
                return True

            # 更新状态
            self._update_module_state(module_name, ModuleState.LOADING)

            # 获取配置
            config = self.config_manager.get_config(module_name)
            if not config:
                self.logger.warning(f"模块 {module_name} 配置不存在，使用默认配置")
                config = ModuleConfig(name=module_name)
                self.config_manager.add_config(config)

            # 模拟加载过程（实际实现中应该调用真正的模块加载逻辑）
            time.sleep(0.1)  # 模拟加载时间

            # 记录加载时间
            load_time = time.time() - start_time
            self.metrics_manager.record_load_time(module_name, load_time)

            # 更新状态
            self._update_module_state(module_name, ModuleState.LOADED)

            # 发出事件
            self.event_manager.emit_module_loaded(module_name)

            self.logger.info(f"模块 {module_name} 加载成功，耗时 {load_time:.3f}s")
            return True

        except Exception as e:
            self.logger.error(f"加载模块 {module_name} 失败: {e}")
            self._update_module_state(module_name, ModuleState.ERROR)
            self.event_manager.emit_module_error(module_name, str(e))
            return False

    def _unload_module(self, module_name: str, **kwargs: Any) -> bool:
        """卸载模块"""
        try:
            # 检查模块状态
            current_state = self.module_states.get(
                module_name, ModuleState.IDLE)
            if current_state == ModuleState.IDLE:
                self.logger.info(f"模块 {module_name} 未加载，无需卸载")
                return True

            # 模拟卸载过程
            time.sleep(0.05)

            # 更新状态
            self._update_module_state(module_name, ModuleState.IDLE)

            # 发出事件
            self.event_manager.emit_module_unloaded(module_name)

            self.logger.info(f"模块 {module_name} 卸载成功")
            return True

        except Exception as e:
            self.logger.error(f"卸载模块 {module_name} 失败: {e}")
            self._update_module_state(module_name, ModuleState.ERROR)
            self.event_manager.emit_module_error(module_name, str(e))
            return False

    def _reload_module(self, module_name: str, **kwargs: Any) -> bool:
        """重新加载模块"""
        try:
            # 先卸载再加载
            if self._unload_module(module_name):
                return self._load_module(module_name, force=True)
            return False

        except Exception as e:
            self.logger.error(f"重新加载模块 {module_name} 失败: {e}")
            return False

    def _validate_module(self, module_name: str, **kwargs: Any) -> bool:
        """验证模块"""
        try:
            # 获取配置
            config = self.config_manager.get_config(module_name)
            if not config or not config.validation_enabled:
                self.logger.info(f"模块 {module_name} 验证已禁用")
                return True

            # 模拟验证过程
            time.sleep(0.1)

            # 模拟验证结果
            validation_issues: List[Dict[str, Any]] = (
                []
            )  # 实际实现中应该包含真正的验证逻辑
            success = len(validation_issues) == 0

            # 发出验证完成事件
            self.event_manager.emit_validation_completed(
                module_name, success, validation_issues
            )

            self.logger.info(f"模块 {module_name} 验证{'成功' if success else '失败'}")
            return success

        except Exception as e:
            self.logger.error(f"验证模块 {module_name} 失败: {e}")
            self.event_manager.emit_module_error(module_name, str(e))
            return False

    def _update_module_state(self, module_name: str, new_state: ModuleState) -> None:
        """更新模块状态 - 线程安全版本"""
        with self._state_lock:
            old_state = self.module_states.get(module_name, ModuleState.IDLE)
            self.module_states[module_name] = new_state

            if old_state != new_state:
                self.logger.debug(
                    f"模块 {module_name} 状态变更: {old_state.value} -> {new_state.value}"
                )
                # 信号发射在锁外进行，避免潜在的死锁

        # 在锁外发射信号
        if old_state != new_state:
            self.state_changed.emit(module_name, new_state.value)

    def get_module_state(self, module_name: str) -> ModuleState:
        """获取模块状态 - 线程安全版本"""
        with self._state_lock:
            return self.module_states.get(module_name, ModuleState.IDLE)

    def get_all_module_states(self) -> Dict[str, ModuleState]:
        """获取所有模块状态 - 线程安全版本"""
        with self._state_lock:
            return self.module_states.copy()

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态 - 线程安全版本"""
        with self._queue_lock:
            queue_length = len(self.operation_queue)
            pending_operations = [
                {
                    "operation": op["operation"],
                    "module_name": op["module_name"],
                    "timestamp": op["timestamp"],
                }
                for op in self.operation_queue
            ]

        with self._processing_lock:
            is_processing = self.is_processing

        return {
            "queue_length": queue_length,
            "is_processing": is_processing,
            "pending_operations": pending_operations,
        }
