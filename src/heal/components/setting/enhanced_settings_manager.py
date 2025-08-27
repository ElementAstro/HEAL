"""
Enhanced Settings Manager with Performance Optimizations
Integrates caching, lazy loading, and error handling
"""

import json
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from PySide6.QtCore import QObject, QProcess, Signal
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets import (
    ComboBoxSettingCard,
    CustomColorSettingCard,
    FluentIcon,
    PrimaryPushSettingCard,
    SwitchSettingCard,
    setThemeColor,
)

from src.heal.common.json_utils import JsonUtils
from src.heal.common.logging_config import get_logger
from src.heal.models.check_update import check_update
from src.heal.models.config import Info, cfg
from src.heal.models.setting_card import CustomDialog, SettingCardGroup
from .performance_manager import (
    SettingsPerformanceManager,
    get_performance_manager,
    performance_optimized,
)
from .setting_cards import LineEditSettingCardPort
from src.heal.components.tools.editor import JsonEditor

if TYPE_CHECKING:
    from ...interfaces.setting_interface import Setting


class EnhancedSettingsManager(QObject):
    """Enhanced settings manager with performance optimizations and error handling."""

    # Signals for async operations
    setting_loaded = Signal(str, object)
    setting_saved = Signal(str, bool)
    error_occurred = Signal(str, str)

    def __init__(self, parent_widget: "Setting") -> None:
        super().__init__(parent_widget)
        self.parent = parent_widget
        self.config_editor = JsonEditor()
        self.performance_manager = get_performance_manager()
        self.logger = get_logger(
            "enhanced_settings_manager", module="EnhancedSettingsManager"
        )

        # Connect performance manager signals
        self.performance_manager.setting_saved.connect(self.setting_saved)
        self.performance_manager.error_occurred.connect(self.error_occurred)

        # Cache for expensive operations
        self._interface_cache: Dict[str, SettingCardGroup] = {}

        # 优化：添加操作去重缓存
        self._operation_cache: Dict[str, Any] = {}
        self._last_cache_cleanup = time.time()

        # Register lazy loading for complex settings
        self._register_lazy_settings()

        self.logger.info("Enhanced settings manager initialized")

    def _register_lazy_settings(self) -> None:
        """Register settings that should be loaded lazily"""
        # Register config editor as lazy-loaded
        self.performance_manager.register_lazy_setting(
            "config_editor", lambda: JsonEditor()
        )

        # Register update checker as lazy-loaded
        self.performance_manager.register_lazy_setting(
            "update_checker", lambda: self._initialize_update_checker()
        )

    def _initialize_update_checker(self) -> Any:
        """Initialize update checker lazily"""
        try:
            # Perform expensive update check initialization
            return check_update
        except Exception as e:
            self.logger.error(f"Failed to initialize update checker: {e}")
            return None

    def _get_cached_operation(self, operation_key: str, operation_func: Any, *args: Any, **kwargs: Any) -> Any:
        """获取缓存的操作结果，避免重复计算"""
        current_time = time.time()

        # 定期清理缓存
        if current_time - self._last_cache_cleanup > 300:  # 5分钟清理一次
            self._cleanup_operation_cache()
            self._last_cache_cleanup = current_time

        # 检查缓存
        if operation_key in self._operation_cache:
            cached_result, timestamp = self._operation_cache[operation_key]
            # 缓存有效期1分钟
            if current_time - timestamp < 60:
                self.logger.debug(f"使用缓存结果: {operation_key}")
                return cached_result

        # 执行操作并缓存结果
        try:
            result = operation_func(*args, **kwargs)
            self._operation_cache[operation_key] = (result, current_time)
            return result
        except Exception as e:
            self.logger.error(f"操作 {operation_key} 执行失败: {e}")
            return None

    def _cleanup_operation_cache(self) -> None:
        """清理过期的操作缓存"""
        current_time = time.time()
        expired_keys = []

        for key, (result, timestamp) in self._operation_cache.items():
            if current_time - timestamp > 300:  # 5分钟过期
                expired_keys.append(key)

        for key in expired_keys:
            del self._operation_cache[key]

        if expired_keys:
            self.logger.debug(f"清理了 {len(expired_keys)} 个过期缓存")

    @performance_optimized
    def create_appearance_interface(self) -> SettingCardGroup:
        """Create appearance and display settings interface with caching."""
        cache_key = "appearance_interface"

        # Check cache first
        if cache_key in self._interface_cache:
            self.logger.debug("Using cached appearance interface")
            return self._interface_cache[cache_key]

        appearance_interface = SettingCardGroup(self.parent.scrollWidget)

        try:
            # Theme color card
            self.themeColorCard = CustomColorSettingCard(
                cfg.themeColor,
                FluentIcon.PALETTE,
                self.parent.tr("主题色"),
                self.parent.tr("默认流萤主题色，开拓者你不会改的吧?"),
            )

            # DPI scale card
            self.zoomCard = ComboBoxSettingCard(
                cfg.dpiScale,
                FluentIcon.ZOOM,
                "DPI",
                self.parent.tr("调整全局缩放"),
                texts=[
                    "100%",
                    "125%",
                    "150%",
                    "175%",
                    "200%",
                    self.parent.tr("跟随系统设置"),
                ],
            )

            # Language card
            self.languageCard = ComboBoxSettingCard(
                cfg.language,
                FluentIcon.LANGUAGE,
                self.parent.tr("语言"),
                self.parent.tr("界面显示语言"),
                texts=[
                    "简体中文",
                    "繁體中文",
                    "English",
                    self.parent.tr("跟随系统设置"),
                ],
            )

            # Add cards to interface
            appearance_interface.addSettingCard(self.themeColorCard)
            appearance_interface.addSettingCard(self.zoomCard)
            appearance_interface.addSettingCard(self.languageCard)

            # Cache the interface
            self._interface_cache[cache_key] = appearance_interface
            self.logger.debug("Created and cached appearance interface")

        except Exception as e:
            self.logger.error(f"Error creating appearance interface: {e}")
            self.error_occurred.emit("create_appearance_interface", str(e))

        return appearance_interface

    @performance_optimized
    def create_behavior_interface(self) -> SettingCardGroup:
        """Create application behavior settings interface with caching."""
        cache_key = "behavior_interface"

        if cache_key in self._interface_cache:
            self.logger.debug("Using cached behavior interface")
            return self._interface_cache[cache_key]

        behavior_interface = SettingCardGroup(self.parent.scrollWidget)

        try:
            # Auto copy card
            self.autoCopyCard = SwitchSettingCard(
                FluentIcon.COPY,
                self.parent.tr("命令自动复制"),
                self.parent.tr("选择命令时，自动复制命令到剪贴板"),
                configItem=cfg.autoCopy,
            )

            # Login card
            self.useLoginCard = SwitchSettingCard(
                FluentIcon.PENCIL_INK,
                self.parent.tr("启用登录功能"),
                self.parent.tr("使用自定义登陆彩蛋"),
                configItem=cfg.useLogin,
            )

            # Audio card
            self.useAudioCard = SwitchSettingCard(
                FluentIcon.MUSIC,
                self.parent.tr("启用流萤语音"),
                self.parent.tr("使用随机流萤语音彩蛋"),
                configItem=cfg.useAudio,
            )

            # Add cards to interface
            behavior_interface.addSettingCard(self.autoCopyCard)
            behavior_interface.addSettingCard(self.useLoginCard)
            behavior_interface.addSettingCard(self.useAudioCard)

            self._interface_cache[cache_key] = behavior_interface
            self.logger.debug("Created and cached behavior interface")

        except Exception as e:
            self.logger.error(f"Error creating behavior interface: {e}")
            self.error_occurred.emit("create_behavior_interface", str(e))

        return behavior_interface

    @performance_optimized
    def create_network_interface(self) -> SettingCardGroup:
        """Create network and connectivity settings interface with caching."""
        cache_key = "network_interface"

        if cache_key in self._interface_cache:
            self.logger.debug("Using cached network interface")
            return self._interface_cache[cache_key]

        network_interface = SettingCardGroup(self.parent.scrollWidget)

        try:
            # Proxy card
            self.proxyCard = SwitchSettingCard(
                FluentIcon.CERTIFICATE,
                self.parent.tr("使用代理端口"),
                self.parent.tr("启用代理，在配置文件里更改地址"),
                configItem=cfg.proxyStatus,
            )

            # Proxy port card
            self.proxyPortCard = LineEditSettingCardPort(
                self.parent.tr("代理端口"))

            # China mirror card
            self.chinaCard = SwitchSettingCard(
                FluentIcon.CALORIES,
                self.parent.tr("使用国内镜像"),
                self.parent.tr("为Github下载启用国内镜像站链接"),
                configItem=cfg.chinaStatus,
            )

            # Add cards to interface
            network_interface.addSettingCard(self.proxyCard)
            network_interface.addSettingCard(self.proxyPortCard)
            network_interface.addSettingCard(self.chinaCard)

            self._interface_cache[cache_key] = network_interface
            self.logger.debug("Created and cached network interface")

        except Exception as e:
            self.logger.error(f"Error creating network interface: {e}")
            self.error_occurred.emit("create_network_interface", str(e))

        return network_interface

    @performance_optimized
    def create_system_interface(self) -> SettingCardGroup:
        """Create system and maintenance settings interface with lazy loading."""
        cache_key = "system_interface"

        if cache_key in self._interface_cache:
            self.logger.debug("Using cached system interface")
            return self._interface_cache[cache_key]

        system_interface = SettingCardGroup(self.parent.scrollWidget)

        try:
            # Update card - lazy loaded
            self.updateOnStartUpCard = PrimaryPushSettingCard(
                self.parent.tr("检查更新"),
                FluentIcon.UPDATE,
                self.parent.tr("手动检查更新"),
                self.parent.tr("当前版本 : ") + cfg.APP_VERSION,
            )

            # Restart card
            self.restartCard = PrimaryPushSettingCard(
                self.parent.tr("重启程序"),
                FluentIcon.ROTATE,
                self.parent.tr("重启程序"),
                self.parent.tr("无奖竞猜，存在即合理"),
            )

            # Config editor card - lazy loaded
            self.configEditorCard = PrimaryPushSettingCard(
                self.parent.tr("打开配置"),
                FluentIcon.PENCIL_INK,
                self.parent.tr("打开配置"),
                self.parent.tr("自实现Json编辑器"),
            )

            # Add cards to interface
            system_interface.addSettingCard(self.updateOnStartUpCard)
            system_interface.addSettingCard(self.restartCard)
            system_interface.addSettingCard(self.configEditorCard)

            self._interface_cache[cache_key] = system_interface
            self.logger.debug("Created and cached system interface")

        except Exception as e:
            self.logger.error(f"Error creating system interface: {e}")
            self.error_occurred.emit("create_system_interface", str(e))

        return system_interface

    def connect_signals(self) -> None:
        """Connect all setting card signals with error handling."""
        try:
            # Appearance interface signals
            self.themeColorCard.colorChanged.connect(
                lambda c: setThemeColor(c, lazy=True)
            )
            self.zoomCard.comboBox.currentIndexChanged.connect(
                self.restart_application)
            self.languageCard.comboBox.currentIndexChanged.connect(
                self.restart_application
            )

            # System interface signals with lazy loading
            self.updateOnStartUpCard.clicked.connect(self._handle_update_check)
            self.restartCard.clicked.connect(self.restart_application)
            self.configEditorCard.clicked.connect(self._handle_config_editor)

            # Behavior interface signals
            self.autoCopyCard.checkedChanged.connect(
                lambda: self.handle_choice_changed(
                    cfg.autoCopy.value,
                    self.parent.tr("自动复制已开启!"),
                    self.parent.tr("自动复制已关闭!"),
                )
            )
            self.useLoginCard.checkedChanged.connect(
                lambda: self.handle_choice_changed(
                    cfg.useLogin.value,
                    self.parent.tr("登录功能已开启!"),
                    self.parent.tr("登录功能已关闭!"),
                )
            )
            self.useAudioCard.checkedChanged.connect(
                lambda: self.handle_choice_changed(
                    cfg.useAudio.value,
                    self.parent.tr("流萤语音已开启!"),
                    self.parent.tr("流萤语音已关闭!"),
                )
            )

            # Network interface signals
            self.proxyCard.checkedChanged.connect(
                lambda: self.handle_proxy_changed(
                    cfg.proxyStatus.value,
                    self.parent.tr("代理端口已开启!"),
                    self.parent.tr("代理端口已关闭!"),
                )
            )
            self.chinaCard.checkedChanged.connect(
                lambda: self.handle_proxy_changed(
                    cfg.chinaStatus.value,
                    self.parent.tr("国内镜像已开启!"),
                    self.parent.tr("国内镜像已关闭!"),
                )
            )
            self.proxyPortCard.set_port.connect(self.handle_set_proxy_port)

            self.logger.debug("All signals connected successfully")

        except Exception as e:
            self.logger.error(f"Error connecting signals: {e}")
            self.error_occurred.emit("connect_signals", str(e))

    def _handle_update_check(self) -> None:
        """Handle update check with lazy loading"""
        try:
            update_checker = self.performance_manager.load_lazy_setting(
                "update_checker"
            )
            if update_checker:
                if self.parent.parent_widget:
                    update_checker()
                else:
                    update_checker()
            else:
                self.logger.warning("Update checker not available")
                Info(self.parent, "W", 3000, self.parent.tr("更新检查功能暂时不可用"))
        except Exception as e:
            self.logger.error(f"Error in update check: {e}")
            self.error_occurred.emit("update_check", str(e))

    def _handle_config_editor(self) -> None:
        """Handle config editor with lazy loading"""
        try:
            config_editor = self.performance_manager.load_lazy_setting(
                "config_editor")
            if config_editor:
                self.config_editor_dialog = CustomDialog(config_editor)
                self.config_editor_dialog.show()
            else:
                # Fallback to regular config editor
                self.config_editor_dialog = CustomDialog(self.config_editor)
                self.config_editor_dialog.show()
        except Exception as e:
            self.logger.error(f"Error opening config editor: {e}")
            self.error_occurred.emit("config_editor", str(e))

    def restart_application(self) -> None:
        """Restart the application with error handling."""
        try:
            # Flush any pending saves before restart
            self.performance_manager._flush_pending_saves()

            current_process = QProcess()
            current_process.startDetached(sys.executable, sys.argv)
            sys.exit()
        except Exception as e:
            self.logger.error(f"Error restarting application: {e}")
            self.error_occurred.emit("restart_application", str(e))

    def handle_choice_changed(self, status: Any, title_true: Any, title_false: Any) -> None:
        """Handle toggle setting changes with error handling."""
        try:
            if status:
                Info(self.parent, "S", 1000, title_true)
            else:
                Info(self.parent, "S", 1000, title_false)
        except Exception as e:
            self.logger.error(f"Error handling choice change: {e}")
            self.error_occurred.emit("handle_choice_changed", str(e))

    def handle_proxy_changed(self, status: Any, title_true: Any, title_false: Any) -> None:
        """Handle proxy setting changes with error handling."""
        try:
            if status:
                Info(self.parent, "S", 1000, title_true)
            else:
                Info(self.parent, "S", 1000, title_false)

            if cfg.chinaStatus.value and cfg.proxyStatus.value:
                Info(
                    self.parent,
                    "W",
                    3000,
                    self.parent.tr("代理设置冲突,优先使用国内镜像!"),
                )

            self.init_proxy_info()
        except Exception as e:
            self.logger.error(f"Error handling proxy change: {e}")
            self.error_occurred.emit("handle_proxy_changed", str(e))

    @performance_optimized
    def handle_set_proxy_port(self) -> None:
        """Handle proxy port setting with performance optimization."""
        try:
            new_port = self.proxyPortCard.port_edit.text()
            if new_port:
                # Use performance manager for optimized saving
                self.performance_manager.set_setting(
                    "config/config.json",
                    "PROXY_PORT",
                    new_port,
                    immediate=False,  # Use batching
                )

                # Copy to clipboard
                clipboard: QClipboard = QApplication.clipboard()
                clipboard.setText(new_port)
                Info(self.parent, "S", 1000, self.parent.tr("代理端口已复制到剪贴板!"))

            self.init_proxy_info()
        except Exception as e:
            self.logger.error(f"Error setting proxy port: {e}")
            self.error_occurred.emit("handle_set_proxy_port", str(e))

    def init_proxy_info(self) -> None:
        """Initialize proxy information display with caching."""
        try:
            # Use performance manager for cached access
            port = self.performance_manager.get_setting(
                "./config/config.json", "PROXY_PORT", "7890"  # default value
            )
            self.proxyPortCard.titleLabel.setText(
                self.parent.tr(f"代理端口 (当前: {port})")
            )
            self.proxyPortCard.setDisabled(not cfg.proxyStatus.value)
        except Exception as e:
            self.logger.error(f"Error initializing proxy info: {e}")
            self.error_occurred.emit("init_proxy_info", str(e))

    def clear_cache(self) -> None:
        """Clear all cached interfaces and data"""
        self._interface_cache.clear()
        self.performance_manager.cache.clear()
        self.logger.info("Cleared all caches")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_manager.get_performance_stats()

    def cleanup(self) -> None:
        """Cleanup resources"""
        self.performance_manager.cleanup()
        self.clear_cache()
        self.logger.info("Enhanced settings manager cleaned up")
