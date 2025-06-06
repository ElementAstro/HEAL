"""
Enhanced Module Interface
Provides comprehensive module management with robust validation, monitoring, and error handling.
"""

import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QFrame
from PySide6.QtCore import Qt, QTimer, QObject, Signal
from qfluentwidgets import (
    Pivot, qrouter, ScrollArea, FluentIcon, InfoBar, InfoBarPosition,
    MessageBox
)

from app.model.style_sheet import StyleSheet
from app.model.setting_card import CustomFrameGroup
from loguru import logger

from app.components.module.mod_manager import ModManager
from app.components.module.mod_download import ModDownload
from app.components.tools.scaffold import ScaffoldApp


class ModuleState(Enum):
    """模块状态枚举"""
    IDLE = "idle"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UPDATING = "updating"


@dataclass
class ModuleMetrics:
    """模块性能指标"""
    load_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    operations_count: int = 0
    success_rate: float = 100.0


@dataclass
class ModuleConfig:
    """模块配置"""
    name: str
    enabled: bool = True
    auto_refresh: bool = True
    refresh_interval: int = 30  # seconds
    max_retries: int = 3
    timeout: int = 10  # seconds
    validation_enabled: bool = True
    performance_monitoring: bool = True
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class ModuleEventManager(QObject):
    """模块事件管理器"""
    module_loaded = Signal(str)
    module_unloaded = Signal(str)
    module_error = Signal(str, str)
    performance_updated = Signal(str, dict)
    validation_completed = Signal(str, bool, list)


