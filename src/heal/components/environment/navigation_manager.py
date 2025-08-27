"""
Environment Navigation Manager
Handles navigation and layout for environment interface
"""

from typing import Optional

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon, Pivot, qrouter

from src.heal.common.logging_config import get_logger


class EnvironmentNavigationManager(QObject):
    """环境导航管理器"""

    # 信号
    navigation_changed = Signal(str, int)  # object_name, index

    def __init__(self, parent_widget: QWidget) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger(
            "environment_navigation_manager", module="EnvironmentNavigationManager"
        )

        # UI组件将由外部设置
        self.pivot: Optional[Pivot] = None
        self.stacked_widget: Optional[QStackedWidget] = None

    def set_navigation_components(self, pivot: Pivot, stacked_widget: QStackedWidget) -> None:
        """设置导航组件"""
        self.pivot = pivot
        self.stacked_widget = stacked_widget

        # 连接信号
        if self.stacked_widget:
            self.stacked_widget.currentChanged.connect(
                self.on_current_index_changed)

    def add_sub_interface(
        self,
        widget: QWidget,
        objectName: str,
        text: str,
        icon: Optional[FluentIcon] = None,
    ) -> None:
        """添加子界面"""
        widget.setObjectName(objectName)

        if self.stacked_widget:
            self.stacked_widget.addWidget(widget)

        if self.pivot:
            self.pivot.addItem(
                icon=icon,
                routeKey=objectName,
                text=text,
                onClick=lambda: self.navigate_to_widget(widget),
            )

        self.logger.debug(f"子界面 {objectName} 已添加。")

    def navigate_to_widget(self, widget: QWidget) -> None:
        """导航到指定组件"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentWidget(widget)
        self._update_navigation_state(widget)

    def navigate_to_index(self, index: int) -> None:
        """导航到指定索引"""
        if self.stacked_widget and 0 <= index < self.stacked_widget.count():
            widget = self.stacked_widget.widget(index)
            if widget:
                self.stacked_widget.setCurrentIndex(index)
                self._update_navigation_state(widget)

    def on_current_index_changed(self, index: int) -> None:
        """当前索引改变处理"""
        if self.stacked_widget:
            widget = self.stacked_widget.widget(index)
            if widget:
                self._update_navigation_state(widget)
                self.navigation_changed.emit(widget.objectName(), index)
                self.logger.debug(f"当前索引已更改为 {index} - {widget.objectName()}")

    def _update_navigation_state(self, widget: QWidget) -> None:
        """更新导航状态"""
        if self.pivot and widget:
            self.pivot.setCurrentItem(widget.objectName())
            if self.stacked_widget:
                qrouter.push(self.stacked_widget, widget.objectName())

    def setup_layout(self, vbox_layout: QVBoxLayout) -> None:
        """设置布局"""
        if self.pivot:
            vbox_layout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        if self.stacked_widget:
            vbox_layout.addWidget(self.stacked_widget)

        vbox_layout.setSpacing(15)
        vbox_layout.setContentsMargins(0, 10, 10, 0)

    def set_default_interface(self, widget: QWidget) -> None:
        """设置默认界面"""
        if self.stacked_widget and self.pivot:
            self.stacked_widget.setCurrentWidget(widget)
            self.pivot.setCurrentItem(widget.objectName())
            qrouter.setDefaultRouteKey(
                self.stacked_widget, widget.objectName())

    def get_current_widget(self) -> Optional[QWidget]:
        """获取当前组件"""
        if self.stacked_widget:
            return self.stacked_widget.currentWidget()
        return None

    def get_current_index(self) -> int:
        """获取当前索引"""
        if self.stacked_widget:
            return int(self.stacked_widget.currentIndex())
        return -1
