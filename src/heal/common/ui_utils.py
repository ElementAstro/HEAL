"""
UI Utilities - 统一UI组件初始化和管理工具
消除项目中UI初始化的重复代码
"""

import time
from typing import Any, Callable, Dict, List, Optional, Union

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    ExpandLayout,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SettingCard,
)

from .logging_config import get_logger
from .resource_manager import register_custom_resource, register_timer

logger = get_logger(__name__)


class UIComponentManager(QObject):
    """UI组件管理器 - 统一UI组件的创建和管理"""

    # 信号
    component_created = Signal(str, QWidget)  # component_name, widget
    layout_created = Signal(str, object)  # layout_name, layout
    signal_connected = Signal(str, str)  # source, target

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.parent_widget = parent
        self.logger = logger.bind(component="UIComponentManager")

        # 组件注册表
        self.components: Dict[str, QWidget] = {}
        self.layouts: Dict[str, object] = {}
        self.timers: Dict[str, QTimer] = {}
        self.signal_connections: List[Dict[str, Any]] = []

        self.logger.debug("UI组件管理器已初始化")

    def create_responsive_operation(
        self,
        operation_name: str,
        operation_func: Callable,
        progress_callback: Optional[Callable] = None,
        completion_callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None
    ) -> 'ResponsiveOperation':
        """创建响应式操作，防止UI阻塞"""
        return ResponsiveOperation(
            operation_name,
            operation_func,
            progress_callback,
            completion_callback,
            error_callback,
            parent=self
        )

    def create_layout(
        self, layout_type: str, name: str, parent: Optional[QWidget] = None, **kwargs: Any
    ) -> object:
        """
        创建布局

        Args:
            layout_type: 布局类型 ('vbox', 'hbox', 'grid', 'expand')
            name: 布局名称
            parent: 父组件
            **kwargs: 布局参数

        Returns:
            object: 创建的布局对象
        """
        try:
            layout = None

            if layout_type == "vbox":
                layout = QVBoxLayout(parent)
                if "spacing" in kwargs:
                    layout.setSpacing(kwargs["spacing"])
                if "margins" in kwargs:
                    margins = kwargs["margins"]
                    if isinstance(margins, (list, tuple)):
                        layout.setContentsMargins(*margins)
                    else:
                        layout.setContentsMargins(
                            margins, margins, margins, margins)

            elif layout_type == "hbox":
                layout = QHBoxLayout(parent)
                if "spacing" in kwargs:
                    layout.setSpacing(kwargs["spacing"])
                if "margins" in kwargs:
                    margins = kwargs["margins"]
                    if isinstance(margins, (list, tuple)):
                        layout.setContentsMargins(*margins)
                    else:
                        layout.setContentsMargins(
                            margins, margins, margins, margins)

            elif layout_type == "grid":
                layout = QGridLayout(parent)
                if "spacing" in kwargs:
                    layout.setSpacing(kwargs["spacing"])
                if "margins" in kwargs:
                    margins = kwargs["margins"]
                    if isinstance(margins, (list, tuple)):
                        layout.setContentsMargins(*margins)
                    else:
                        layout.setContentsMargins(
                            margins, margins, margins, margins)

            elif layout_type == "expand":
                layout = ExpandLayout(parent)

            else:
                raise ValueError(f"不支持的布局类型: {layout_type}")

            # 注册布局
            self.layouts[name] = layout
            self.layout_created.emit(name, layout)

            self.logger.debug(f"创建布局: {name} ({layout_type})")
            return layout

        except Exception as e:
            self.logger.error(f"创建布局失败 {name}: {e}")
            raise

    def create_splitter(
        self,
        name: str,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        stretch_factors: Optional[List[int]] = None,
    ) -> QSplitter:
        """
        创建分割器

        Args:
            name: 分割器名称
            orientation: 方向
            stretch_factors: 拉伸因子列表

        Returns:
            QSplitter: 创建的分割器
        """
        try:
            splitter = QSplitter(orientation)

            # 设置拉伸因子
            if stretch_factors:
                for i, factor in enumerate(stretch_factors):
                    splitter.setStretchFactor(i, factor)

            # 注册组件
            self.components[name] = splitter
            self.component_created.emit(name, splitter)

            self.logger.debug(f"创建分割器: {name}")
            return splitter

        except Exception as e:
            self.logger.error(f"创建分割器失败 {name}: {e}")
            raise

    def create_scroll_area(
        self,
        name: str,
        widget_resizable: bool = True,
        horizontal_policy: Qt.ScrollBarPolicy = Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        vertical_policy: Qt.ScrollBarPolicy = Qt.ScrollBarPolicy.ScrollBarAsNeeded,
    ) -> QScrollArea:
        """
        创建滚动区域

        Args:
            name: 滚动区域名称
            widget_resizable: 是否可调整大小
            horizontal_policy: 水平滚动条策略
            vertical_policy: 垂直滚动条策略

        Returns:
            QScrollArea: 创建的滚动区域
        """
        try:
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(widget_resizable)
            scroll_area.setHorizontalScrollBarPolicy(horizontal_policy)
            scroll_area.setVerticalScrollBarPolicy(vertical_policy)

            # 注册组件
            self.components[name] = scroll_area
            self.component_created.emit(name, scroll_area)

            self.logger.debug(f"创建滚动区域: {name}")
            return scroll_area

        except Exception as e:
            self.logger.error(f"创建滚动区域失败 {name}: {e}")
            raise

    def create_timer(
        self,
        name: str,
        interval: int,
        callback: Callable,
        single_shot: bool = False,
        auto_start: bool = False,
    ) -> QTimer:
        """
        创建定时器

        Args:
            name: 定时器名称
            interval: 间隔时间(ms)
            callback: 回调函数
            single_shot: 是否单次触发
            auto_start: 是否自动启动

        Returns:
            QTimer: 创建的定时器
        """
        try:
            timer = QTimer()
            timer.setInterval(interval)
            timer.setSingleShot(single_shot)
            timer.timeout.connect(callback)

            if auto_start:
                timer.start()

            # 注册定时器
            self.timers[name] = timer
            register_timer(f"ui_timer_{name}", timer, f"UI定时器: {name}")

            self.logger.debug(f"创建定时器: {name} (间隔: {interval}ms)")
            return timer

        except Exception as e:
            self.logger.error(f"创建定时器失败 {name}: {e}")
            raise

    def connect_signal(
        self,
        source_obj: QObject,
        signal_name: str,
        target_obj: Union[QObject, Callable],
        slot_name: Optional[str] = None,
        connection_type: Qt.ConnectionType = Qt.ConnectionType.AutoConnection,
    ) -> bool:
        """
        连接信号和槽

        Args:
            source_obj: 信号源对象
            signal_name: 信号名称
            target_obj: 目标对象或回调函数
            slot_name: 槽名称（如果target_obj是对象）
            connection_type: 连接类型

        Returns:
            bool: 是否连接成功
        """
        try:
            # 获取信号
            signal = getattr(source_obj, signal_name, None)
            if signal is None:
                raise AttributeError(f"对象 {source_obj} 没有信号 {signal_name}")

            # 连接信号
            if callable(target_obj):
                # 直接连接到函数
                signal.connect(target_obj, connection_type)
                target_desc = (
                    target_obj.__name__
                    if hasattr(target_obj, "__name__")
                    else str(target_obj)
                )
            else:
                # 连接到对象的槽
                if slot_name is None:
                    raise ValueError("连接到对象时必须指定槽名称")

                slot = getattr(target_obj, slot_name, None)
                if slot is None:
                    raise AttributeError(f"对象 {target_obj} 没有槽 {slot_name}")

                signal.connect(slot, connection_type)
                target_desc = f"{target_obj}.{slot_name}"

            # 记录连接
            connection_info = {
                "source": f"{source_obj}.{signal_name}",
                "target": target_desc,
                "connection_type": connection_type,
            }
            self.signal_connections.append(connection_info)

            self.signal_connected.emit(
                connection_info["source"], connection_info["target"]
            )
            self.logger.debug(
                f"信号连接成功: {connection_info['source']} -> {connection_info['target']}"
            )

            return True

        except Exception as e:
            self.logger.error(f"信号连接失败: {e}")
            return False

    def batch_connect_signals(self, connections: List[Dict[str, Any]]) -> int:
        """
        批量连接信号

        Args:
            connections: 连接配置列表

        Returns:
            int: 成功连接的数量
        """
        success_count = 0

        for conn in connections:
            try:
                result = self.connect_signal(
                    source_obj=conn["source"],
                    signal_name=conn["signal"],
                    target_obj=conn["target"],
                    slot_name=conn.get("slot"),
                    connection_type=conn.get(
                        "type", Qt.ConnectionType.AutoConnection),
                )

                if result:
                    success_count += 1

            except Exception as e:
                self.logger.error(f"批量连接信号失败: {e}")

        self.logger.info(f"批量信号连接完成: {success_count}/{len(connections)} 成功")
        return success_count

    def show_info_bar(
        self,
        title: str,
        content: str,
        duration: int = 3000,
        position: InfoBarPosition = InfoBarPosition.TOP,
        parent: Optional[QWidget] = None,
    ) -> InfoBar:
        """
        显示信息条

        Args:
            title: 标题
            content: 内容
            duration: 显示时长(ms)
            position: 位置
            parent: 父组件

        Returns:
            InfoBar: 信息条对象
        """
        try:
            parent_widget = parent or self.parent_widget
            if parent_widget is None:
                raise ValueError("必须指定父组件")

            info_bar = InfoBar.success(
                title=title,
                content=content,
                duration=duration,
                position=position,
                parent=parent_widget,
            )

            self.logger.debug(f"显示信息条: {title}")
            return info_bar

        except Exception as e:
            self.logger.error(f"显示信息条失败: {e}")
            raise

    def get_component(self, name: str) -> Optional[QWidget]:
        """获取注册的组件"""
        return self.components.get(name)

    def get_layout(self, name: str) -> Optional[object]:
        """获取注册的布局"""
        return self.layouts.get(name)

    def get_timer(self, name: str) -> Optional[QTimer]:
        """获取注册的定时器"""
        return self.timers.get(name)

    def cleanup_resources(self) -> None:
        """清理资源"""
        try:
            # 停止所有定时器
            for timer in self.timers.values():
                if timer.isActive():
                    timer.stop()

            # 清理注册表
            self.components.clear()
            self.layouts.clear()
            self.timers.clear()
            self.signal_connections.clear()

            self.logger.info("UI组件资源清理完成")

        except Exception as e:
            self.logger.error(f"清理UI组件资源失败: {e}")

    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            "total_connections": len(self.signal_connections),
            "components_count": len(self.components),
            "layouts_count": len(self.layouts),
            "timers_count": len(self.timers),
            "connections": self.signal_connections.copy(),
        }


