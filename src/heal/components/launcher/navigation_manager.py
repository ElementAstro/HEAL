"""
Launcher Navigation Manager
Handles navigation and interface management for launcher interface
"""

from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QStackedWidget, QWidget
from qfluentwidgets import FluentIcon, Pivot, qrouter

from src.heal.common.logging_config import get_logger


class LauncherNavigationManager(QObject):
    """启动器导航管理器"""

    # 信号
    interface_changed = Signal(str)  # interface_name

    def __init__(self, parent_widget: Optional[QWidget] = None) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger(
            "launcher_navigation_manager", module="LauncherNavigationManager"
        )

        # 界面组件
        self.pivot: Optional[Pivot] = None
        self.stacked_widget: Optional[QStackedWidget] = None

    def setup_navigation(self, pivot: Pivot, stacked_widget: QStackedWidget) -> None:
        """设置导航组件"""
        self.pivot = pivot
        self.stacked_widget = stacked_widget

        # 连接信号
        self.stacked_widget.currentChanged.connect(self.on_current_index_changed)

        self.logger.debug("导航组件已设置")

    def add_sub_interface(
        self, widget: QWidget, object_name: str, text: str, icon=None
    ):
        """添加子界面"""
        if not self.pivot or not self.stacked_widget:
            self.logger.error("导航组件未初始化")
            return

        widget.setObjectName(object_name)
        self.stacked_widget.addWidget(widget)
        self.pivot.addItem(
            icon=icon,
            routeKey=object_name,
            text=text,
            onClick=lambda: self.set_current_widget(widget),
        )
        self.logger.debug(f"子界面 {object_name} 已添加。")

    def set_current_widget(self, widget: QWidget) -> None:
        """设置当前显示的界面"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentWidget(widget)
            self.interface_changed.emit(widget.objectName())

    def set_default_interface(self, widget: QWidget) -> None:
        """设置默认界面"""
        if not self.pivot or not self.stacked_widget:
            self.logger.error("导航组件未初始化")
            return

        self.stacked_widget.setCurrentWidget(widget)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.setDefaultRouteKey(self.stacked_widget, widget.objectName())
        self.logger.debug(f"默认界面已设置: {widget.objectName()}")

    def on_current_index_changed(self, index: int) -> None:
        """当前索引改变时的回调"""
        if not self.stacked_widget or not self.pivot:
            return

        widget = self.stacked_widget.widget(index)
        if widget:
            self.pivot.setCurrentItem(widget.objectName())
            qrouter.push(self.stacked_widget, widget.objectName())
            self.interface_changed.emit(widget.objectName())
            self.logger.debug(f"当前索引已更改为 {index} - {widget.objectName()}")
