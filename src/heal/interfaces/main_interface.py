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
        """初始化应用程序 - 使用工作流优化"""
        from src.heal.common.workflow_optimizer import create_workflow

        # 创建应用初始化工作流
        workflow = create_workflow("main_app_initialization")

        # 添加初始化步骤
        workflow.add_step("init_theme", self.theme_manager.init_theme)
        workflow.add_step(
            "init_window", self.window_manager.init_main_window, ["init_theme"])
        workflow.add_step(
            "init_navigation", self.navigation_manager.init_navigation, ["init_window"])
        workflow.add_step(
            "check_fonts", self.font_manager.handle_font_check, optional=True)
        workflow.add_step("finish_splash", self.window_manager.finish_splash, [
                          "init_navigation"])
        workflow.add_step("connect_signals", self.connect_signals, [
                          "init_navigation"])
        workflow.add_step("initial_setup", self.handle_initial_setup, [
                          "connect_signals"], optional=True)

        # 执行工作流
        try:
            result = workflow.execute()
            if result["success"]:
                logger.info(f"应用程序初始化完成，耗时 {result['total_time']:.2f}s")
            else:
                logger.warning(f"应用程序初始化部分失败: {result['failed_steps']}")
        except Exception as e:
            logger.error(f"应用程序初始化失败: {e}")
            # 回退到传统初始化方式
            self._fallback_initialization()

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

    def _fallback_initialization(self) -> None:
        """回退初始化方式"""
        logger.info("使用传统初始化方式")
        try:
            self.theme_manager.init_theme()
            self.window_manager.init_main_window()
            self.navigation_manager.init_navigation()
            self.font_manager.handle_font_check()
            self.window_manager.finish_splash()
            self.connect_signals()
            self.handle_initial_setup()
            logger.info("传统初始化完成")
        except Exception as e:
            logger.critical(f"传统初始化也失败: {e}")
            raise

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