# 便捷函数
def create_standard_layout(
    parent: QWidget,
    layout_type: str = "vbox",
    spacing: int = 10,
    margins: Union[int, List[int]] = 10,
) -> object:
    """创建标准布局的便捷函数"""
    manager = UIComponentManager(parent)
    return manager.create_layout(
        layout_type=layout_type,
        name=f"standard_{layout_type}_layout",
        parent=parent,
        spacing=spacing,
        margins=margins,
    )


def create_standard_splitter(
    orientation: Qt.Orientation = Qt.Orientation.Horizontal,
    stretch_factors: Optional[List[int]] = None,
) -> QSplitter:
    """创建标准分割器的便捷函数"""
    manager = UIComponentManager()
    return manager.create_splitter(
        name="standard_splitter",
        orientation=orientation,
        stretch_factors=stretch_factors,
    )


class ResponsiveOperation(QObject):
    """响应式操作类 - 防止UI阻塞的操作包装器"""

    # 信号
    progress_updated = Signal(int)  # progress percentage
    operation_completed = Signal(object)  # result
    operation_failed = Signal(str)  # error message

    def __init__(
        self,
        operation_name: str,
        operation_func: Callable,
        progress_callback: Optional[Callable] = None,
        completion_callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
        parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self.operation_name = operation_name
        self.operation_func = operation_func
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback
        self.logger = logger.bind(component="ResponsiveOperation")

        # 连接信号
        if progress_callback:
            self.progress_updated.connect(progress_callback)
        if completion_callback:
            self.operation_completed.connect(completion_callback)
        if error_callback:
            self.operation_failed.connect(error_callback)

    def execute_async(self, *args: Any, **kwargs: Any) -> None:
        """异步执行操作"""
        from .performance_analyzer import global_performance_analyzer

        # 记录UI响应时间
        start_time = time.time()

        def run_operation() -> None:
            try:
                result = self.operation_func(*args, **kwargs)
                self.operation_completed.emit(result)

                # 记录操作完成时间
                execution_time = time.time() - start_time
                global_performance_analyzer.record_ui_responsiveness(
                    self.operation_name, execution_time
                )

            except Exception as e:
                error_msg = f"操作失败: {e}"
                self.logger.error(error_msg)
                self.operation_failed.emit(error_msg)

        # 使用QTimer延迟执行，保持UI响应
        QTimer.singleShot(0, run_operation)

    def execute_in_thread(self, *args: Any, **kwargs: Any) -> None:
        """在后台线程中执行操作"""
        from PySide6.QtCore import QThread

        class WorkerThread(QThread):
            def __init__(self, operation: Any, args: Any, kwargs: Any) -> None:
                super().__init__()
                self.operation = operation
                self.args = args
                self.kwargs = kwargs

            def run(self) -> None:
                try:
                    result = self.operation.operation_func(
                        *self.args, **self.kwargs)
                    self.operation.operation_completed.emit(result)
                except Exception as e:
                    error_msg = f"后台操作失败: {e}"
                    self.operation.logger.error(error_msg)
                    self.operation.operation_failed.emit(error_msg)

        worker = WorkerThread(self, args, kwargs)
        worker.start()


class UIBatchProcessor(QObject):
    """UI批处理器 - 批量处理UI更新以提高性能"""

    batch_processed = Signal(int)  # processed count

    def __init__(self, batch_size: int = 50, delay_ms: int = 100, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.batch_size = batch_size
        self.delay_ms = delay_ms
        self.pending_operations: List[Callable] = []
        self.timer = QTimer()
        self.timer.timeout.connect(self._process_batch)
        self.timer.setSingleShot(True)
        self.logger = logger.bind(component="UIBatchProcessor")

    def add_operation(self, operation: Callable) -> None:
        """添加操作到批处理队列"""
        self.pending_operations.append(operation)

        # 如果达到批处理大小或者定时器未启动，开始处理
        if len(self.pending_operations) >= self.batch_size or not self.timer.isActive():
            self.timer.start(self.delay_ms)

    def _process_batch(self) -> None:
        """处理批量操作"""
        if not self.pending_operations:
            return

        processed_count = 0
        operations_to_process = self.pending_operations[:self.batch_size]
        self.pending_operations = self.pending_operations[self.batch_size:]

        for operation in operations_to_process:
            try:
                operation()
                processed_count += 1

                # 每处理几个操作就让UI响应一下
                if processed_count % 10 == 0:
                    from PySide6.QtWidgets import QApplication
                    QApplication.processEvents()

            except Exception as e:
                self.logger.error(f"批处理操作失败: {e}")

        self.batch_processed.emit(processed_count)

        # 如果还有待处理的操作，继续处理
        if self.pending_operations:
            self.timer.start(self.delay_ms)

    def flush(self) -> None:
        """立即处理所有待处理的操作"""
        if self.timer.isActive():
            self.timer.stop()
        self._process_batch()


# 全局UI优化实例
global_ui_batch_processor = UIBatchProcessor()

# 创建常用UI对象的对象池
# Declare variables with proper types
timer_pool: Optional[Any] = None
label_pool: Optional[Any] = None
button_pool: Optional[Any] = None

try:
    from .memory_optimizer import create_object_pool

    # QTimer对象池
    def create_timer() -> QTimer:
        timer = QTimer()
        timer.setSingleShot(True)
        return timer

    timer_pool = create_object_pool("ui_timers", create_timer, max_size=50)

    # QLabel对象池
    def create_label() -> QLabel:
        return QLabel()

    label_pool = create_object_pool("ui_labels", create_label, max_size=100)

    # QPushButton对象池
    def create_button() -> QPushButton:
        return QPushButton()

    button_pool = create_object_pool("ui_buttons", create_button, max_size=50)

except ImportError:
    # Variables already declared above
    pass


def batch_ui_update(operation: Callable) -> None:
    """将UI更新操作添加到批处理队列"""
    global_ui_batch_processor.add_operation(operation)


def create_responsive_operation(
    operation_name: str,
    operation_func: Callable,
    progress_callback: Optional[Callable] = None,
    completion_callback: Optional[Callable] = None,
    error_callback: Optional[Callable] = None
) -> ResponsiveOperation:
    """创建响应式操作的便捷函数"""
    return ResponsiveOperation(
        operation_name,
        operation_func,
        progress_callback,
        completion_callback,
        error_callback
    )


def get_pooled_timer() -> QTimer:
    """从对象池获取QTimer"""
    if timer_pool:
        return timer_pool.acquire()
    else:
        timer = QTimer()
        timer.setSingleShot(True)
        return timer


def return_pooled_timer(timer: QTimer) -> None:
    """将QTimer返回到对象池"""
    if timer_pool:
        # 重置定时器状态
        timer.stop()
        timer.timeout.disconnect()
        timer_pool.release(timer)


def get_pooled_label() -> QLabel:
    """从对象池获取QLabel"""
    if label_pool:
        return label_pool.acquire()
    else:
        return QLabel()


def return_pooled_label(label: QLabel) -> None:
    """将QLabel返回到对象池"""
    if label_pool:
        # 重置标签状态
        label.clear()
        label.setParent(None)
        label_pool.release(label)


def get_pooled_button() -> QPushButton:
    """从对象池获取QPushButton"""
    if button_pool:
        return button_pool.acquire()
    else:
        return QPushButton()


def return_pooled_button(button: QPushButton) -> None:
    """将QPushButton返回到对象池"""
    if button_pool:
        # 重置按钮状态
        button.setText("")
        button.setParent(None)
        button.clicked.disconnect()
        button_pool.release(button)
