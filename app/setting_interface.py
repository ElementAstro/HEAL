import sys
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    Pivot, qrouter, ScrollArea
)
from app.model.style_sheet import StyleSheet
from app.model.config import cfg
from app.components.setting import (
    SettingsManager, SettingsLayoutManager
)


class Setting(ScrollArea):
    """Main settings interface with navigation and different setting categories."""
    Nav = Pivot

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.parent_widget = parent  # 重命名避免与QWidget.parent()冲突
        self.setObjectName(text)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        # Initialize components
        self.settings_manager = SettingsManager(self)
        self.layout_manager = SettingsLayoutManager(self)

        # 栏定义
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        self.__initWidget()

    def __initWidget(self):
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # 水平滚动条关闭
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)  # 必须设置！！！

        # 使用qss设置样式
        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()
        self.__initInfo()
        self.__connectSignalToSlot()

    def __initLayout(self):
        # Create setting interfaces using manager
        self.PersonalInterface = self.settings_manager.create_personal_interface()
        self.FunctionInterface = self.settings_manager.create_function_interface()
        self.ProxyInterface = self.settings_manager.create_proxy_interface()

        # Setup layout using layout manager
        self.layout_manager.setup_layout(self.pivot, self.stackedWidget)
        self.layout_manager.setup_interfaces(
            self.pivot, self.stackedWidget,
            self.PersonalInterface, self.FunctionInterface, self.ProxyInterface
        )

    def __initInfo(self):
        self.settings_manager.init_proxy_info()

    def __connectSignalToSlot(self):
        self.settings_manager.connect_signals()

    def addSubInterface(self, widget: QWidget, objectName: str, text: str, icon=None):
        """Legacy method for compatibility."""
        self.layout_manager.add_sub_interface(
            self.pivot, self.stackedWidget, widget, objectName, text, icon
        )

    def onCurrentIndexChanged(self, index):
        """Legacy method for compatibility."""
        self.layout_manager.on_current_index_changed(self.pivot, self.stackedWidget, index)

