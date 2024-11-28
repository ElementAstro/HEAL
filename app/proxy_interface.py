import os
import time
import subprocess
from typing import Optional, Dict
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    Pivot, qrouter, ScrollArea, PrimaryPushSettingCard, PopupTeachingTip, InfoBarPosition,
    PrimaryPushButton, InfoBar,
    FluentIcon, FlyoutViewBase, TeachingTipTailPosition, InfoBarIcon,
    HyperlinkCard
)
from app.model.style_sheet import StyleSheet
from app.model.setting_card import SettingCard, SettingCardGroup
from app.model.download_process import SubDownloadCMD
from app.model.config import cfg, get_json, Info


class PrimaryPushSettingCardFiddler(SettingCard):
    clicked_script = Signal()
    clicked_old = Signal()
    clicked_backup = Signal()

    def __init__(self, title: str, content: Optional[str] = None, icon=FluentIcon.VPN):
        super().__init__(icon, title, content)
        self.button_script = PrimaryPushButton(self.tr('脚本打开'), self)
        self.button_old = PrimaryPushButton(self.tr('原版打开'), self)
        self.button_backup = PrimaryPushButton(self.tr('备份'), self)
        self.hBoxLayout.addWidget(self.button_script, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.button_old, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.button_backup, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.button_script.clicked.connect(self.clicked_script)
        self.button_old.clicked.connect(self.clicked_old)
        self.button_backup.clicked.connect(self.clicked_backup)


class CustomFlyoutViewFiddler(FlyoutViewBase):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent=parent)
        self.parent = parent

        self.gc_button = PrimaryPushButton('Grasscutter')
        self.ht_button = PrimaryPushButton('Hutao-GS')
        self.lc_button = PrimaryPushButton('LunarCore')
        self.clash_button = PrimaryPushButton('Clash')  # 新增Clash按钮
        for button in [self.gc_button, self.ht_button, self.lc_button, self.clash_button]:
            button.setFixedWidth(120)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setSpacing(12)
        self.hBoxLayout.setContentsMargins(20, 16, 20, 16)
        self.hBoxLayout.addWidget(self.gc_button)
        self.hBoxLayout.addWidget(self.ht_button)
        self.hBoxLayout.addWidget(self.lc_button)
        self.hBoxLayout.addWidget(self.clash_button)  # 添加Clash按钮

        self.gc_button.clicked.connect(lambda: self.handleFiddlerButton('gc'))
        self.ht_button.clicked.connect(lambda: self.handleFiddlerButton('ht'))
        self.lc_button.clicked.connect(lambda: self.handleFiddlerButton('lc'))
        self.clash_button.clicked.connect(
            lambda: self.handleFiddlerButton('clash'))  # 处理Clash按钮点击

    def handleFiddlerButton(self, mode: str):
        status = Proxy.handleFiddlerOpen(self.parent)
        if status:
            script_map: Dict[str, str] = {
                'gc': 'CustomRules-GC.js',
                'ht': 'CustomRules-HT.js',
                'lc': 'CustomRules-LC.js',
                'clash': 'CustomRules-Clash.js'  # 添加Clash对应的脚本
            }
            script_file = script_map.get(mode)
            if script_file:
                try:
                    subprocess.run(
                        f'del /f "%userprofile%\\Documents\\Fiddler2\\Scripts\\CustomRules.js" && '
                        f'copy /y "src\\patch\\fiddler\\{
                            script_file}" "%userprofile%\\Documents\\Fiddler2\\Scripts\\CustomRules.js"',
                        shell=True, check=True
                    )
                except subprocess.CalledProcessError as e:
                    Info(self, 'E', 3000, self.tr("脚本更新失败！"), str(e))


class Proxy(ScrollArea):
    Nav = Pivot

    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(parent=parent)
        self.parent = parent
        self.setObjectName(text)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

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

        self.__initWidget()

    def __initWidget(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.ProxyDownloadInterface.addSettingCard(self.ProxyRepoCard)
        self.ProxyDownloadInterface.addSettingCard(self.DownloadFiddlerCard)
        self.ProxyToolInterface.addSettingCard(self.FiddlerCard)
        self.ProxyToolInterface.addSettingCard(self.noproxyCard)

        self.addSubInterface(self.ProxyToolInterface, 'ProxyToolInterface', self.tr(
            '启动'), icon=FluentIcon.PLAY)
        self.addSubInterface(self.ProxyDownloadInterface, 'ToolkitDownloadInterface', self.tr('下载'),
                             icon=FluentIcon.DOWNLOAD)

        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.ProxyToolInterface)
        self.pivot.setCurrentItem(self.ProxyToolInterface.objectName())
        qrouter.setDefaultRouteKey(
            self.stackedWidget, self.ProxyToolInterface.objectName())

    def __connectSignalToSlot(self):
        sub_download_cmd = SubDownloadCMD(self)
        self.DownloadFiddlerCard.clicked.connect(
            lambda: sub_download_cmd.handleDownloadStarted('fiddler'))
        self.FiddlerCard.clicked_script.connect(self.handleFiddlerTip)
        self.FiddlerCard.clicked_old.connect(self.handleFiddlerOpen)
        self.FiddlerCard.clicked_backup.connect(self.handleFiddlerBackup)
        self.noproxyCard.clicked.connect(self.handleProxyDisabled)

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

    def handleFiddlerOpen(self) -> bool:
        fiddler_path = 'tool/Fiddler/Fiddler.exe'
        if os.path.exists(fiddler_path):
            try:
                subprocess.run(['start', fiddler_path], shell=True, check=True)
                Info(self, "S", 1000, self.tr("文件已打开!"))
                return True
            except subprocess.CalledProcessError as e:
                Info(self, 'E', 3000, self.tr("打开文件失败！"), str(e))
                return False
        else:
            file_error = InfoBar(
                icon=InfoBarIcon.ERROR,
                title=self.tr('找不到文件!'),
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
            return False

    def handleFiddlerTip(self):
        PopupTeachingTip.make(
            target=self.FiddlerCard.button_script,
            view=CustomFlyoutViewFiddler(parent=self),
            tailPosition=TeachingTipTailPosition.RIGHT,
            duration=-1,
            parent=self
        )

    def handleFiddlerBackup(self):
        now_time = time.strftime('%Y%m%d%H%M%S', time.localtime())
        backup_path = f"CustomRules-{now_time}.js"
        try:
            subprocess.run(
                f'copy /y "%userprofile%\\Documents\\Fiddler2\\Scripts\\CustomRules.js" "{
                    backup_path}"',
                shell=True, check=True
            )
            Info(self, "S", 1000, self.tr("备份成功!"))
        except subprocess.CalledProcessError as e:
            Info(self, 'E', 3000, self.tr("备份失败！"), str(e))

    def handleProxyDisabled(self):
        try:
            port = get_json('./config/config.json', 'PROXY_PORT')
            if cfg.proxyStatus.value:
                subprocess.run(
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW, check=True
                )
                subprocess.run(
                    f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer /d "127.0.0.1:{
                        port}" /f',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW, check=True
                )
            else:
                subprocess.run(
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW, check=True
                )
                subprocess.run(
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer /d "" /f',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW, check=True
                )
            Info(self, 'S', 1000, self.tr("全局代理已更改！"))
        except subprocess.CalledProcessError as e:
            Info(self, 'E', 3000, self.tr("全局代理更改失败！"), str(e))