class ScaffoldAppWrapper(QFrame):
    """ScaffoldApp包装器，使其兼容QFrame"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scaffold_app = ScaffoldApp()
        layout.addWidget(self.scaffold_app)


class Module(ScrollArea):
    """Enhanced Module Interface with comprehensive management capabilities"""

    Nav = Pivot

    # 信号
    module_operation_requested = Signal(str, str)  # operation, module_name
    performance_alert = Signal(str, str, str)  # alert_name, message, severity

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.parent_widget = parent
        self.setObjectName(text)

        # 初始化日志
        self.logger = logger.bind(component="ModuleInterface")

        # 核心组件初始化
        self.event_manager = ModuleEventManager()

        # 模块配置
        self.module_configs: Dict[str, ModuleConfig] = {}
        self.module_metrics: Dict[str, ModuleMetrics] = {}

        # UI组件
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

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
        self.last_refresh_times = {}

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

    def _create_interfaces(self):
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
        self.ModuleValidationFrame = None
        self.ModuleValidationInterface = None

        # 性能监控界面 - 可选
        self.PerformanceDashboardFrame = None
        self.PerformanceDashboardInterface = None

    def _initWidget(self):
        """初始化增强的界面组件"""
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # 设置样式
        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self._initLayout()
        self._connectSignalToSlot()

    def _initLayout(self):
        """初始化增强的布局"""
        # 核心界面
        self.addSubInterface(
            self.ModuleManagerInterface,
            'ModuleManagerInterface',
            self.tr('模组管理'),
            icon=FluentIcon.IOT
        )

        self.addSubInterface(
            self.ModuleDownloadInterface,
            'ModuleDownloadInterface',
            self.tr('模组下载'),
            icon=FluentIcon.DOWNLOAD
        )

        self.addSubInterface(
            self.ScaffoldAppInterface,
            'ScaffoldAppInterface',
            self.tr('模组生成器'),
            icon=FluentIcon.IOT
        )

        # 布局设置
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)

        # 连接信号
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.ModuleManagerInterface)
        self.pivot.setCurrentItem(self.ModuleManagerInterface.objectName())
        qrouter.setDefaultRouteKey(
            self.stackedWidget,
            self.ModuleManagerInterface.objectName()
        )

    def _connectSignalToSlot(self):
        """连接信号到槽函数"""
        # 内部信号
        self.module_operation_requested.connect(self._handle_module_operation)
        self.performance_alert.connect(self._show_performance_alert)

    def _setup_event_connections(self):
        """设置事件连接"""
        # 连接事件管理器
        self.event_manager.module_loaded.connect(self._on_module_loaded)
        self.event_manager.module_unloaded.connect(self._on_module_unloaded)
        self.event_manager.module_error.connect(self._on_module_error)
        self.event_manager.performance_updated.connect(
            self._on_performance_updated)
        self.event_manager.validation_completed.connect(
            self._on_validation_event)

    def _load_module_configurations(self):
        """加载模块配置"""
        try:
            config_path = Path("config/module_configs.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                for name, config in config_data.items():
                    self.module_configs[name] = ModuleConfig(**config)

                self.logger.info(f"已加载 {len(self.module_configs)} 个模块配置")
        except Exception as e:
            self.logger.error(f"加载模块配置失败: {e}")

    def _save_module_configurations(self):
        """保存模块配置"""
        try:
            config_path = Path("config/module_configs.json")
            config_path.parent.mkdir(exist_ok=True)

            config_data = {}
            for name, config in self.module_configs.items():
                config_data[name] = {
                    'name': config.name,
                    'enabled': config.enabled,
                    'auto_refresh': config.auto_refresh,
                    'refresh_interval': config.refresh_interval,
                    'max_retries': config.max_retries,
                    'timeout': config.timeout,
                    'validation_enabled': config.validation_enabled,
                    'performance_monitoring': config.performance_monitoring,
                    'custom_settings': config.custom_settings
                }

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.logger.info("模块配置已保存")
        except Exception as e:
            self.logger.error(f"保存模块配置失败: {e}")

    def _start_monitoring(self):
        """启动监控系统"""
        # 配置自动刷新
        self._configure_auto_refresh()

    def _configure_auto_refresh(self):
        """配置自动刷新"""
        # 检查是否有模块启用了自动刷新
        auto_refresh_enabled = any(
            config.auto_refresh for config in self.module_configs.values()
        )

        if auto_refresh_enabled:
            # 使用最小的刷新间隔
            min_interval = min(
                (config.refresh_interval for config in self.module_configs.values()
                 if config.auto_refresh),
                default=30
            )

            self.refresh_timer.start(min_interval * 1000)  # 转换为毫秒
            self.logger.info(f"自动刷新已启用，间隔: {min_interval}秒")

    def _auto_refresh_modules(self):
        """自动刷新模块"""
        current_time = time.time()

        for name, config in self.module_configs.items():
            if config.auto_refresh:
                # 检查是否需要刷新
                if hasattr(self, 'last_refresh_times'):
                    last_refresh = self.last_refresh_times.get(name, 0)
                    if current_time - last_refresh >= config.refresh_interval:
                        self._refresh_module(name)

    def _refresh_module(self, module_name: str):
        """刷新单个模块"""
        try:
            # 记录刷新时间
            if not hasattr(self, 'last_refresh_times'):
                pass  # 'self.last_refresh_times' is already initialized in __init__
            self.last_refresh_times[module_name] = time.time()

            self.logger.debug(f"模块 {module_name} 已刷新")
        except Exception as e:
            self.logger.error(f"刷新模块 {module_name} 失败: {e}")

    def _update_performance_metrics(self):
        """更新性能指标"""
        try:
            # 模拟性能数据更新
            for module_name in self.module_configs.keys():
                if module_name not in self.module_metrics:
                    self.module_metrics[module_name] = ModuleMetrics()

                # 更新一些基本指标
                metrics = self.module_metrics[module_name]
                metrics.cpu_usage = 0
                metrics.memory_usage = 0

        except Exception as e:
            self.logger.error(f"更新性能指标失败: {e}")

    # 信号处理方法
    def _on_module_state_changed(self, module_name: str, new_state: str):
        """模块状态变更处理"""
        self.logger.info(f"模块 {module_name} 状态变更为: {new_state}")

        # 发送事件
        if new_state == ModuleState.LOADED.value:
            self.event_manager.module_loaded.emit(module_name)
        elif new_state == ModuleState.INACTIVE.value:
            self.event_manager.module_unloaded.emit(module_name)
        elif new_state == ModuleState.ERROR.value:
            self.event_manager.module_error.emit(module_name, "Unknown error")

    def _show_performance_alert(self, alert_name: str, message: str, severity: str):
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
                parent=self
            )
        elif severity == "warning":
            InfoBar.warning(
                title="Performance Warning",
                content=message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def _handle_module_operation(self, operation: str, module_name: str):
        """处理模块操作请求"""
        if operation == "load":
            self._load_module_internal(module_name)
        elif operation == "unload":
            self.unload_module(module_name)
        elif operation == "reload":
            self.reload_module(module_name)
        elif operation == "validate":
            self._validate_module_internal(module_name)
        else:
            self.logger.warning(f"未知操作: {operation}")

    def _load_module_internal(self, module_name: str):
        """内部模块加载实现"""
        try:
            self.logger.info(f"正在加载模块: {module_name}")
            # 这里添加实际的模块加载逻辑
        except Exception as e:
            self.logger.error(f"加载模块 {module_name} 失败: {e}")

    def _validate_module_internal(self, module_name: str):
        """内部模块验证实现"""
        try:
            self.logger.info(f"正在验证模块: {module_name}")
            # 这里添加实际的模块验证逻辑
        except Exception as e:
            self.logger.error(f"验证模块 {module_name} 失败: {e}")

    # 事件处理方法
    def _on_module_loaded(self, module_name: str):
        """模块加载事件"""
        self.logger.info(f"模块加载事件: {module_name}")

    def _on_module_unloaded(self, module_name: str):
        """模块卸载事件"""
        self.logger.info(f"模块卸载事件: {module_name}")

    def _on_module_error(self, module_name: str, error_message: str):
        """模块错误事件"""
        self.logger.error(f"模块错误事件: {module_name} - {error_message}")
        self._show_error_message(f"模块 {module_name} 错误", error_message)

    def _on_performance_updated(self, module_name: str, metrics: Dict[str, Any]):
        """性能更新事件"""
        self.event_manager.performance_updated.emit(module_name, metrics)

    def _on_validation_event(self, module_name: str, success: bool, issues: List[Dict]):
        """验证事件"""
        # 记录验证事件以供后续处理
        self.logger.info(f"验证事件: {module_name} - {'成功' if success else '失败'}")
        if not success and issues:
            self.logger.warning(f"模块 {module_name} 验证发现 {len(issues)} 个问题")

    # 消息显示方法
    def _show_success_message(self, title: str, content: str):
        """显示成功消息"""
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def _show_error_message(self, title: str, content: str):
        """显示错误消息"""
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )

    def _show_critical_validation_warning(self, module_name: str, critical_issues: List[Dict]):
        """显示严重验证警告"""
        issues_text = "\n".join([issue.get('message', '')
                                for issue in critical_issues[:3]])
        if len(critical_issues) > 3:
            issues_text += f"\n... 及其他 {len(critical_issues) - 3} 个问题"

        # 使用正确的MessageBox API
        msg_box = MessageBox(
            title="严重验证问题",
            content=f"模块 {module_name} 存在严重问题：\n\n{issues_text}",
            parent=self
        )
        msg_box.exec()

    # 公共API方法
    def load_module(self, module_name: str, force: bool = False):
        """加载模块"""
        # 使用force参数进行条件检查
        if force or module_name not in self.module_configs:
            self.module_operation_requested.emit("load", module_name)
            self.logger.info(f"请求加载模块: {module_name} (force={force})")
        else:
            self.logger.info(f"模块 {module_name} 已存在，跳过加载")

    def unload_module(self, module_name: str):
        """卸载模块"""
        self.module_operation_requested.emit("unload", module_name)
        self.logger.info(f"请求卸载模块: {module_name}")

    def reload_module(self, module_name: str):
        """重新加载模块"""
        self.module_operation_requested.emit("reload", module_name)
        self.logger.info(f"请求重新加载模块: {module_name}")

    def validate_module(self, module_name: str):
        """验证模块"""
        self.module_operation_requested.emit("validate", module_name)
        self.logger.info(f"请求验证模块: {module_name}")

    def get_module_config(self, module_name: str) -> Optional[ModuleConfig]:
        """获取模块配置"""
        return self.module_configs.get(module_name)

    def update_module_config(self, module_name: str, config: ModuleConfig):
        """更新模块配置"""
        self.module_configs[module_name] = config
        self._save_module_configurations()

        # 如果配置了自动刷新，重新配置定时器
        if config.auto_refresh:
            self._configure_auto_refresh()

    def get_module_metrics(self, module_name: str) -> Optional[ModuleMetrics]:
        """获取模块性能指标"""
        return self.module_metrics.get(module_name)

    def get_all_module_metrics(self) -> Dict[str, ModuleMetrics]:
        """获取所有模块性能指标"""
        return self.module_metrics.copy()

    def export_module_data(self, filepath: str):
        """导出模块数据"""
        try:
            data = {
                'timestamp': time.time(),
                'configs': {},
                'metrics': {}
            }

            # 导出配置
            for name, config in self.module_configs.items():
                data['configs'][name] = {
                    'name': config.name,
                    'enabled': config.enabled,
                    'auto_refresh': config.auto_refresh,
                    'refresh_interval': config.refresh_interval,
                    'validation_enabled': config.validation_enabled,
                    'performance_monitoring': config.performance_monitoring
                }

            # 导出性能指标
            for name, metrics in self.module_metrics.items():
                data['metrics'][name] = {
                    'load_time': metrics.load_time,
                    'memory_usage': metrics.memory_usage,
                    'cpu_usage': metrics.cpu_usage,
                    'error_count': metrics.error_count,
                    'operations_count': metrics.operations_count,
                    'success_rate': metrics.success_rate,
                    'last_error': metrics.last_error
                }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"模块数据已导出到: {filepath}")
            self._show_success_message("导出成功", f"模块数据已导出到 {filepath}")

        except Exception as e:
            self.logger.error(f"导出模块数据失败: {e}")
            self._show_error_message("导出失败", str(e))

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'module_interface_state': self.current_state.value,
            'total_modules': len(self.module_configs),
            'performance_monitoring': self.performance_timer.isActive(),
            'auto_refresh': self.refresh_timer.isActive(),
            'cpu_usage': 0,
            'memory_usage': 0
        }

    def addSubInterface(self, widget: QWidget, object_name: str, text: str, icon=None):
        """添加子界面"""
        widget.setObjectName(object_name)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            icon=icon,
            routeKey=object_name,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index: int):
        """当前索引改变时的处理"""
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())

    def cleanup(self):
        """清理资源"""
        self.logger.info("开始清理 Module Interface 资源")

        # 停止定时器
        if self.performance_timer.isActive():
            self.performance_timer.stop()
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()

        # 保存配置
        self._save_module_configurations()

        self.logger.info("Module Interface 资源清理完成")

    def __del__(self):
        """析构函数"""
        try:
            self.cleanup()
        except Exception as e:
            print(f"Error during Module Interface cleanup: {e}")
