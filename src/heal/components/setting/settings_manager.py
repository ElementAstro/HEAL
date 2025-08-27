import json
import sys
from typing import TYPE_CHECKING, Any, Dict

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

from src.heal.common.logging_config import get_logger
from src.heal.components.setting.error_handler import settings_error_handler, ErrorSeverity
from src.heal.components.setting.performance_manager import performance_optimized
from src.heal.models.check_update import check_update
from src.heal.models.config import Info, cfg, get_json
from src.heal.models.setting_card import CustomDialog, SettingCardGroup
from .error_handler import (
    ErrorSeverity,
    get_error_handler,
    settings_error_handler,
)
from .lazy_settings import get_lazy_manager
from .performance_manager import (
    get_performance_manager,
    performance_optimized,
)
from .setting_cards import LineEditSettingCardPort
from src.heal.components.tools.editor import JsonEditor

if TYPE_CHECKING:
    from ...interfaces.setting_interface import Setting


class SettingsManager(QObject):
    """Manages all setting cards and their operations with performance optimizations."""

    # Signals for performance monitoring
    interface_created = Signal(str)  # interface_name
    setting_changed = Signal(str, object)  # setting_key, value
    performance_stats = Signal(dict)  # performance statistics

    def __init__(self, parent_widget: "Setting") -> None:
        super().__init__(parent_widget)
        self.parent = parent_widget
        self.config_editor = JsonEditor()

        # Performance managers
        self.performance_manager = get_performance_manager()
        self.lazy_manager = get_lazy_manager()
        self.error_handler = get_error_handler()
        self.logger = get_logger("settings_manager", module="SettingsManager")

        # Interface cache for performance
        self._interface_cache: Dict[str, SettingCardGroup] = {}

        # Connect performance manager signals
        self.performance_manager.setting_saved.connect(self._on_setting_saved)

        self.logger.info("Performance-optimized settings manager initialized")

    def _on_setting_saved(self, setting_key: str, success: bool) -> None:
        """Handle setting saved signal from performance manager"""
        if success:
            self.setting_changed.emit(setting_key, True)
        else:
            self.logger.warning(f"Failed to save setting: {setting_key}")

    @performance_optimized
    def create_appearance_interface(self) -> SettingCardGroup:
        """Create appearance and display settings interface with caching."""
        cache_key = "appearance_interface"

        # Check cache first
        if cache_key in self._interface_cache:
            self.logger.debug("Using cached appearance interface")
            return self._interface_cache[cache_key]

        appearance_interface = SettingCardGroup(self.parent.scrollWidget)

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
            texts=["简体中文", "繁體中文", "English", self.parent.tr("跟随系统设置")],
        )

        # Add cards to interface - only appearance-related settings
        appearance_interface.addSettingCard(self.themeColorCard)
        appearance_interface.addSettingCard(self.zoomCard)
        appearance_interface.addSettingCard(self.languageCard)

        # Cache the interface for performance
        self._interface_cache[cache_key] = appearance_interface
        self.interface_created.emit("appearance")
        self.logger.debug("Created and cached appearance interface")

        return appearance_interface

    @performance_optimized
    def create_behavior_interface(self) -> SettingCardGroup:
        """Create application behavior settings interface with caching."""
        cache_key = "behavior_interface"

        if cache_key in self._interface_cache:
            self.logger.debug("Using cached behavior interface")
            return self._interface_cache[cache_key]

        behavior_interface = SettingCardGroup(self.parent.scrollWidget)

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

        # Cache the interface
        self._interface_cache[cache_key] = behavior_interface
        self.interface_created.emit("behavior")
        self.logger.debug("Created and cached behavior interface")

        return behavior_interface

    @performance_optimized
    def create_network_interface(self) -> SettingCardGroup:
        """Create network and connectivity settings interface with caching."""
        cache_key = "network_interface"

        if cache_key in self._interface_cache:
            self.logger.debug("Using cached network interface")
            return self._interface_cache[cache_key]

        network_interface = SettingCardGroup(self.parent.scrollWidget)

        # Proxy card
        self.proxyCard = SwitchSettingCard(
            FluentIcon.CERTIFICATE,
            self.parent.tr("使用代理端口"),
            self.parent.tr("启用代理，在配置文件里更改地址"),
            configItem=cfg.proxyStatus,
        )

        # Proxy port card
        self.proxyPortCard = LineEditSettingCardPort(self.parent.tr("代理端口"))

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

        # Cache the interface
        self._interface_cache[cache_key] = network_interface
        self.interface_created.emit("network")
        self.logger.debug("Created and cached network interface")

        return network_interface

    @performance_optimized
    def create_system_interface(self) -> SettingCardGroup:
        """Create system and maintenance settings interface with lazy loading."""
        cache_key = "system_interface"

        if cache_key in self._interface_cache:
            self.logger.debug("Using cached system interface")
            return self._interface_cache[cache_key]

        system_interface = SettingCardGroup(self.parent.scrollWidget)

        # Update card
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

        # Config editor card
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

        # Cache the interface
        self._interface_cache[cache_key] = system_interface
        self.interface_created.emit("system")
        self.logger.debug("Created and cached system interface")

        return system_interface

    def connect_signals(self) -> None:
        """Connect all setting card signals."""
        # Personal interface signals
        self.themeColorCard.colorChanged.connect(
            lambda c: setThemeColor(c, lazy=True))
        self.zoomCard.comboBox.currentIndexChanged.connect(
            self.restart_application)
        self.languageCard.comboBox.currentIndexChanged.connect(
            self.restart_application)
        self.updateOnStartUpCard.clicked.connect(
            lambda: check_update() if self.parent.parent_widget else check_update()
        )
        self.restartCard.clicked.connect(self.restart_application)
        self.configEditorCard.clicked.connect(self.open_config_editor)

        # Function interface signals
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

        # Proxy interface signals
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

    def restart_application(self) -> None:
        """Restart the application."""
        current_process = QProcess()
        current_process.startDetached(sys.executable, sys.argv)
        sys.exit()

    def open_config_editor(self) -> None:
        """Open the configuration editor."""
        self.config_editor_dialog = CustomDialog(self.config_editor)
        self.config_editor_dialog.show()

    def handle_choice_changed(self, status: Any, title_true: Any, title_false: Any) -> None:
        """Handle toggle setting changes."""
        if status:
            Info(self.parent, "S", 1000, title_true)
        else:
            Info(self.parent, "S", 1000, title_false)

    def handle_proxy_changed(self, status: Any, title_true: Any, title_false: Any) -> None:
        """Handle proxy setting changes."""
        if status:
            Info(self.parent, "S", 1000, title_true)
        else:
            Info(self.parent, "S", 1000, title_false)

        if cfg.chinaStatus.value and cfg.proxyStatus.value:
            Info(
                self.parent, "W", 3000, self.parent.tr("代理设置冲突,优先使用国内镜像!")
            )

        self.init_proxy_info()

    @settings_error_handler("handle_set_proxy_port", ErrorSeverity.MEDIUM)
    @performance_optimized
    def handle_set_proxy_port(self) -> None:
        """Handle proxy port setting with performance optimization and error handling."""
        new_port = self.proxyPortCard.port_edit.text()
        if new_port:
            # Use performance manager for optimized saving
            self.performance_manager.set_setting(
                "config/config.json",
                "PROXY_PORT",
                new_port,
                immediate=False,  # Use batching for better performance
            )

            # 复制到剪贴板
            clipboard: QClipboard = QApplication.clipboard()
            clipboard.setText(new_port)
            Info(self.parent, "S", 1000, self.parent.tr("代理端口已复制到剪贴板!"))

        self.init_proxy_info()

    @settings_error_handler("init_proxy_info", ErrorSeverity.LOW)
    def init_proxy_info(self) -> None:
        """Initialize proxy information display with caching."""
        # Use performance manager for cached access
        port = self.performance_manager.get_setting(
            "./config/config.json", "PROXY_PORT", "7890"  # default value
        )
        self.proxyPortCard.titleLabel.setText(
            self.parent.tr(f"代理端口 (当前: {port})")
        )
        self.proxyPortCard.setDisabled(not cfg.proxyStatus.value)

    def clear_cache(self) -> None:
        """Clear all cached interfaces and performance data"""
        self._interface_cache.clear()
        self.performance_manager.cache.clear()
        self.logger.info("Cleared all settings caches")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        perf_stats = self.performance_manager.get_performance_stats()
        lazy_stats = self.lazy_manager.get_loading_stats()
        error_stats = self.error_handler.get_error_statistics()

        return {
            "performance": perf_stats,
            "lazy_loading": lazy_stats,
            "error_handling": error_stats,
            "cached_interfaces": len(self._interface_cache),
        }

    def preload_interfaces(self) -> None:
        """Preload interfaces in background for better performance"""
        try:
            # Preload most commonly used interfaces
            self.lazy_manager.load_setting_async("appearance_interface")
            self.lazy_manager.load_setting_async("behavior_interface")
            self.logger.info("Started preloading interfaces")
        except Exception as e:
            self.logger.error(f"Error preloading interfaces: {e}")

    def cleanup(self) -> None:
        """Cleanup resources and save pending changes"""
        try:
            # Flush any pending saves
            self.performance_manager._flush_pending_saves()

            # Cleanup managers
            self.performance_manager.cleanup()
            self.lazy_manager.cleanup()

            # Clear caches
            self.clear_cache()

            self.logger.info("Settings manager cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
