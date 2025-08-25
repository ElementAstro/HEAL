from typing import Optional

from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QWidget
from qfluentwidgets import Action, FluentIcon, RoundMenu

from src.heal.common.logging_config import get_logger
from ..resources import resource_manager

# 使用统一日志配置
logger = get_logger("system_tray")


class SystemTray(QSystemTrayIcon):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # 设置初始图标
        self.setIcon(
            QIcon(str(resource_manager.get_resource_path("images", "atom.png")))
        )

        # 创建托盘图标的右键菜单
        self.tray_menu = RoundMenu(parent=parent)

        # 添加显示/隐藏主窗口的菜单项
        self.toggle_action = Action(FluentIcon.HOME, "Show Window", self)
        if parent and hasattr(parent, "toggle_window"):
            self.toggle_action.triggered.connect(parent.toggle_window)
        else:
            logger.warning(
                f"系统托盘父组件 {parent} 没有 'toggle_window' 方法或父组件为空"
            )
        self.tray_menu.addAction(self.toggle_action)

        # 添加退出的菜单项
        quit_action = Action(FluentIcon.CLOSE, "Quit", self)
        app_instance = QCoreApplication.instance()
        if app_instance:
            quit_action.triggered.connect(app_instance.quit)
        else:
            logger.warning("QCoreApplication.instance() 为空，无法连接退出操作")
        self.tray_menu.addAction(quit_action)

        # 将菜单应用到托盘图标
        self.setContextMenu(self.tray_menu)

        # 显示托盘图标
        self.show()

        # 连接托盘图标的点击事件
        if parent and hasattr(parent, "on_tray_icon_activated"):
            self.activated.connect(parent.on_tray_icon_activated)
        else:
            logger.warning(
                f"系统托盘父组件 {parent} 没有 'on_tray_icon_activated' 方法或父组件为空"
            )

        # 显示图标提示
        self.setToolTip("My Application is running")

        # 动态更新图标
        self.icon_timer = QTimer(self)
        self.icon_timer.timeout.connect(self.update_icon)
        self.icon_timer.start(5000)  # 每5秒更新图标

    def update_icon(self) -> None:
        # 动态更新图标
        # Corrected path assuming it's relative to execution dir or use absolute
        new_icon_path = str(resource_manager.get_resource_path("images", "atom.png"))
        self.setIcon(QIcon(new_icon_path))
