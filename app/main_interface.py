import os
import sys
import json
import glob
import random
import winreg
import hashlib
import subprocess
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from qfluentwidgets import (
    MSFluentWindow, NavigationItemPosition, setTheme, Theme, InfoBar,
    PrimaryPushButton, InfoBarPosition, SplashScreen, HyperlinkButton,
    InfoBarIcon, FluentIcon
)
from app.home_interface import Home
from app.launcher_interface import Launcher
from app.environment_interface import Environment
from app.proxy_interface import Proxy
from app.setting_interface import Setting
from app.model.config import cfg, Info
from app.model.check_update import checkUpdate
from app.model.login_card import MessageLogin


class Main(MSFluentWindow):
    def __init__(self):
        super().__init__()
        setTheme(cfg.themeMode.value)

        self.initMainWindow()
        self.initNavigation()
        self.handleFontCheck()

        self.splashScreen.finish()

        checkUpdate(self)
        if cfg.useLogin.value:
            self.count_pwd = 1
            self.login_card = MessageLogin(self)
            self.login_card.show()
            self.login_card.passwordEntered.connect(self.handleLogin)
        else:
            if cfg.useAudio.value:
                self.handleMediaPlay('success')

    def initNavigation(self):
        self.homeInterface = Home('HomeInterface', self)
        self.launcherInterface = Launcher('LauncherInterface', self)
        self.environmentInterface = Environment('EnvironmentInterface', self)
        self.proxyInterface = Proxy('ProxyInterface', self)
        self.settingInterface = Setting('SettingInterface', self)

        interfaces = [
            (self.homeInterface, FluentIcon.HOME, self.tr('主页'), FluentIcon.HOME_FILL),
            (self.launcherInterface, FluentIcon.PLAY, self.tr('启动器'), FluentIcon.PLAY),
            (self.environmentInterface, FluentIcon.DICTIONARY, self.tr('环境'), FluentIcon.DICTIONARY),
            (self.proxyInterface, FluentIcon.CERTIFICATE, self.tr('代理'), FluentIcon.CERTIFICATE),
            (self.settingInterface, FluentIcon.SETTING, self.tr('设置'), FluentIcon.SETTING, NavigationItemPosition.BOTTOM)
        ]

        for interface, icon, text, fillIcon, *position in interfaces:
            position = position[0] if position else NavigationItemPosition.TOP
            self.addSubInterface(interface, icon, text, fillIcon, position)

        self.navigationInterface.addItem(
            routeKey='theme',
            icon=FluentIcon.CONSTRACT,
            text=self.tr('主题'),
            onClick=self.handleThemeChanged,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )

    def initMainWindow(self):
        self.titleBar.maxBtn.setHidden(True)
        self.titleBar.maxBtn.setDisabled(True)
        self.titleBar.setDoubleClickEnabled(False)
        self.setResizeEnabled(False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

        self.setWindowTitle(cfg.APP_NAME)
        self.setFixedSize(1280, 768)
        self.setWindowIcon(QIcon('./src/image/icon.ico'))

        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(200, 200))
        self.splashScreen.raise_()

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.show()
        QApplication.processEvents()

    def handleFontCheck(self):
        isSetupFont = False
        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Fonts")
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
                                    isSetupFont = True
                                i += 1
                            except OSError:
                                break
        except Exception as e:
            Info(self, 'E', 3000, self.tr('检查字体失败: '), str(e))

        if not isSetupFont:
            subprocess.run('cd src/patch/font && start zh-cn.ttf', shell=True)
            sys.exit()

    def handleLogin(self, pwd):
        with open('config/config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        local_pwd = config['PASSWORD']
        if local_pwd == pwd:
            Info(self, 'S', 1000, self.tr('登录成功!'))
            if cfg.useAudio.value:
                self.handleMediaPlay('success')
            self.login_card.close()
        else:
            Info(self, 'E', 3000, self.tr('密码错误!'), self.tr('次数: ') + str(self.count_pwd))
            self.count_pwd += 1
            if cfg.useAudio.value:
                self.handleMediaPlay('error')

    def handleThemeChanged(self):
        theme = Theme.LIGHT if cfg.themeMode.value == Theme.DARK else Theme.DARK
        setTheme(theme)
        cfg.themeMode.value = theme
        cfg.save()

    def handleUpdate(self, status, info):
        if status == 2:
            update_info = InfoBar(
                icon=InfoBarIcon.WARNING,
                title=self.tr('检测到新版本: ') + info,
                content='',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=-1,
                parent=self
            )
            update_button = HyperlinkButton(cfg.URL_LATEST, self.tr('前往下载'))
            update_info.addWidget(update_button)
            update_info.show()
        elif status == 1:
            Info(self, 'S', 1000, self.tr('当前是最新版本: ') + info)
        elif status == 0:
            Info(self, 'E', 3000, self.tr('检测更新失败: ') + info)

    def handleMediaPlay(self, status):
        if os.path.exists('src/audio'):
            self.player = QMediaPlayer()
            self.audioOutput = QAudioOutput()
            self.player.setAudioOutput(self.audioOutput)
            self.audioOutput.setVolume(1)
            audio_list = glob.glob(f'src\\audio\\{status}\\*.wav')
            audio_play = QUrl.fromLocalFile(random.choice(audio_list))
            self.player.setSource(audio_play)
            self.player.play()
        else:
            file_error = InfoBar(
                icon=InfoBarIcon.ERROR,
                title=self.tr('未找到语音!'),
                content='',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            file_error_button = PrimaryPushButton(self.tr('前往下载'))
            file_error_button.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
            file_error.addWidget(file_error_button)
            file_error.show()