from typing import TYPE_CHECKING
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt
from qfluentwidgets import Pivot, qrouter, FluentIcon
from app.model.setting_card import SettingCardGroup
from app.components.setting.about_component import About

if TYPE_CHECKING:
    from app.setting_interface import Setting


class SettingsLayoutManager:
    """Manages the layout and navigation for settings interface."""
    
    def __init__(self, parent_widget: "Setting"):
        self.parent = parent_widget
        
    def create_navigation(self) -> Pivot:
        """Create the pivot navigation."""
        return Pivot(self.parent)
        
    def create_stacked_widget(self) -> QStackedWidget:
        """Create the stacked widget for content."""
        return QStackedWidget(self.parent)
    
    def setup_layout(self, pivot: Pivot, stacked_widget: QStackedWidget):
        """Setup the main layout with pivot and stacked widget."""
        self.parent.vBoxLayout.addWidget(pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.parent.vBoxLayout.addWidget(stacked_widget)
        self.parent.vBoxLayout.setSpacing(15)
        self.parent.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        
    def add_sub_interface(self, pivot: Pivot, stacked_widget: QStackedWidget, 
                         widget: QWidget, object_name: str, text: str, icon=None):
        """Add a sub-interface to the stacked widget and pivot."""
        widget.setObjectName(object_name)
        stacked_widget.addWidget(widget)
        pivot.addItem(
            icon=icon,
            routeKey=object_name,
            text=text,
            onClick=lambda: stacked_widget.setCurrentWidget(widget)
        )
    
    def setup_interfaces(self, pivot: Pivot, stacked_widget: QStackedWidget,
                        personal_interface: SettingCardGroup,
                        function_interface: SettingCardGroup,
                        proxy_interface: SettingCardGroup):
        """Setup all setting interfaces."""
        # Add interfaces to navigation
        self.add_sub_interface(
            pivot, stacked_widget, personal_interface, 'PersonalInterface', 
            self.parent.tr('程序'), icon=FluentIcon.SETTING
        )
        self.add_sub_interface(
            pivot, stacked_widget, function_interface, 'FunctionInterface', 
            self.parent.tr('功能'), icon=FluentIcon.TILES
        )
        self.add_sub_interface(
            pivot, stacked_widget, proxy_interface, 'ProxyInterface', 
            self.parent.tr('代理'), icon=FluentIcon.CERTIFICATE
        )
        
        # Create and add about interface
        about_interface = About('AboutInterface', self.parent)
        self.add_sub_interface(
            pivot, stacked_widget, about_interface, 'AboutInterface', 
            self.parent.tr('关于'), icon=FluentIcon.INFO
        )
        
        # Setup navigation callbacks
        stacked_widget.currentChanged.connect(
            lambda index: self.on_current_index_changed(pivot, stacked_widget, index)
        )
        
        # Set default interface
        stacked_widget.setCurrentWidget(personal_interface)
        pivot.setCurrentItem(personal_interface.objectName())
        qrouter.setDefaultRouteKey(stacked_widget, personal_interface.objectName())
    
    def on_current_index_changed(self, pivot: Pivot, stacked_widget: QStackedWidget, index: int):
        """Handle navigation index changes."""
        widget = stacked_widget.widget(index)
        pivot.setCurrentItem(widget.objectName())
        qrouter.push(stacked_widget, widget.objectName())
