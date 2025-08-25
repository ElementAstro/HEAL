"""
UI Utilities - 统一UI组件初始化和管理工具
消除项目中UI初始化的重复代码
"""

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

    def create_layout(
        self, layout_type: str, name: str, parent: Optional[QWidget] = None, **kwargs
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
                        layout.setContentsMargins(margins, margins, margins, margins)

            elif layout_type == "hbox":
                layout = QHBoxLayout(parent)
                if "spacing" in kwargs:
                    layout.setSpacing(kwargs["spacing"])
                if "margins" in kwargs:
                    margins = kwargs["margins"]
                    if isinstance(margins, (list, tuple)):
                        layout.setContentsMargins(*margins)
                    else:
                        layout.setContentsMargins(margins, margins, margins, margins)

            elif layout_type == "grid":
                layout = QGridLayout(parent)
                if "spacing" in kwargs:
                    layout.setSpacing(kwargs["spacing"])
                if "margins" in kwargs:
                    margins = kwargs["margins"]
                    if isinstance(margins, (list, tuple)):
                        layout.setContentsMargins(*margins)
                    else:
                        layout.setContentsMargins(margins, margins, margins, margins)

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
                    connection_type=conn.get("type", Qt.ConnectionType.AutoConnection),
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
