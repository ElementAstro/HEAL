import json
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import Pivot, ScrollArea, qrouter

from src.heal.common.logging_config import get_logger, log_performance, with_correlation_id
from src.heal.components.setting import SettingsLayoutManager, SettingsManager
from src.heal.components.setting.search_integration import (
    SearchEnabledSettingsInterface,
    get_search_integrator,
)
from src.heal.models.config import cfg
from src.heal.models.style_sheet import StyleSheet

# 使用统一日志配置
logger = get_logger("setting_interface")


class Setting(ScrollArea, SearchEnabledSettingsInterface):
    """Main settings interface with navigation, different setting categories, and search functionality."""

    Nav = Pivot

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent=parent)
        self.parent_widget = parent  # 重命名避免与QWidget.parent()冲突
        self.setObjectName(text)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        # Initialize search functionality
        self.search_integrator = get_search_integrator()
        self.search_widget = self.search_integrator.get_search_widget()

        logger.info(f"初始化设置界面: {text}")

        # Initialize components
        self.settings_manager = SettingsManager(self)
        self.layout_manager = SettingsLayoutManager(self)

        # 栏定义
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        self.__initWidget()

        # Initialize search functionality after UI is set up
        self._setup_search_integration()

        logger.debug("设置界面初始化完成")

    def __initWidget(self) -> None:
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )  # 水平滚动条关闭
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)  # 必须设置！！！

        # 使用qss设置样式
        self.scrollWidget.setObjectName("scrollWidget")
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()
        self.__initInfo()
        self.__connectSignalToSlot()

    def __initLayout(self) -> None:
        # Add search widget to the top of the layout
        self.vBoxLayout.addWidget(self.search_widget)

        # Create setting interfaces using manager with new logical groupings
        self.AppearanceInterface = self.settings_manager.create_appearance_interface()
        self.BehaviorInterface = self.settings_manager.create_behavior_interface()
        self.NetworkInterface = self.settings_manager.create_network_interface()
        self.SystemInterface = self.settings_manager.create_system_interface()

        # Setup layout using layout manager
        self.layout_manager.setup_layout(self.pivot, self.stackedWidget)
        self.layout_manager.setup_interfaces(
            self.pivot,
            self.stackedWidget,
            self.AppearanceInterface,
            self.BehaviorInterface,
            self.NetworkInterface,
            self.SystemInterface,
        )

    def __initInfo(self) -> None:
        self.settings_manager.init_proxy_info()

    def __connectSignalToSlot(self) -> None:
        self.settings_manager.connect_signals()

        # Connect search signals
        self.search_integrator.search_mode_changed.connect(self.on_search_mode_changed)
        self.search_integrator.setting_found.connect(self.on_setting_found)

    def addSubInterface(self, widget: QWidget, objectName: str, text: str, icon=None) -> None:
        """Legacy method for compatibility."""
        self.layout_manager.add_sub_interface(
            self.pivot, self.stackedWidget, widget, objectName, text, icon
        )

    def _setup_search_integration(self) -> None:
        """Setup search integration with all interfaces"""
        try:
            # Register all interfaces for search
            interfaces = {
                "Appearance": self.AppearanceInterface,
                "Behavior": self.BehaviorInterface,
                "Network": self.NetworkInterface,
                "System": self.SystemInterface,
            }

            for name, interface in interfaces.items():
                self.search_integrator.register_setting_interface(name, interface)

            logger.info(f"Registered {len(interfaces)} interfaces for search")

        except Exception as e:
            logger.error(f"Failed to setup search integration: {e}")

    def on_search_mode_changed(self, is_search_active: bool) -> None:
        """Handle search mode changes"""
        try:
            if is_search_active:
                # Hide normal navigation when search is active
                self.pivot.hide()
                self.stackedWidget.hide()
                logger.debug("Entered search mode")
            else:
                # Show normal navigation when search is inactive
                self.pivot.show()
                self.stackedWidget.show()
                logger.debug("Exited search mode")

        except Exception as e:
            logger.error(f"Error handling search mode change: {e}")

    def on_setting_found(self, setting_key: str, widget) -> None:
        """Handle setting found from search"""
        try:
            # Exit search mode
            self.search_widget.clear_search()

            # Find which interface contains this widget
            interfaces = [
                ("Appearance", self.AppearanceInterface),
                ("Behavior", self.BehaviorInterface),
                ("Network", self.NetworkInterface),
                ("System", self.SystemInterface),
            ]

            for interface_name, interface in interfaces:
                if self._widget_in_interface(widget, interface):
                    # Switch to the appropriate interface
                    self.stackedWidget.setCurrentWidget(interface)
                    self.pivot.setCurrentItem(interface.objectName())

                    # Scroll to the widget
                    self._scroll_to_widget(widget)

                    logger.info(
                        f"Navigated to {interface_name} interface for setting: {setting_key}"
                    )
                    break

        except Exception as e:
            logger.error(f"Error navigating to setting: {e}")

    def _widget_in_interface(self, widget, interface) -> bool:
        """Check if a widget is in the given interface"""
        try:
            # Check if widget is a child of the interface
            parent = widget.parent()
            while parent:
                if parent == interface:
                    return True
                parent = parent.parent()
            return False
        except Exception:
            return False

    def _scroll_to_widget(self, widget) -> None:
        """Scroll to make the widget visible"""
        try:
            # Ensure the widget is visible in the scroll area
            self.ensureWidgetVisible(widget)
        except Exception as e:
            logger.debug(f"Could not scroll to widget: {e}")

    def get_search_statistics(self) -> None:
        """Get search statistics for debugging"""
        return self.search_integrator.get_search_statistics()

    def onCurrentIndexChanged(self, index) -> None:
        """Legacy method for compatibility."""
        self.layout_manager.on_current_index_changed(
            self.pivot, self.stackedWidget, index
        )
