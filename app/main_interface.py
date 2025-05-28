import sys
import json
import random
import subprocess
from pathlib import Path

import winreg
from PySide6.QtCore import Signal, Qt, QSize, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import QApplication

from qfluentwidgets import (
    MSFluentWindow, NavigationItemPosition, setTheme, Theme, InfoBar,
    PrimaryPushButton, InfoBarPosition, SplashScreen, HyperlinkButton,
    InfoBarIcon, FluentIcon
)

from app.home_interface import Home
from app.launcher_interface import Launcher
from app.download_interface import Download
from app.environment_interface import Environment
from app.proxy_interface import Proxy
from app.setting_interface import Setting
from app.module_interface import Module
from app.tool_interface import Tools

from app.model.config import cfg, Info
from app.model.login_card import MessageLogin


class Main(MSFluentWindow):
    reload_signal = Signal()
    shutdown_signal = Signal()

    def __init__(self) -> None:
        super().__init__()
        setTheme(cfg.themeMode.value)

        # Initialize tray_icon as None initially
        self.tray_icon = None

        self.initMainWindow()
        self.initNavigation()
        self.handleFontCheck()

        self.splashScreen.finish()

        # check_update()
        if cfg.useLogin.value:
            self.count_pwd = 1
            self.login_card = MessageLogin()  # 移除错误的参数
            self.login_card.show()
            self.login_card.passwordEntered.connect(self.handleLogin)
        else:
            if cfg.useAudio.value:
                self.handleMediaPlay('success')

    def initNavigation(self) -> None:
        self.homeInterface = Home('HomeInterface', self)
        self.launcherInterface = Launcher('LauncherInterface', self)
        self.downloadInterface = Download('DownloadInterface', self)
        self.environmentInterface = Environment('EnvironmentInterface', self)
        self.proxyInterface = Proxy('ProxyInterface', self)
        self.settingInterface = Setting('SettingInterface', self)
        self.moduleInterface = Module('ModuleInterface', self)
        self.toolsInterface = Tools('ToolsInterface', self)

        interfaces = [
            (self.homeInterface, FluentIcon.HOME,
             self.tr('主页'), FluentIcon.HOME_FILL),
            (self.launcherInterface, FluentIcon.PLAY,
             self.tr('启动器'), FluentIcon.PLAY),
            (self.downloadInterface, FluentIcon.DOWNLOAD,
             self.tr('下载'), FluentIcon.DOWNLOAD),
            (self.environmentInterface, FluentIcon.DICTIONARY,
             self.tr('环境'), FluentIcon.DICTIONARY),
            (self.moduleInterface, FluentIcon.APPLICATION,
             self.tr('模块'), FluentIcon.APPLICATION),
            (self.proxyInterface, FluentIcon.CERTIFICATE,
             self.tr('代理'), FluentIcon.CERTIFICATE),
            (self.toolsInterface, FluentIcon.DEVELOPER_TOOLS,
             self.tr('工具'), FluentIcon.DEVELOPER_TOOLS),
            (self.settingInterface, FluentIcon.SETTING, self.tr('设置'),
             FluentIcon.SETTING, NavigationItemPosition.BOTTOM)
        ]

        for interface in interfaces:
            widget, icon, text, fill_icon, *position = interface
            pos = position[0] if position else NavigationItemPosition.TOP
            self.addSubInterface(widget, icon, text, fill_icon, pos)

        self.navigationInterface.addItem(
            routeKey='theme',
            icon=FluentIcon.CONSTRACT,
            text=self.tr('主题'),
            onClick=self.handleThemeChanged,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )

        self.navigationInterface.addItem(
            routeKey='reload',
            icon=FluentIcon.SYNC,
            text=self.tr('热重载'),
            onClick=self.handleReload,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )

        self.navigationInterface.addItem(
            routeKey='shutdown',
            icon=FluentIcon.POWER_BUTTON,
            text=self.tr('关机'),
            onClick=self.handleShutdown,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )

    def initMainWindow(self) -> None:
        self.titleBar.maxBtn.setHidden(True)
        self.titleBar.maxBtn.setDisabled(True)
        self.titleBar.setDoubleClickEnabled(False)
        self.setResizeEnabled(False)
        self.setWindowFlags(self.windowFlags() & ~
                            Qt.WindowType.WindowMaximizeButtonHint)

        self.setWindowTitle(cfg.APP_NAME)
        self.setFixedSize(1280, 768)
        self.setWindowIcon(QIcon('./src/image/icon.ico'))

        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(200, 200))
        self.splashScreen.raise_()

        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.show()
        QApplication.processEvents()

    def handleFontCheck(self) -> None:
        is_setup_font = False
        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
            (winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows NT\CurrentVersion\Fonts")
        ]
        try:
            for hkey, sub_key in registry_keys:
                with winreg.ConnectRegistry(None, hkey) as reg:
                    with winreg.OpenKey(reg, sub_key) as reg_key:
                        i = 0
                        while True:
                            try:
                                name, _, _ = winreg.EnumValue(reg_key, i)
                                if cfg.APP_FONT.lower() in name.lower():
                                    is_setup_font = True
                                i += 1
                            except OSError:
                                break
        except Exception as e:
            Info(self, 'E', 3000, self.tr('检查字体失败: ') + str(e))

        if not is_setup_font:
            subprocess.run('cd src/patch/font && start zh-cn.ttf', shell=True)
            sys.exit()

    def handleLogin(self, pwd: str) -> None:
        config_path = Path('config/config.json')
        with config_path.open('r', encoding='utf-8') as file:
            config = json.load(file)
        local_pwd = config.get('PASSWORD', '')
        if local_pwd == pwd:
            Info(self, 'S', 1000, self.tr('登录成功!'))
            if cfg.useAudio.value:
                self.handleMediaPlay('success')
            self.login_card.close()
        else:
            Info(self, 'E', 3000,
                 f"{self.tr('密码错误!')} {self.tr('次数: ')}{self.count_pwd}")
            self.count_pwd += 1
            if cfg.useAudio.value:
                self.handleMediaPlay('error')

    def handleThemeChanged(self) -> None:
        theme = Theme.LIGHT if cfg.themeMode.value == Theme.DARK else Theme.DARK
        setTheme(theme)
        cfg.themeMode.value = theme
        cfg.save()

    def handleReload(self) -> None:
        self.reload_signal.emit()

    def handleShutdown(self) -> None:
        self.shutdown_signal.emit()

    def handleUpdate(self, status: int, info: str) -> None:
        if status == 2:
            update_info = InfoBar(
                icon=InfoBarIcon.WARNING,
                title=f"{self.tr('检测到新版本: ')}{info}",
                content='',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=-1,
                parent=self
            )
            update_button = HyperlinkButton(cfg.URL_LATEST, self.tr('前往下载'))
            update_info.addWidget(update_button)
            update_info.show()
        elif status == 1:
            Info(self, 'S', 1000, f"{self.tr('当前是最新版本: ')}{info}")
        elif status == 0:
            Info(self, 'E', 3000, f"{self.tr('检测更新失败: ')}{info}")

    def handleMediaPlay(self, status: str) -> None:
        audio_path = Path('src/audio') / status
        if audio_path.exists():
            audio_files = list(audio_path.glob('*.wav'))
            if audio_files:
                self.player = QMediaPlayer()
                self.audioOutput = QAudioOutput()
                self.player.setAudioOutput(self.audioOutput)
                self.audioOutput.setVolume(1)
                audio_play = QUrl.fromLocalFile(
                    str(random.choice(audio_files)))
                self.player.setSource(audio_play)
                self.player.play()
            else:
                self.showAudioError()
        else:
            self.showAudioError()

    def showAudioError(self) -> None:
        file_error = InfoBar(
            icon=InfoBarIcon.ERROR,
            title=self.tr('未找到语音!'),
            content='',
            orient=Qt.Orientation.Horizontal,
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

    def toggle_window(self) -> None:
        if self.isVisible():
            self.hide()
            if self.tray_icon and hasattr(self.tray_icon, 'toggle_action'):
                self.tray_icon.toggle_action.setText("显示窗口")
        else:
            self.show()
            if self.tray_icon and hasattr(self.tray_icon, 'toggle_action'):
                self.tray_icon.toggle_action.setText("隐藏窗口")
