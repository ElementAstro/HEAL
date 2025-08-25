import sys

from PySide6.QtCore import Signal
from qfluentwidgets import MSFluentWindow

from src.heal.common.logging_config import get_logger

from typing import Any

# Import main components
from src.heal.components.main import (
    AudioManager,
    AuthenticationManager,
    FontManager,
    MainNavigationManager,
    ThemeManager,
    UpdateManager,
    WindowManager,
)
from src.heal.models.config import cfg

# 使用统一日志配置
logger = get_logger("main_interface")


class Main(MSFluentWindow):
    reload_signal = Signal()
    shutdown_signal = Signal()

    def __init__(self) -> None:
        super().__init__()

        # 初始化所有管理器
        self.window_manager = WindowManager(self)
        self.navigation_manager = MainNavigationManager(self)
        self.auth_manager = AuthenticationManager(self)
        self.theme_manager = ThemeManager(self)
        self.audio_manager = AudioManager(self)
        self.font_manager = FontManager(self)
        self.update_manager = UpdateManager(self)

        # Initialize tray_icon as None initially
        self.tray_icon: Any = None

        # 初始化应用
        self.init_application()

    def init_application(self) -> None:
        """初始化应用程序"""
        # 1. 初始化主题
        self.theme_manager.init_theme()

        # 2. 初始化主窗口
        self.window_manager.init_main_window()

        # 3. 初始化导航
        self.navigation_manager.init_navigation()

        # 4. 检查字体
        self.font_manager.handle_font_check()

        # 5. 完成启动画面
        self.window_manager.finish_splash()

        # 6. 连接信号
        self.connect_signals()

        # 7. 处理登录或音频
        self.handle_initial_setup()

        logger.info("应用程序初始化完成")

    def connect_signals(self) -> None:
        """连接所有信号"""
        # 导航管理器信号
        self.navigation_manager.theme_change_requested.connect(
            self.theme_manager.toggle_theme
        )
        self.navigation_manager.reload_requested.connect(
            lambda: self.reload_signal.emit()
        )
        self.navigation_manager.shutdown_requested.connect(
            lambda: self.shutdown_signal.emit()
        )

        # 认证管理器信号
        self.auth_manager.login_success.connect(self.handle_login_success)
        self.auth_manager.login_failed.connect(self.handle_login_failed)

        # 更新管理器信号
        self.update_manager.update_checked.connect(
            self.update_manager.handle_update_result
        )

        logger.debug("信号连接完成")

    def handle_initial_setup(self) -> None:
        """处理初始设置"""
        # 处理登录
        if not self.auth_manager.init_login():
            # 如果不需要登录，直接处理音频
            if cfg.useAudio.value:
                self.audio_manager.play_audio("success")

    def handle_login_success(self) -> None:
        """处理登录成功"""
        if cfg.useAudio.value:
            self.audio_manager.play_audio("success")

    def handle_login_failed(self, attempt_count: int) -> None:
        """处理登录失败"""
        if cfg.useAudio.value:
            self.audio_manager.play_audio("error")

    def toggle_window(self) -> None:
        """切换窗口显示状态"""
        self.window_manager.toggle_window_visibility()

        # 更新托盘图标状态（如果存在）
        if self.tray_icon and hasattr(self.tray_icon, "toggle_action"):
            action_text = "显示窗口" if not self.isVisible() else "隐藏窗口"
            self.tray_icon.toggle_action.setText(action_text)
