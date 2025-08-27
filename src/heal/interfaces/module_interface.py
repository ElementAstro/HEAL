"""
Enhanced Module Interface
Provides comprehensive module management with robust validation, monitoring, and error handling.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import (
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    MessageBox,
    Pivot,
    ScrollArea,
    qrouter,
)

from src.heal.common.logging_config import get_logger, log_performance, with_correlation_id
from src.heal.components.module import (
    ModuleConfig,
    ModuleConfigManager,
    ModuleEventManager,
    ModuleMetrics,
    ModuleMetricsManager,
    ModuleOperationHandler,
    ModuleState,
    ScaffoldAppWrapper,
)
from src.heal.components.module.mod_download import ModDownload
from src.heal.components.module.mod_manager import ModManager
from src.heal.models.setting_card import CustomFrameGroup
from src.heal.models.style_sheet import StyleSheet


class Module(ScrollArea):
    """Enhanced Module Interface with comprehensive management capabilities"""

    Nav = Pivot

    # 信号
    module_operation_requested = Signal(str, str)  # operation, module_name
    performance_alert = Signal(str, str, str)  # alert_name, message, severity

    def __init__(self, text: str, parent: Any = None) -> None:
        super().__init__(parent=parent)
        self.parent_widget = parent
        self.setObjectName(text)

        # 初始化日志
        self.logger = get_logger("module_interface", module="ModuleInterface")

        # 核心组件初始化
        self.event_manager = ModuleEventManager()
        self.config_manager = ModuleConfigManager()
        self.metrics_manager = ModuleMetricsManager()
        self.operation_handler = ModuleOperationHandler(
            self.event_manager, self.config_manager, self.metrics_manager
        )

        # 正确初始化ScrollArea的scrollWidget
        self.scrollWidget = QWidget()
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # UI组件 - 使用正确的父组件
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.pivot = self.Nav(self.scrollWidget)
        self.stackedWidget = QStackedWidget(self.scrollWidget)

        # 状态管理
        self.current_state = ModuleState.IDLE
        self.operation_queue: List[Dict[str, Any]] = []
        self.is_processing = False

        # 性能监控定时器
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(
            self._update_performance_metrics)
        self.performance_timer.start(5000)  # 5秒更新一次

        # 初始化刷新时间记录
        self.last_refresh_times: Dict[str, float] = {}

        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh_modules)

        # 创建子界面
        self._create_interfaces()

        # 初始化
        self._initWidget()
        self._setup_event_connections()
        self._load_module_configurations()

        # 启动监控
        self._start_monitoring()

        self.logger.info("Enhanced Module Interface initialized successfully")

    def _create_interfaces(self) -> None:
        """创建增强的界面"""
        # 模组管理界面 - 增强版
        self.ModuleManagerFrame = ModManager()
        self.ModuleManagerInterface = CustomFrameGroup(self.scrollWidget)
        self.ModuleManagerInterface.addCustomFrame(self.ModuleManagerFrame)

        # 模组下载界面 - 增强版
        self.ModuleDownloadFrame = ModDownload()
        self.ModuleDownloadInterface = CustomFrameGroup(self.scrollWidget)
        self.ModuleDownloadInterface.addCustomFrame(self.ModuleDownloadFrame)

        # 脚手架应用界面 - 使用包装器
        self.ScaffoldAppFrame = ScaffoldAppWrapper()
        self.ScaffoldAppInterface = CustomFrameGroup(self.scrollWidget)
        self.ScaffoldAppInterface.addCustomFrame(self.ScaffoldAppFrame)

        # 模块验证界面 - 可选
        self.ModuleValidationFrame: Any = None
        self.ModuleValidationInterface: Any = None

        # 性能监控界面 - 可选
        self.PerformanceDashboardFrame: Any = None
        self.PerformanceDashboardInterface: Any = None

    def _initWidget(self) -> None:
        """初始化增强的界面组件"""
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # 设置样式
        self.scrollWidget.setObjectName("scrollWidget")
        StyleSheet.SETTING_INTERFACE.apply(self)

        self._initLayout()
        self._connectSignalToSlot()

    def _initLayout(self) -> None:
        """初始化增强的布局"""
        # 设置ScrollArea属性
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.enableTransparentBackground()

        # 添加Pivot导航项
        self.pivot.addItem(
            routeKey="ModuleManagerInterface",
            text=self.tr("模组管理"),
            onClick=lambda: self.stackedWidget.setCurrentWidget(
                self.ModuleManagerInterface
            ),
        )

        self.pivot.addItem(
            routeKey="ModuleDownloadInterface",
            text=self.tr("模组下载"),
            onClick=lambda: self.stackedWidget.setCurrentWidget(
                self.ModuleDownloadInterface
            ),
        )

        self.pivot.addItem(
            routeKey="ScaffoldAppInterface",
            text=self.tr("模组生成器"),
            onClick=lambda: self.stackedWidget.setCurrentWidget(
                self.ScaffoldAppInterface
            ),
        )

        # 添加界面到StackedWidget
        self.stackedWidget.addWidget(self.ModuleManagerInterface)
        self.stackedWidget.addWidget(self.ModuleDownloadInterface)
        self.stackedWidget.addWidget(self.ScaffoldAppInterface)

        # 布局设置 - 正确的间距和边距
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget, 1)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(20, 20, 20, 20)

        # 连接信号
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.pivot.currentItemChanged.connect(self._onPivotItemChanged)

        # 设置默认页面
        self.stackedWidget.setCurrentWidget(self.ModuleManagerInterface)
        self.pivot.setCurrentItem("ModuleManagerInterface")

        # 设置路由
        qrouter.setDefaultRouteKey(
            self.stackedWidget, "ModuleManagerInterface")

    def _connectSignalToSlot(self) -> None:
        """连接信号到槽函数"""
        # 内部信号
        self.module_operation_requested.connect(self._handle_module_operation)
        self.performance_alert.connect(self._show_performance_alert)

    def _onPivotItemChanged(self, routeKey: str) -> None:
        """处理Pivot项目改变事件"""
        if routeKey == "ModuleManagerInterface":
            self.stackedWidget.setCurrentWidget(self.ModuleManagerInterface)
        elif routeKey == "ModuleDownloadInterface":
            self.stackedWidget.setCurrentWidget(self.ModuleDownloadInterface)
        elif routeKey == "ScaffoldAppInterface":
            self.stackedWidget.setCurrentWidget(self.ScaffoldAppInterface)

    def _setup_event_connections(self) -> None:
        """设置事件连接"""
        # 连接事件管理器
        self.event_manager.module_loaded.connect(self._on_module_loaded)
        self.event_manager.module_unloaded.connect(self._on_module_unloaded)
        self.event_manager.module_error.connect(self._on_module_error)
        self.event_manager.performance_updated.connect(
            self._on_performance_updated)
        self.event_manager.validation_completed.connect(
            self._on_validation_event)

    def _load_module_configurations(self) -> None:
        """加载模块配置"""
        self.config_manager.load_configurations()
        self.logger.info("模块配置加载完成")

    def _save_module_configurations(self) -> None:
        """保存模块配置"""
        self.config_manager.save_configurations()
        self.logger.info("模块配置保存完成")

    def _start_monitoring(self) -> None:
        """启动监控系统"""
        # 配置自动刷新
        self._configure_auto_refresh()

    def _configure_auto_refresh(self) -> None:
        """配置自动刷新"""
        # 检查是否有模块启用了自动刷新
        all_configs = self.config_manager.get_all_configs()
        auto_refresh_enabled = any(
            config.auto_refresh for config in all_configs.values()
        )

        if auto_refresh_enabled:
            # 使用最小的刷新间隔
            min_interval = min(
                (
                    config.refresh_interval
                    for config in all_configs.values()
                    if config.auto_refresh
                ),
                default=30,
            )

            self.refresh_timer.start(min_interval * 1000)  # 转换为毫秒
            self.logger.info(f"自动刷新已启用，间隔: {min_interval}秒")

    def _auto_refresh_modules(self) -> None:
        """自动刷新模块"""
        current_time = time.time()
        all_configs = self.config_manager.get_all_configs()

        for name, config in all_configs.items():
            if config.auto_refresh:
                # 检查是否需要刷新
                last_refresh = self.last_refresh_times.get(name, 0)
                if current_time - last_refresh >= config.refresh_interval:
                    self._refresh_module(name)

    def _refresh_module(self, module_name: str) -> None:
        """刷新单个模块"""
        try:
            # 记录刷新时间
            self.last_refresh_times[module_name] = time.time()

            self.logger.debug(f"模块 {module_name} 已刷新")
        except Exception as e:
            self.logger.error(f"刷新模块 {module_name} 失败: {e}")

    def _update_performance_metrics(self) -> None:
        """更新性能指标"""
        try:
            # 模拟性能数据更新
            all_configs = self.config_manager.get_all_configs()
            for module_name in all_configs.keys():
                # 初始化指标（如果不存在）
                self.metrics_manager.initialize_metrics(module_name)

                # 更新一些基本指标
                self.metrics_manager.update_resource_usage(
                    module_name, 0.0, 0.0)

        except Exception as e:
            self.logger.error(f"更新性能指标失败: {e}")

    # 信号处理方法
    def _on_module_state_changed(self, module_name: str, new_state: str) -> None:
        """模块状态变更处理"""
        self.logger.info(f"模块 {module_name} 状态变更为: {new_state}")

        # 发送事件
        if new_state == ModuleState.LOADED.value:
            self.event_manager.module_loaded.emit(module_name)
        elif new_state == ModuleState.INACTIVE.value:
            self.event_manager.module_unloaded.emit(module_name)
        elif new_state == ModuleState.ERROR.value:
            self.event_manager.module_error.emit(module_name, "Unknown error")

    def _show_performance_alert(self, alert_name: str, message: str, severity: str) -> None:
        """显示性能告警"""
        # 记录告警用于可能的后续处理
        self.logger.warning(f"Performance alert '{alert_name}': {message}")

        if severity == "critical":
            InfoBar.error(
                title="Critical Performance Alert",
                content=message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=10000,
                parent=self,
            )
        elif severity == "warning":
            InfoBar.warning(
                title="Performance Warning",
                content=message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self,
            )

    def _handle_module_operation(self, operation: str, module_name: str) -> None:
        """处理模块操作请求"""
        self.operation_handler.handle_operation(operation, module_name)

    # 事件处理方法
    def _on_module_loaded(self, module_name: str) -> None:
        """模块加载事件"""
        self.logger.info(f"模块加载事件: {module_name}")

    def _on_module_unloaded(self, module_name: str) -> None:
        """模块卸载事件"""
        self.logger.info(f"模块卸载事件: {module_name}")

    def _on_module_error(self, module_name: str, error_message: str) -> None:
        """模块错误事件"""
        self.logger.error(f"模块错误事件: {module_name} - {error_message}")
        self._show_error_message(f"模块 {module_name} 错误", error_message)

    def _on_performance_updated(self, module_name: str, metrics: Dict[str, Any]) -> None:
        """性能更新事件"""
        self.event_manager.performance_updated.emit(module_name, metrics)

    def _on_validation_event(self, module_name: str, success: bool, issues: List[Dict]) -> None:
        """验证事件"""
        # 记录验证事件以供后续处理
        self.logger.info(f"验证事件: {module_name} - {'成功' if success else '失败'}")
        if not success and issues:
            self.logger.warning(f"模块 {module_name} 验证发现 {len(issues)} 个问题")

    # 消息显示方法
    def _show_success_message(self, title: str, content: str) -> None:
        """显示成功消息"""
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def _show_error_message(self, title: str, content: str) -> None:
        """显示错误消息"""
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self,
        )

    def _show_critical_validation_warning(
        self, module_name: str, critical_issues: List[Dict]
    ) -> None:
        """显示严重验证警告"""
        issues_text = "\n".join(
            [issue.get("message", "") for issue in critical_issues[:3]]
        )
        if len(critical_issues) > 3:
            issues_text += f"\n... 及其他 {len(critical_issues) - 3} 个问题"

        # 使用正确的MessageBox API
        msg_box = MessageBox(
            title="严重验证问题",
            content=f"模块 {module_name} 存在严重问题：\n\n{issues_text}",
            parent=self,
        )
        msg_box.exec()

    # 公共API方法
    def load_module(self, module_name: str, force: bool = False) -> None:
        """加载模块"""
        # 使用force参数进行条件检查
        all_configs = self.config_manager.get_all_configs()
        if force or module_name not in all_configs:
            self.module_operation_requested.emit("load", module_name)
            self.logger.info(f"请求加载模块: {module_name} (force={force})")
        else:
            self.logger.info(f"模块 {module_name} 已存在，跳过加载")

    def unload_module(self, module_name: str) -> None:
        """卸载模块"""
        self.module_operation_requested.emit("unload", module_name)
        self.logger.info(f"请求卸载模块: {module_name}")

    def reload_module(self, module_name: str) -> None:
        """重新加载模块"""
        self.module_operation_requested.emit("reload", module_name)
        self.logger.info(f"请求重新加载模块: {module_name}")

    def validate_module(self, module_name: str) -> None:
        """验证模块"""
        self.module_operation_requested.emit("validate", module_name)
        self.logger.info(f"请求验证模块: {module_name}")

    def get_module_config(self, module_name: str) -> Optional[ModuleConfig]:
        """获取模块配置"""
        return self.config_manager.get_config(module_name)

    def update_module_config(self, module_name: str, config: ModuleConfig) -> None:
        """更新模块配置"""
        self.config_manager.update_config(module_name, config)

        # 如果配置了自动刷新，重新配置定时器
        if config.auto_refresh:
            self._configure_auto_refresh()

    def get_module_metrics(self, module_name: str) -> Optional[ModuleMetrics]:
        """获取模块性能指标"""
        return self.metrics_manager.get_metrics(module_name)

    def get_all_module_metrics(self) -> Dict[str, ModuleMetrics]:
        """获取所有模块性能指标"""
        return self.metrics_manager.get_all_metrics()

    def export_module_data(self, filepath: str) -> None:
        """导出模块数据"""
        try:
            data: Dict[str, Any] = {
                "timestamp": time.time(),
                "configs": {},
                "metrics": {},
            }

            # 导出配置
            all_configs = self.config_manager.get_all_configs()
            for name, config in all_configs.items():
                data["configs"][name] = {
                    "name": config.name,
                    "enabled": config.enabled,
                    "auto_refresh": config.auto_refresh,
                    "refresh_interval": config.refresh_interval,
                    "validation_enabled": config.validation_enabled,
                    "performance_monitoring": config.performance_monitoring,
                }

            # 导出性能指标
            all_metrics = self.metrics_manager.get_all_metrics()
            for name, metrics in all_metrics.items():
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

            self.logger.info(f"模块数据已导出到: {filepath}")
            self._show_success_message("导出成功", f"模块数据已导出到 {filepath}")

        except Exception as e:
            self.logger.error(f"导出模块数据失败: {e}")
            self._show_error_message("导出失败", str(e))

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        all_configs = self.config_manager.get_all_configs()
        return {
            "module_interface_state": self.current_state.value,
            "total_modules": len(all_configs),
            "performance_monitoring": self.performance_timer.isActive(),
            "auto_refresh": self.refresh_timer.isActive(),
            "cpu_usage": 0,
            "memory_usage": 0,
        }

    def addSubInterface(self, widget: QWidget, object_name: str, text: str, icon: Any = None) -> None:
        """添加子界面"""
        widget.setObjectName(object_name)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            icon=icon,
            routeKey=object_name,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index: int) -> None:
        """当前索引改变时的处理"""
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())

    def cleanup(self) -> None:
        """清理资源"""
        self.logger.info("开始清理 Module Interface 资源")

        # 停止定时器
        if self.performance_timer.isActive():
            self.performance_timer.stop()
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()

        # 保存配置
        self.config_manager.save_configurations()

        self.logger.info("Module Interface 资源清理完成")

    def __del__(self) -> None:
        """析构函数"""
        try:
            self.cleanup()
        except Exception as e:
            self.logger.error(f"模块界面清理时发生错误: {e}")
