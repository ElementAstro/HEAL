import os
import subprocess
import json
from PySide6.QtWidgets import QWidget, QLabel, QStackedWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (Pivot, qrouter, ScrollArea, PrimaryPushSettingCard, InfoBar, FluentIcon,
                            HyperlinkButton, InfoBarPosition, PrimaryPushButton, InfoBarIcon)
from app.model.style_sheet import StyleSheet
from app.model.setting_card import SettingCard, SettingCardGroup
from app.model.download_process import SubDownloadCMD
from app.setting_interface import Setting
from app.model.config import Info


class HyperlinkCard_Environment(SettingCard):
    def __init__(self, title, content=None, icon=FluentIcon.LINK, links=None):
        super().__init__(icon, title, content)
        self.links = links or {}
        for name, url in self.links.items():
            link_button = HyperlinkButton(url, name, self)
            self.hBoxLayout.addWidget(link_button, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)


class PrimaryPushSettingCard_Download(SettingCard):
    download_signal = Signal(str)

    def __init__(self, title, content, icon=FluentIcon.DOWNLOAD, options=None):
        super().__init__(icon, title, content)
        self.options = options or []
        for option in self.options:
            button = PrimaryPushButton(option['name'], self)
            button.clicked.connect(
                lambda _, key=option['key']: self.download_signal.emit(key))
            self.hBoxLayout.addWidget(button, 0, Qt.AlignRight)
            self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addSpacing(16)


class Environment(ScrollArea):
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
        self.EnvironmentInterface = SettingCardGroup(self.scrollWidget)
        self.MongoDBCard = PrimaryPushSettingCard(
            self.tr('打开'),
            FluentIcon.FIT_PAGE,
            'MongoDB',
            self.tr('打开便携版MongoDB数据库')
        )
        self.EnvironmentDownloadInterface = SettingCardGroup(self.scrollWidget)

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
        self.__loadDownloadConfig()

    def __initLayout(self):
        # 项绑定到栏目
        self.EnvironmentInterface.addSettingCard(self.MongoDBCard)

        # 栏绑定界面
        self.addSubInterface(self.EnvironmentInterface, 'EnvironmentInterface', self.tr(
            '环境'), icon=FluentIcon.PLAY)
        self.addSubInterface(self.EnvironmentDownloadInterface, 'EnvironmentDownloadInterface', self.tr('下载'),
                             icon=FluentIcon.DOWNLOAD)

        # 初始化配置界面
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.EnvironmentInterface)
        self.pivot.setCurrentItem(self.EnvironmentInterface.objectName())
        qrouter.setDefaultRouteKey(
            self.stackedWidget, self.EnvironmentInterface.objectName())

    def __connectSignalToSlot(self):
        self.MongoDBCard.clicked.connect(self.handleMongoDBOpen)
        SubDownloadCMDSelf = SubDownloadCMD(self)
        for i in range(self.EnvironmentDownloadInterface.cardLayout.count()):
            card = self.EnvironmentDownloadInterface.cardLayout.itemAt(
                i).widget()
            if isinstance(card, PrimaryPushSettingCard_Download):
                card.download_signal.connect(
                    SubDownloadCMDSelf.handleDownloadStarted)
            elif isinstance(card, HyperlinkCard_Environment) and 'git' in card.links:
                card.clicked.connect(self.handleRestartInfo)

    def __loadDownloadConfig(self):
        config_file = 'config/download.json'
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                download_config = json.load(f)
            for item in download_config:
                if item['type'] == 'link':
                    card = HyperlinkCard_Environment(
                        item['title'], item.get('content'), links=item.get('links'))
                elif item['type'] == 'download':
                    card = PrimaryPushSettingCard_Download(
                        item['title'], item.get('content'), options=item.get('options'))
                self.EnvironmentDownloadInterface.addSettingCard(card)

    def addSubInterface(self, widget: QLabel, objectName, text, icon=None):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            icon=icon,
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())

    def handleMongoDBOpen(self):
        if os.path.exists('tool/mongodb/mongod.exe'):
            subprocess.run(
                'start cmd /c "cd tool/mongodb && mongod --dbpath data --port 27017"', shell=True)
            Info(self, "S", 1000, self.tr("数据库已开始运行!"))
        else:
            file_error = InfoBar(
                icon=InfoBarIcon.ERROR,
                title=self.tr('找不到数据库!'),
                content='',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            file_error_button = PrimaryPushButton(self.tr('前往下载'))
            file_error_button.clicked.connect(
                lambda: self.stackedWidget.setCurrentIndex(1))
            file_error.addWidget(file_error_button)
            file_error.show()

    def handleRestartInfo(self):
        restart_info = InfoBar(
            icon=InfoBarIcon.WARNING,
            title=self.tr('重启应用以使用Git命令!'),
            content='',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=self
        )
        restart_button = PrimaryPushButton(self.tr('重启'))
        restart_button.clicked.connect(Setting.restart_application)
        restart_info.addWidget(restart_button)
        restart_info.show()
