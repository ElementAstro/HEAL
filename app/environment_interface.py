import os
import subprocess
import json
from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QStackedWidget, QVBoxLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import QApplication

from qfluentwidgets import (
    Pivot, qrouter, ScrollArea, PrimaryPushSettingCard, InfoBar, FluentIcon,
    HyperlinkButton, InfoBarPosition, PrimaryPushButton, InfoBarIcon
)

from app.model.style_sheet import StyleSheet
from app.model.setting_card import SettingCard, SettingCardGroup
from app.model.download_process import SubDownloadCMD
from app.setting_interface import Setting
from app.model.config import Info

from loguru import logger

logger.add("environment_interface.log", rotation="1 MB")


class HyperlinkCardEnvironment(SettingCard):
    clicked = Signal()
    
    def __init__(
        self, title: str, content: Optional[str] = None,
        icon: FluentIcon = FluentIcon.LINK, links: Optional[Dict[str, str]] = None
    ):
        super().__init__(icon, title, content or "")
        self.links = links or {}
        self.init_ui()

    def init_ui(self):
        for name, url in self.links.items():
            link_button = HyperlinkButton(url, name, self)
            self.hBoxLayout.addWidget(link_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        copy_button = PrimaryPushButton("复制链接", self)
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(
            next(iter(self.links.values()), "")))
        self.hBoxLayout.addWidget(copy_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)

    def copy_to_clipboard(self, text: str) -> None:
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(text)
        Info(self, "S", 1000, self.tr("链接已复制到剪贴板!"))
        logger.info(f"Copied URL to clipboard: {text}")


class PrimaryPushSettingCardDownload(SettingCard):
    download_signal = Signal(str)
    handle_download_started = Signal(str)  # 添加缺失的信号

    def __init__(
        self, title: str, content: str, icon: FluentIcon = FluentIcon.DOWNLOAD,
        options: Optional[Any] = None
    ):
        super().__init__(icon, title, content)
        self.options = options or []
        self.init_ui()

    def init_ui(self):
        for option in self.options:
            button = PrimaryPushButton(option['name'], self)
            button.clicked.connect(
                lambda _, key=option['key']: self.download_signal.emit(key)
            )
            self.hBoxLayout.addWidget(button, 0, Qt.AlignmentFlag.AlignRight)
            self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addSpacing(16)


class Environment(ScrollArea):
    Nav = Pivot

    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(parent=parent)
        self._parent_widget = parent  # 使用不同的名称避免冲突
        self.setObjectName(text)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        self.environmentInterface = SettingCardGroup(self.scrollWidget)
        self.mongoDBCard = PrimaryPushSettingCard(
            self.tr('打开'),
            FluentIcon.FIT_PAGE,
            self.tr('启动便携版MongoDB数据库'),
            self.tr('打开MongoDB数据库'),
            self
        )
        self.environmentDownloadInterface = SettingCardGroup(self.scrollWidget)

        self.init_widget()

    def init_widget(self) -> None:
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.init_layout()
        self.connect_signals()
        self.load_download_config()

    def init_layout(self) -> None:
        self.environmentInterface.addSettingCard(self.mongoDBCard)

        self.add_sub_interface(
            self.environmentInterface, 'EnvironmentInterface',
            self.tr('环境'), icon=FluentIcon.PLAY
        )
        self.add_sub_interface(
            self.environmentDownloadInterface, 'EnvironmentDownloadInterface',
            self.tr('下载'), icon=FluentIcon.DOWNLOAD
        )

        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        self.stackedWidget.currentChanged.connect(
            self.on_current_index_changed)
        self.stackedWidget.setCurrentWidget(self.environmentInterface)
        self.pivot.setCurrentItem(self.environmentInterface.objectName())
        qrouter.setDefaultRouteKey(
            self.stackedWidget, self.environmentInterface.objectName()
        )

    def connect_signals(self) -> None:
        self.mongoDBCard.clicked.connect(self.handle_mongo_db_open)
        sub_download_cmd_self = SubDownloadCMD(self)
        for i in range(self.environmentDownloadInterface.cardLayout.count()):
            item = self.environmentDownloadInterface.cardLayout.itemAt(i)
            if item is not None:
                card = item.widget()
                if isinstance(card, PrimaryPushSettingCardDownload):
                    card.download_signal.connect(
                        sub_download_cmd_self.handle_download_started
                    )
                elif isinstance(card, HyperlinkCardEnvironment) and 'git' in card.links:
                    card.clicked.connect(self.handle_restart_info)
        logger.info("信号已连接到槽。")

    def load_download_config(self) -> None:
        config_file = Path('config') / 'download.json'
        if config_file.exists():
            with config_file.open('r', encoding='utf-8') as f:
                download_config = json.load(f)
            for item in download_config:
                card = self.create_card_from_config(item)
                self.environmentDownloadInterface.addSettingCard(card)
                logger.info(f"Loaded card from config: {item['title']}")
        else:
            logger.warning(f"下载配置文件不存在: {config_file}")

    def create_card_from_config(self, item: Dict[str, Any]) -> SettingCard:
        card_type = item.get('type')
        if card_type == 'link':
            return HyperlinkCardEnvironment(
                title=item['title'],
                content=item.get('content') or "",
                links=item.get('links')
            )
        elif card_type == 'download':
            return PrimaryPushSettingCardDownload(
                title=item['title'],
                content=item.get('content') or "",
                options=item.get('options')
            )
        else:
            logger.error(f"未知的卡片类型: {card_type}")
            raise ValueError(f"未知的卡片类型: {card_type}")

    def add_sub_interface(
        self, widget: QWidget, objectName: str, text: str,
        icon: Optional[FluentIcon] = None
    ) -> None:
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            icon=icon,
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )
        logger.debug(f"子界面 {objectName} 已添加。")

    def on_current_index_changed(self, index: int) -> None:
        widget = self.stackedWidget.widget(index)
        if widget:
            self.pivot.setCurrentItem(widget.objectName())
            qrouter.push(self.stackedWidget, widget.objectName())
            logger.debug(f"当前索引已更改为 {index} - {widget.objectName()}")

    def handle_mongo_db_open(self) -> None:
        mongo_exe = Path('tool') / 'mongodb' / 'mongod.exe'
        if mongo_exe.exists():
            try:
                subprocess.Popen(
                    ['cmd', '/c',
                     f'cd /d "{mongo_exe.parent}" && mongod --dbpath data --port 27017'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                Info(self, "S", 1000, self.tr("数据库已开始运行!"))
                logger.info("MongoDB 已启动。")
            except Exception as e:
                Info(self, 'E', 3000, self.tr("启动数据库失败！"), str(e))
                logger.error(f"启动 MongoDB 失败: {e}")
        else:
            file_error = InfoBar(
                icon=InfoBarIcon.ERROR,
                title=self.tr('找不到数据库!'),
                content='',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            file_error_button = PrimaryPushButton(
                self.tr('前往下载'), self)
            file_error_button.clicked.connect(
                lambda: self.stackedWidget.setCurrentIndex(1))
            file_error.addWidget(file_error_button)
            file_error.show()
            logger.warning("MongoDB 文件不存在。")

    def handle_restart_info(self) -> None:
        restart_info = InfoBar(
            icon=InfoBarIcon.WARNING,
            title=self.tr('重启应用以使用Git命令!'),
            content='',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=self
        )
        restart_button = PrimaryPushButton(self.tr('重启'))
        restart_button.clicked.connect(Setting.restart_application)
        restart_info.addWidget(restart_button)
        restart_info.show()
        logger.info("显示重启应用信息。")