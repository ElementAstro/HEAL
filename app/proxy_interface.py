from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt
from qfluentwidgets import (
    Pivot, qrouter, ScrollArea, PrimaryPushSettingCard, FluentIcon, HyperlinkCard
)

from app.model.style_sheet import StyleSheet
from app.model.setting_card import SettingCardGroup
from app.common.logging_config import get_logger

# Import proxy components
from app.components.proxy import (
    PrimaryPushSettingCardFiddler, ProxyNavigationManager, ProxySignalManager
)

# 使用统一日志配置
logger = get_logger('proxy_interface')


class Proxy(ScrollArea):
    Nav = Pivot

    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(parent=parent)
        self._parent_widget = parent  # 使用不同的名称避免冲突
        self.setObjectName(text)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        # 创建界面组件
        self.ProxyDownloadInterface = SettingCardGroup(self.scrollWidget)
        self.ProxyRepoCard = HyperlinkCard(
            'https://www.telerik.com/fiddler#fiddler-classic',
            'Fiddler',
            FluentIcon.LINK,
            self.tr('项目仓库'),
            self.tr('打开代理工具仓库')
        )
        self.DownloadFiddlerCard = PrimaryPushSettingCard(
            self.tr('下载'),
            FluentIcon.DOWNLOAD,
            'Fiddler',
            self.tr('下载代理工具Fiddler')
        )
        self.ProxyToolInterface = SettingCardGroup(self.scrollWidget)
        self.FiddlerCard = PrimaryPushSettingCardFiddler(
            'Fiddler',
            self.tr('使用Fiddler Scripts代理')
        )
        self.noproxyCard = PrimaryPushSettingCard(
            self.tr('重置'),
            FluentIcon.POWER_BUTTON,
            self.tr('重置代理'),
            self.tr('重置部分服务端未关闭的代理')
        )

        # 初始化管理器
        self.navigation_manager = ProxyNavigationManager(self)
        self.signal_manager = ProxySignalManager(self)

        self.__initWidget()

    def __initWidget(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        # 项绑定到栏目
        self.ProxyDownloadInterface.addSettingCard(self.ProxyRepoCard)
        self.ProxyDownloadInterface.addSettingCard(self.DownloadFiddlerCard)
        self.ProxyToolInterface.addSettingCard(self.FiddlerCard)
        self.ProxyToolInterface.addSettingCard(self.noproxyCard)

        # 设置导航管理器
        self.navigation_manager.setup_navigation(self.pivot, self.stackedWidget)

        # 栏绑定界面
        self.navigation_manager.add_sub_interface(
            self.ProxyDownloadInterface, 'ProxyDownloadInterface',
            self.tr('下载'), icon=FluentIcon.DOWNLOAD
        )
        self.navigation_manager.add_sub_interface(
            self.ProxyToolInterface, 'ProxyToolInterface',
            self.tr('工具'), icon=FluentIcon.COMMAND_PROMPT
        )

        # 初始化配置界面
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        
        # 设置默认界面
        self.navigation_manager.set_default_interface(self.ProxyDownloadInterface)

    def __connectSignalToSlot(self):
        # 使用信号管理器连接信号
        self.signal_manager.connect_download_signals(self.DownloadFiddlerCard)
        self.signal_manager.connect_fiddler_signals(self.FiddlerCard)
        self.signal_manager.connect_proxy_signals(self.noproxyCard)
        
        logger.info("信号已连接到槽。")
