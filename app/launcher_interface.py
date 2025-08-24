from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import Pivot, qrouter, ScrollArea, PrimaryPushSettingCard, FluentIcon
from app.model.style_sheet import StyleSheet
from app.model.setting_card import SettingCardGroup

# Import launcher components
from app.components.launcher import (
    HyperlinkCardLauncher, LauncherNavigationManager, LauncherSignalManager
)

class Launcher(ScrollArea):
    Nav = Pivot

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self._parent_widget = parent
        self.setObjectName(text)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        # 栏定义
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        # 添加项
        self.LauncherDownloadInterface = SettingCardGroup(self.scrollWidget)
        self.LauncherRepoCard = HyperlinkCardLauncher(
            self.tr('项目仓库'),
            self.tr('打开Firefly-Launcher相关项目仓库')
        )
        self.AudioDownloadCard = PrimaryPushSettingCard(
            self.tr('下载'),
            FluentIcon.DOWNLOAD,
            'Firefly-Launcher-Audio',
            self.tr('下载流萤音频文件')
        )
        self.ConfigInterface = SettingCardGroup(self.scrollWidget)
        self.settingConfigCard = PrimaryPushSettingCard(
            self.tr('打开文件'),
            FluentIcon.LABEL,
            self.tr('启动器设置'),
            self.tr('自定义启动器配置')
        )

        # 初始化管理器
        self.navigation_manager = LauncherNavigationManager(self)
        self.signal_manager = LauncherSignalManager(self)

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
        self.__connectSignalToSlot()

    def __initLayout(self):
        # 项绑定到栏目
        self.LauncherDownloadInterface.addSettingCard(self.LauncherRepoCard)
        self.LauncherDownloadInterface.addSettingCard(self.AudioDownloadCard)
        self.ConfigInterface.addSettingCard(self.settingConfigCard)

        # 设置导航管理器
        self.navigation_manager.setup_navigation(self.pivot, self.stackedWidget)

        # 栏绑定界面
        self.navigation_manager.add_sub_interface(
            self.LauncherDownloadInterface, 'LauncherDownloadInterface',
            self.tr('下载'), icon=FluentIcon.DOWNLOAD
        )
        self.navigation_manager.add_sub_interface(
            self.ConfigInterface, 'configInterface',
            self.tr('配置'), icon=FluentIcon.EDIT
        )

        # 初始化配置界面
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        
        # 设置默认界面
        self.navigation_manager.set_default_interface(self.LauncherDownloadInterface)

    def __connectSignalToSlot(self):
        # 使用信号管理器连接信号
        self.signal_manager.connect_audio_download_signal(self.AudioDownloadCard)
        self.signal_manager.connect_config_signal(self.settingConfigCard)


