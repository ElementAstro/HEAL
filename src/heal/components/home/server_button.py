from typing import List

from PySide6.QtGui import QAction, QContextMenuEvent
from PySide6.QtWidgets import QWidget
from qfluentwidgets import Action, FluentIcon, RoundMenu, TogglePushButton


class ServerButton(TogglePushButton):
    """Custom server control button with context menu functionality."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_server_button()

    def _init_server_button(self) -> None:
        """Initialize server button specific functionality."""
        self.context_menu_widgets: List[QWidget] = []

    def add_widget(self, widget: QWidget) -> None:
        """添加组件到上下文菜单"""
        self.context_menu_widgets.append(widget)

    def remove_widget(self, widget: QWidget) -> None:
        """从上下文菜单移除组件"""
        if widget in self.context_menu_widgets:
            self.context_menu_widgets.remove(widget)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """显示上下文菜单"""
        menu = RoundMenu(parent=self)
        for widget in self.context_menu_widgets:
            menu.addWidget(widget, selectable=False)

        self.add_custom_actions(menu)
        menu.exec(event.globalPos())

    def add_custom_actions(self, menu: RoundMenu) -> None:
        """添加自定义服务器操作到菜单"""
        menu.addSeparator()
        settings_action = Action(FluentIcon.SETTING, "设置")
        restart_action = QAction("重启服务器", self)
        restart_action.triggered.connect(self.restart_server)
        stop_action = QAction("停止服务器", self)
        stop_action.triggered.connect(self.stop_server)
        start_action = QAction("启动服务器", self)
        start_action.triggered.connect(self.start_server)
        menu.addAction(settings_action)
        menu.addAction(restart_action)
        menu.addAction(stop_action)
        menu.addAction(start_action)

    def restart_server(self) -> None:
        """重启服务器"""
        print(f"服务器 {self.objectName()} 正在重启...")

    def stop_server(self) -> None:
        """停止服务器"""
        print(f"服务器 {self.objectName()} 已停止。")

    def start_server(self) -> None:
        """启动服务器"""
        print(f"服务器 {self.objectName()} 已启动。")
