import sys
import time

from PySide6.QtCore import Signal
from qfluentwidgets import MSFluentWindow

from src.heal.common.logging_config import get_logger

from typing import Any, Optional, Callable

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

        # 初始化用户引导系统
        self.onboarding_manager: Optional[Any] = None

        # Initialize tray_icon as None initially
        self.tray_icon: Any = None

        # 初始化应用
        self.init_application()

    def init_application(self) -> None:
        """初始化应用程序 - Enhanced with performance monitoring"""
        from src.heal.common.workflow_optimizer import create_workflow
        from src.heal.common.startup_performance_monitor import record_startup_phase

        # 创建应用初始化工作流 - 启用性能跟踪
        workflow = create_workflow("main_app_initialization", enable_performance_tracking=True)

        # 添加初始化步骤 - 包装每个步骤以记录性能
        workflow.add_step("init_theme", self._wrap_with_monitoring(
            self.theme_manager.init_theme, "theme_init"))
        workflow.add_step(
            "init_window", self._wrap_with_monitoring(
                self.window_manager.init_main_window, "window_init"), ["init_theme"])
        workflow.add_step(
            "init_navigation", self._wrap_with_monitoring(
                self.navigation_manager.init_navigation, "navigation_init"), ["init_window"])
        workflow.add_step(
            "check_fonts", self._wrap_with_monitoring(
                self.font_manager.handle_font_check, "font_check"), optional=True)
        workflow.add_step("finish_splash", self._wrap_with_monitoring(
            self.window_manager.finish_splash, "splash_finish"), ["init_navigation"])
        workflow.add_step("connect_signals", self._wrap_with_monitoring(
            self.connect_signals, "signal_connection"), ["init_navigation"])
        workflow.add_step("initial_setup", self._wrap_with_monitoring(
            self.handle_initial_setup, "initial_setup"), ["connect_signals"], optional=True)
        workflow.add_step("init_onboarding", self._wrap_with_monitoring(
            self.init_onboarding_system, "onboarding_init"), ["initial_setup"], optional=True)
        workflow.add_step("init_progressive", self._wrap_with_monitoring(
            self.init_progressive_loading, "progressive_loading"), ["init_onboarding"], optional=True)

        # 执行工作流
        try:
            result = workflow.execute()
            if result["success"]:
                logger.info(f"应用程序初始化完成，耗时 {result['total_time']:.2f}s")

                # 获取性能报告
                performance_report = workflow.get_performance_report()
                if performance_report.get("bottleneck_steps"):
                    logger.warning(f"发现初始化瓶颈: {[step['step_name'] for step in performance_report['bottleneck_steps']]}")

            else:
                logger.warning(f"应用程序初始化部分失败: {result['failed_steps']}")
        except Exception as e:
            logger.error(f"应用程序初始化失败: {e}")
            # 回退到传统初始化方式
            self._fallback_initialization()

    def _wrap_with_monitoring(self, func: Callable[[], Any], phase_name: str) -> Callable[[], Any]:
        """包装函数以添加性能监控"""
        from src.heal.common.startup_performance_monitor import record_startup_phase

        def wrapped_func() -> Any:
            record_startup_phase(phase_name, start=True)
            try:
                result = func()
                record_startup_phase(phase_name, start=False, success=True)
                return result
            except Exception as e:
                record_startup_phase(phase_name, start=False, success=False, error=str(e))
                raise

        return wrapped_func

    def init_progressive_loading(self) -> None:
        """初始化渐进式加载系统"""
        from src.heal.common.progressive_loader import (
            progressive_loading_manager, register_progressive_component,
            LoadingPhase, start_progressive_loading
        )
        from src.heal.common.deferred_initializer import (
            deferred_initializer, InitializationTrigger, initialize_deferred_features
        )

        try:
            # Register non-critical components for progressive loading
            self._register_progressive_components()

            # Register deferred features
            self._register_deferred_features()

            # Start progressive loading system
            start_progressive_loading()

            # Initialize system-ready features
            initialize_deferred_features(InitializationTrigger.SYSTEM_READY)

            self.logger.info("Progressive loading system initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize progressive loading: {e}")

    def _register_progressive_components(self) -> None:
        """注册渐进式加载组件"""
        from src.heal.common.progressive_loader import (
            register_progressive_component, LoadingPhase
        )

        # Register non-critical UI components
        register_progressive_component(
            "advanced_settings",
            "高级设置面板",
            self._load_advanced_settings,
            LoadingPhase.USER_IDLE,
            priority=3,
            essential=False,
            description="Load advanced settings panel when user is idle"
        )

        register_progressive_component(
            "help_system",
            "帮助系统",
            self._load_help_system,
            LoadingPhase.ON_DEMAND,
            priority=4,
            essential=False,
            description="Load help system on demand"
        )

        register_progressive_component(
            "plugin_manager",
            "插件管理器",
            self._load_plugin_manager,
            LoadingPhase.BACKGROUND,
            priority=5,
            essential=False,
            description="Load plugin manager in background"
        )

        register_progressive_component(
            "analytics_system",
            "分析系统",
            self._load_analytics_system,
            LoadingPhase.BACKGROUND,
            priority=6,
            essential=False,
            description="Load analytics system in background"
        )

    def _register_deferred_features(self) -> None:
        """注册延迟初始化功能"""
        from src.heal.common.deferred_initializer import (
            register_deferred_feature, InitializationTrigger
        )

        # Register optional features that can be loaded later
        register_deferred_feature(
            "auto_updater",
            "自动更新器",
            self._init_auto_updater,
            InitializationTrigger.SYSTEM_READY,
            timeout=10.0,
            optional=True,
            description="Initialize auto-updater when system is ready"
        )

        register_deferred_feature(
            "crash_reporter",
            "崩溃报告器",
            self._init_crash_reporter,
            InitializationTrigger.FIRST_ACCESS,
            timeout=5.0,
            optional=True,
            description="Initialize crash reporter on first access"
        )

        register_deferred_feature(
            "telemetry_system",
            "遥测系统",
            self._init_telemetry_system,
            InitializationTrigger.USER_ACTION,
            timeout=15.0,
            optional=True,
            description="Initialize telemetry when user performs action"
        )

    # Progressive loading component loaders
    def _load_advanced_settings(self) -> Any:
        """加载高级设置面板"""
        # Simulate loading advanced settings
        time.sleep(0.5)  # Simulate loading time
        self.logger.debug("Advanced settings panel loaded")
        return {"component": "advanced_settings", "loaded": True}

    def _load_help_system(self) -> Any:
        """加载帮助系统"""
        # Simulate loading help system
        time.sleep(0.3)
        self.logger.debug("Help system loaded")
        return {"component": "help_system", "loaded": True}

    def _load_plugin_manager(self) -> Any:
        """加载插件管理器"""
        # Simulate loading plugin manager
        time.sleep(1.0)
        self.logger.debug("Plugin manager loaded")
        return {"component": "plugin_manager", "loaded": True}

    def _load_analytics_system(self) -> Any:
        """加载分析系统"""
        # Simulate loading analytics system
        time.sleep(0.8)
        self.logger.debug("Analytics system loaded")
        return {"component": "analytics_system", "loaded": True}

    # Deferred feature initializers
    def _init_auto_updater(self) -> Any:
        """初始化自动更新器"""
        # Simulate auto-updater initialization
        time.sleep(0.2)
        self.logger.debug("Auto-updater initialized")
        return {"feature": "auto_updater", "initialized": True}

    def _init_crash_reporter(self) -> Any:
        """初始化崩溃报告器"""
        # Simulate crash reporter initialization
        time.sleep(0.1)
        self.logger.debug("Crash reporter initialized")
        return {"feature": "crash_reporter", "initialized": True}

    def _init_telemetry_system(self) -> Any:
        """初始化遥测系统"""
        # Simulate telemetry system initialization
        time.sleep(0.3)
        self.logger.debug("Telemetry system initialized")
        return {"feature": "telemetry_system", "initialized": True}

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
        """回退初始化方式 - Enhanced with recovery strategies"""
        from src.heal.common.fallback_initializer import (
            attempt_component_recovery, get_fallback_recovery_report
        )

        logger.warning("使用增强回退初始化方式")

        components_to_init = [
            ("theme", self.theme_manager.init_theme),
            ("window", self.window_manager.init_main_window),
            ("navigation", self.navigation_manager.init_navigation),
            ("fonts", self.font_manager.handle_font_check),
            ("splash", self.window_manager.finish_splash),
            ("signals", self.connect_signals),
            ("initial_setup", self.handle_initial_setup),
            ("onboarding", self.init_onboarding_system)
        ]

        successful_components = []
        failed_components = []

        for component_id, init_func in components_to_init:
            try:
                logger.debug(f"Fallback initialization: {component_id}")
                init_func()
                successful_components.append(component_id)

            except Exception as e:
                logger.error(f"Fallback initialization failed for {component_id}: {e}")

                # Attempt recovery using fallback system
                try:
                    from src.heal.common.fallback_initializer import RecoveryResult
                    recovery_result = attempt_component_recovery(component_id, e)

                    if recovery_result in [RecoveryResult.SUCCESS, RecoveryResult.PARTIAL_SUCCESS]:
                        logger.info(f"Successfully recovered {component_id} using fallback")
                        successful_components.append(f"{component_id}_recovered")
                    elif recovery_result == RecoveryResult.SKIPPED:
                        logger.info(f"Skipped {component_id} - continuing without it")
                        successful_components.append(f"{component_id}_skipped")
                    else:
                        failed_components.append(component_id)

                except Exception as recovery_error:
                    logger.error(f"Recovery failed for {component_id}: {recovery_error}")
                    failed_components.append(component_id)

        # Generate recovery report
        recovery_report = get_fallback_recovery_report()

        if successful_components:
            logger.info(f"Fallback initialization completed. "
                       f"Successful: {len(successful_components)}, "
                       f"Failed: {len(failed_components)}")

            if recovery_report["recovery_stats"]["successful_recoveries"] > 0:
                logger.info(f"Recovery statistics: "
                           f"{recovery_report['recovery_stats']['successful_recoveries']} successful, "
                           f"{recovery_report['recovery_stats']['failed_recoveries']} failed")
        else:
            logger.critical("所有回退初始化都失败了")
            self._emergency_initialization()

    def _emergency_initialization(self) -> None:
        """紧急初始化 - 最基本的功能"""
        logger.critical("启动紧急初始化模式")

        try:
            # 只初始化最基本的功能
            from PySide6.QtWidgets import QMessageBox, QApplication

            # 显示紧急模式对话框
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("HEAL - 紧急模式")
            msg.setText("应用程序遇到严重问题，已启动紧急模式。\n\n"
                       "某些功能可能不可用。请检查日志文件获取详细信息。")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Close)

            result = msg.exec()
            if result == QMessageBox.StandardButton.Close:
                QApplication.quit()

            logger.info("紧急初始化完成")

        except Exception as e:
            logger.critical(f"紧急初始化失败: {e}")
            # 最后的手段 - 直接退出
            import sys
            sys.exit(1)

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

    def init_onboarding_system(self) -> None:
        """初始化用户引导系统"""
        try:
            from src.heal.components.onboarding import OnboardingManager

            self.onboarding_manager = OnboardingManager(self)

            # 连接引导系统信号
            self.onboarding_manager.welcome_wizard_requested.connect(self._show_welcome_wizard)
            self.onboarding_manager.tutorial_requested.connect(self._start_tutorial)
            self.onboarding_manager.onboarding_completed.connect(self._handle_onboarding_completed)

            logger.info("用户引导系统已初始化")

        except Exception as e:
            logger.error(f"初始化用户引导系统失败: {e}")

    def _show_welcome_wizard(self) -> None:
        """显示欢迎向导"""
        try:
            if self.onboarding_manager:
                self.onboarding_manager.start_welcome_wizard()
        except Exception as e:
            logger.error(f"显示欢迎向导失败: {e}")

    def _start_tutorial(self, tutorial_id: str) -> None:
        """启动教程"""
        try:
            if self.onboarding_manager:
                self.onboarding_manager.start_tutorial(tutorial_id)
        except Exception as e:
            logger.error(f"启动教程失败: {e}")

    def _handle_onboarding_completed(self) -> None:
        """处理引导完成"""
        logger.info("用户引导已完成")
        # 可以在这里添加引导完成后的逻辑

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
