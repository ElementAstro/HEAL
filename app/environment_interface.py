import json
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QStackedWidget, QVBoxLayout
)
from PySide6.QtCore import Qt

from qfluentwidgets import (
    Pivot, qrouter, ScrollArea, PrimaryPushSettingCard, FluentIcon,
    InfoBar, InfoBarIcon, InfoBarPosition, PrimaryPushButton
)

from app.model.style_sheet import StyleSheet
from app.model.setting_card import SettingCard, SettingCardGroup
from app.model.config import Info
from app.model.download_process import SubDownloadCMD
from app.setting_interface import Setting
from app.common.logging_config import get_logger, log_performance, with_correlation_id

# Import environment components
from app.components.environment.environment_cards import (
    HyperlinkCardEnvironment, PrimaryPushSettingCardDownload
)
from app.components.environment.config_manager import EnvironmentConfigManager
from app.components.environment.signal_manager import EnvironmentSignalManager

# 使用统一日志配置
logger = get_logger('environment_interface')


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

        # 初始化管理器
        self.config_manager = EnvironmentConfigManager(self)
        self.signal_manager = EnvironmentSignalManager(self, self.environmentDownloadInterface)

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
        
        # 连接管理器信号
        self.signal_manager.download_to_page_requested.connect(
            self.stackedWidget.setCurrentIndex
        )
        
        logger.info("信号已连接到槽。")

    def load_download_config(self) -> None:
        """加载下载配置并添加卡片"""
        cards = self.config_manager.load_download_config()
        for card in cards:
            self.environmentDownloadInterface.addSettingCard(card)
        
        # 连接新添加的卡片信号
        self.signal_manager.connect_card_signals(self.environmentDownloadInterface)

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
        """处理MongoDB打开"""
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
                lambda: self.signal_manager.download_to_page_requested.emit(1))
            file_error.addWidget(file_error_button)
            file_error.show()
            logger.warning("MongoDB 文件不存在。")