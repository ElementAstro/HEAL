from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget
from PySide6.QtCore import Qt
from qfluentwidgets import (Pivot, qrouter, ScrollArea, FluentIcon)
from app.model.style_sheet import StyleSheet
from app.model.setting_card import CustomFrameGroup

from app.components.module.mod_manager import ModManager
from app.components.tools.scaffold import ScaffoldApp

class Module(ScrollArea):
    Nav = Pivot

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.setObjectName(text)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        # 栏定义
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        # 添加项
        self.ModuleManagerFrame = ModManager()
        self.ModuleManagerInterface = CustomFrameGroup(self.scrollWidget)
        self.ModuleManagerInterface.addCustomFrame(self.ModuleManagerFrame)

        self.ScaffoldAppFrame = ScaffoldApp()
        self.ScaffoldAppInterface = CustomFrameGroup(self.scrollWidget)
        self.ScaffoldAppInterface.addCustomFrame(self.ScaffoldAppFrame)

        self.__initWidget()

    def __initWidget(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 水平滚动条关闭
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)  # 必须设置！！！

        # 使用qss设置样式
        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        # 项绑定到栏目
        # self.ModuleDownloadInterface.addSettingCard(self.ModuleRepoCard)
        # self.ModuleDownloadInterface.addSettingCard(self.DownloadFiddlerCard)
        # self.ModuleManagerInterface.addSettingCard(self.FiddlerCard)
        # self.ModuleManagerInterface.addSettingCard(self.noproxyCard)

        # 栏绑定界面
        self.addSubInterface(self.ModuleManagerInterface, 'ModuleManagerInterface', self.tr(
            '模组管理'), icon=FluentIcon.IOT)
        self.addSubInterface(self.ScaffoldAppInterface, 'ScaffoldAppInterface', self.tr(
            '模组生成器'), icon=FluentIcon.IOT)

        # 初始化配置界面
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.ModuleManagerInterface)
        self.pivot.setCurrentItem(self.ModuleManagerInterface.objectName())
        qrouter.setDefaultRouteKey(
            self.stackedWidget, self.ModuleManagerInterface.objectName())

    def __connectSignalToSlot(self):
        """"""

    def addSubInterface(self, widget: QLabel, objectName: str, text: str, icon=None):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            icon=icon,
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index: int):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())
