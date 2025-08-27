"""
Main Navigation Manager
Handles interface navigation and routing setup
"""

from typing import Any, List, Tuple

from PySide6.QtCore import QObject, Signal
from qfluentwidgets import FluentIcon, NavigationItemPosition

from ...interfaces.download_interface import Download
from ...interfaces.environment_interface import Environment

# Import all interfaces
from ...interfaces.home_interface import Home
from ...interfaces.launcher_interface import Launcher
from ...interfaces.log_interface import LogManagement
from ...interfaces.module_interface import Module
from ...interfaces.proxy_interface import Proxy
from ...interfaces.setting_interface import Setting
from ...interfaces.tool_interface import Tools

from src.heal.common.logging_config import get_logger


class MainNavigationManager(QObject):
    """主导航管理器"""

    # 信号
    theme_change_requested = Signal()
    reload_requested = Signal()
    shutdown_requested = Signal()

    def __init__(self, main_window: Any) -> None:
        super().__init__(main_window)
        self.main_window = main_window
        self.logger = get_logger(
            "main_navigation_manager", module="MainNavigationManager"
        )

        # 界面实例
        self.interfaces: dict[str, Any] = {}

    def init_navigation(self) -> None:
        """初始化导航界面"""
        # 创建所有界面实例
        self.interfaces = {
            "home": Home("HomeInterface", self.main_window),
            "launcher": Launcher("LauncherInterface", self.main_window),
            "download": Download("DownloadInterface", self.main_window),
            "environment": Environment("EnvironmentInterface", self.main_window),
            "module": Module("ModuleInterface", self.main_window),
            "proxy": Proxy("ProxyInterface", self.main_window),
            "tools": Tools("ToolsInterface", self.main_window),
            "logs": LogManagement("LogInterface", self.main_window),
            "setting": Setting("SettingInterface", self.main_window),
        }

        # 界面配置
        interface_configs = [
            (
                "home",
                FluentIcon.HOME,
                self.main_window.tr("主页"),
                FluentIcon.HOME_FILL,
            ),
            (
                "launcher",
                FluentIcon.PLAY,
                self.main_window.tr("启动器"),
                FluentIcon.PLAY,
            ),
            (
                "download",
                FluentIcon.DOWNLOAD,
                self.main_window.tr("下载"),
                FluentIcon.DOWNLOAD,
            ),
            (
                "environment",
                FluentIcon.DICTIONARY,
                self.main_window.tr("环境"),
                FluentIcon.DICTIONARY,
            ),
            (
                "module",
                FluentIcon.APPLICATION,
                self.main_window.tr("模块"),
                FluentIcon.APPLICATION,
            ),
            (
                "proxy",
                FluentIcon.CERTIFICATE,
                self.main_window.tr("代理"),
                FluentIcon.CERTIFICATE,
            ),
            (
                "tools",
                FluentIcon.DEVELOPER_TOOLS,
                self.main_window.tr("工具"),
                FluentIcon.DEVELOPER_TOOLS,
            ),
            (
                "logs",
                FluentIcon.DOCUMENT,
                self.main_window.tr("日志"),
                FluentIcon.DOCUMENT,
            ),
            (
                "setting",
                FluentIcon.SETTING,
                self.main_window.tr("设置"),
                FluentIcon.SETTING,
                NavigationItemPosition.BOTTOM,
            ),
        ]

        # 添加所有界面
        for config in interface_configs:
            interface_key, icon, text, fill_icon, *position = config
            pos = position[0] if position else NavigationItemPosition.TOP
            interface = self.interfaces[interface_key]
            self.main_window.addSubInterface(
                interface, icon, text, fill_icon, pos)

        # 添加功能按钮
        self._add_navigation_actions()

        self.logger.info("导航界面已初始化")

    def _add_navigation_actions(self) -> None:
        """添加导航功能按钮"""
        # 主题切换按钮
        self.main_window.navigationInterface.addItem(
            routeKey="theme",
            icon=FluentIcon.CONSTRACT,
            text=self.main_window.tr("主题"),
            onClick=self._handle_theme_change,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        # 热重载按钮
        self.main_window.navigationInterface.addItem(
            routeKey="reload",
            icon=FluentIcon.SYNC,
            text=self.main_window.tr("热重载"),
            onClick=self._handle_reload,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        # 关机按钮
        self.main_window.navigationInterface.addItem(
            routeKey="shutdown",
            icon=FluentIcon.POWER_BUTTON,
            text=self.main_window.tr("关机"),
            onClick=self._handle_shutdown,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        self.logger.debug("导航功能按钮已添加")

    def _handle_theme_change(self) -> None:
        """处理主题切换"""
        self.theme_change_requested.emit()

    def _handle_reload(self) -> None:
        """处理重载请求"""
        self.reload_requested.emit()

    def _handle_shutdown(self) -> None:
        """处理关机请求"""
        self.shutdown_requested.emit()

    def get_interface(self, interface_key: str) -> Any:
        """获取指定界面"""
        return self.interfaces.get(interface_key)
