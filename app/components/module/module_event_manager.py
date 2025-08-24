"""
Module Event Manager
Handles all module-related events and signals
"""

from PySide6.QtCore import QObject, Signal


class ModuleEventManager(QObject):
    """模块事件管理器"""
    module_loaded = Signal(str)
    module_unloaded = Signal(str)
    module_error = Signal(str, str)
    performance_updated = Signal(str, dict)
    validation_completed = Signal(str, bool, list)

    def __init__(self, parent=None):
        super().__init__(parent)

    def emit_module_loaded(self, module_name: str):
        """发出模块加载信号"""
        self.module_loaded.emit(module_name)

    def emit_module_unloaded(self, module_name: str):
        """发出模块卸载信号"""
        self.module_unloaded.emit(module_name)

    def emit_module_error(self, module_name: str, error_message: str):
        """发出模块错误信号"""
        self.module_error.emit(module_name, error_message)

    def emit_performance_updated(self, module_name: str, metrics: dict):
        """发出性能更新信号"""
        self.performance_updated.emit(module_name, metrics)

    def emit_validation_completed(self, module_name: str, success: bool, issues: list):
        """发出验证完成信号"""
        self.validation_completed.emit(module_name, success, issues)
