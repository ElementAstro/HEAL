from typing import Any, TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon, Pivot, qrouter

from ...models.setting_card import SettingCardGroup
from .about_component import About

if TYPE_CHECKING:
    from ...interfaces.setting_interface import Setting


class SettingsLayoutManager:
    """Manages the layout and navigation for settings interface."""

    def __init__(self, parent_widget: "Setting") -> None:
        self.parent = parent_widget

    def create_navigation(self) -> Pivot:
        """Create the pivot navigation."""
        return Pivot(self.parent)

    def create_stacked_widget(self) -> QStackedWidget:
        """Create the stacked widget for content."""
        return QStackedWidget(self.parent)

    def setup_layout(self, pivot: Pivot, stacked_widget: QStackedWidget) -> None:
        """Setup the main layout with pivot and stacked widget."""
        self.parent.vBoxLayout.addWidget(pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.parent.vBoxLayout.addWidget(stacked_widget)
        self.parent.vBoxLayout.setSpacing(15)
        self.parent.vBoxLayout.setContentsMargins(0, 10, 10, 0)

    def add_sub_interface(
        self,
        pivot: Pivot,
        stacked_widget: QStackedWidget,
        widget: QWidget,
        object_name: str,
        text: str,
        icon: Any = None,
    ) -> None:
        """Add a sub-interface to the stacked widget and pivot."""
        widget.setObjectName(object_name)
        stacked_widget.addWidget(widget)
        pivot.addItem(
            icon=icon,
            routeKey=object_name,
            text=text,
            onClick=lambda: stacked_widget.setCurrentWidget(widget),
        )

    def setup_interfaces(
        self,
        pivot: Pivot,
        stacked_widget: QStackedWidget,
        appearance_interface: SettingCardGroup,
        behavior_interface: SettingCardGroup,
        network_interface: SettingCardGroup,
        system_interface: SettingCardGroup,
    ) -> None:
        """Setup all setting interfaces."""
        # Add interfaces to navigation with improved labels and icons
        self.add_sub_interface(
            pivot,
            stacked_widget,
            appearance_interface,
            "AppearanceInterface",
            self.parent.tr("外观显示"),
            icon=FluentIcon.PALETTE,
        )
        self.add_sub_interface(
            pivot,
            stacked_widget,
            behavior_interface,
            "BehaviorInterface",
            self.parent.tr("应用行为"),
            icon=FluentIcon.TILES,
        )
        self.add_sub_interface(
            pivot,
            stacked_widget,
            network_interface,
            "NetworkInterface",
            self.parent.tr("网络连接"),
            icon=FluentIcon.CERTIFICATE,
        )
        self.add_sub_interface(
            pivot,
            stacked_widget,
            system_interface,
            "SystemInterface",
            self.parent.tr("系统维护"),
            icon=FluentIcon.SETTING,
        )

        # Create and add about interface
        about_interface = About("AboutInterface", self.parent)
        self.add_sub_interface(
            pivot,
            stacked_widget,
            about_interface,
            "AboutInterface",
            self.parent.tr("关于"),
            icon=FluentIcon.INFO,
        )

        # Setup navigation callbacks
        stacked_widget.currentChanged.connect(
            lambda index: self.on_current_index_changed(
                pivot, stacked_widget, index)
        )

        # Set default interface to appearance (most frequently used)
        stacked_widget.setCurrentWidget(appearance_interface)
        pivot.setCurrentItem(appearance_interface.objectName())
        qrouter.setDefaultRouteKey(
            stacked_widget, appearance_interface.objectName())

    def on_current_index_changed(
        self, pivot: Pivot, stacked_widget: QStackedWidget, index: int
    ) -> None:
        """Handle navigation index changes."""
        widget = stacked_widget.widget(index)
        pivot.setCurrentItem(widget.objectName())
        qrouter.push(stacked_widget, widget.objectName())
