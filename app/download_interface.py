import json
import os
import subprocess
from loguru import logger
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget
from PySide6.QtCore import Qt
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (Pivot, qrouter, ScrollArea, SettingCardGroup,
                            PrimaryPushSettingCard, HyperlinkCard, InfoBar, InfoBarPosition)
from app.model.config import cfg
from app.model.style_sheet import StyleSheet
from app.model.setting_card import SettingCardGroup
from app.model.message_download import (MessageDownload, MessageNINA, MessagePHD2, MessageSharpCap, 
                                        MessageLunarCore, MessageLunarCoreRes, MessageLauncher, 
                                        MessagePython, MessageGit, MessageJava, MessageMongoDB, 
                                        MessageFiddler, MessageMitmdump)
from src.icon.astro import AstroIcon


class Download(ScrollArea):
    Nav = Pivot

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)

        logger.debug(f'Loading Download Interface: {text}')

        self.parent = parent
        self.setObjectName(text.replace(' ', '-'))
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        # Load download interface configuration
        with open('./config/interface/download.json', 'r', encoding="utf-8") as f:
            try:
                self.interface = json.load(f)
                logger.debug(f'Loading JSON file: {f.name}: {self.interface}')
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f'Error loading JSON file: {e}')
                raise

        # Initialize sections from configuration
        for section in self.interface.get('sections', []):
            section_title = section.get('title')
            if not section_title:
                logger.warning('Section title missing')
                continue

            icon_value = section.get('icon', "FIF.HOME")
            section_icon = getattr(FIF, icon_value[4:], FIF.HOME)

            section_interface = SettingCardGroup(self.scrollWidget)
            self.add_items_to_section(section_interface, section.get('items', []))

            self.addSubInterface(section_interface, section_title, section_title, icon=section_icon)

        # Initialize additional interface components
        self.initialize_components()

        self.__initWidget()

    def add_items_to_section(self, section_interface, items):
        for item in items:
            item_type = item.get('type')
            if not item_type:
                logger.warning('Item type missing')
                continue

            required_fields = {
                'hyperlink': ['url', 'text', 'icon', 'title', 'content'],
                'primary_push_setting': ['text', 'icon', 'title', 'content']
            }.get(item_type)

            if not required_fields or not all(field in item for field in required_fields):
                logger.error(f'Missing required fields for {item_type.capitalize()}')
                continue

            item['icon'] = self.resolve_icon(item['icon'])
            card = self.create_card(item_type, item, required_fields)
            section_interface.addSettingCard(card)

    def resolve_icon(self, icon_name):
        if icon_name.startswith('FIF.'):
            return getattr(FIF, icon_name[4:], FIF.DOWNLOAD)
        elif icon_name.startswith('Astro.'):
            return getattr(AstroIcon, icon_name[5:], AstroIcon.DOWNLOAD)
        logger.error(f'Unknown icon: {icon_name}')
        return FIF.DOWNLOAD

    def create_card(self, item_type, item, required_fields):
        card_args = {field: item[field] for field in required_fields}
        if item_type == 'hyperlink':
            return HyperlinkCard(**card_args)
        elif item_type == 'primary_push_setting':
            return PrimaryPushSettingCard(**card_args)

    def initialize_components(self):
        self.LauncherInterface = SettingCardGroup(self.scrollWidget)
        self.LauncherRepoCard = HyperlinkCard(
            'https://github.com/ElementAstro/HEAL',
            'Hello-ElementAstro-Launcher',
            FIF.LINK,
            '项目仓库',
            '打开HEAL项目仓库'
        )
        self.LauncherResourceCard = PrimaryPushSettingCard(
            '启动器资源',
            FIF.MENU,
            '资源下载',
            '下载启动器相关资源'
        )
        self.EnvironmentInterface = SettingCardGroup(self.scrollWidget)
        self.PythonDownloadCard = PrimaryPushSettingCard(
            '详细信息',
            FIF.DOWNLOAD,
            '项目下载',
            '下载Python安装包'
        )
        self.CompilerDownloadCard = PrimaryPushSettingCard(
            '详细信息',
            FIF.DOWNLOAD,
            '项目下载',
            '下载编译环境'
        )
        self.DriverInterface = SettingCardGroup(self.scrollWidget)
        self.ASCOMRepoCard = HyperlinkCard(
            'https://www.ascom-standards.org/Downloads/Index.htm',
            '官网',
            AstroIcon.ASCOM,
            'ASCOM',
            'ASCOM is a consortium of astronomy software developers, vendors, and users.'
        )
        self.INDIRepoCard = HyperlinkCard(
            'https://www.indilib.org/get-indi.html',
            '官网',
            AstroIcon.INDI,
            'INDI',
            'INDI Library is an open source software to control astronomical equipment. It is based on the Instrument Neutral Distributed Interface (INDI) protocol and acts as a bridge between software clients and hardware devices.'
        )
        self.INDIGORepoCard = HyperlinkCard(
            'https://indigo-astronomy.org/',
            '官网',
            AstroIcon.INDIGO,
            'INDIGO',
            'INDIGO is a universal control software for professional and hobbyist astronomy. It is designed to be used with a wide range of devices, including cameras, telescopes, mounts, and other control devices.'
        )
        self.ThirdpartyInterface = SettingCardGroup(self.scrollWidget)
        self.NINARepoCard = HyperlinkCard(
            'https://nighttime-imaging.eu/download/',
            '官网',
            AstroIcon.NINA,
            'NINA',
            'NIGHTTIME IMAGING "N" ASTRONOMY - An astrophotography imaging suite'
        )
        self.PHD2RepoCard = HyperlinkCard(
            'https://openphdguiding.org/downloads/',
            '官网',
            AstroIcon.PHD,
            'PHD2',
            'PHD2 is telescope guiding software that simplifies the process of tracking a guide star, letting you concentrate on other aspects of deep-sky imaging or spectroscopy.'
        )
        self.SharpCapRepoCard = HyperlinkCard(
            'https://github.com/ElementAstro/SharpCap',
            '官网',
            AstroIcon.SharpCap,
            'SharpCap',
            'SharpCap is an easy-to-use and powerful astronomy camera capture tool. It supports a wide range of dedicated astronomy cameras as well as webcams and USB frame grabbers.'
        )
        self.APTRepoCard = HyperlinkCard(
            'https://astrophotography.app/downloads.php',
            '官网',
            AstroIcon.APT,
            'APT',
            'Can control DSLR & CMOS camera,includes image acquisition tools,Now ToupTek Astro Camera is fully compatible with this software'
        )
        self.MaximDLRepoCard = HyperlinkCard(
            'https://www.cyanogen.com/product/maxim-dl/',
            '官网',
            AstroIcon.MaximDL,
            'MaximDL',
            'MaxIm DL is the complete integrated solution for all of your astronomical imaging needs.'
        )
        self.THESkyRepoCard = HyperlinkCard(
            'https://www.bisque.com/product-category/software',
            '官网',
            AstroIcon.TheSky,
            'THESky',
            'An essential tool for astronomical discovery and observation.'
        )
        self.VoyagerRepoCard = HyperlinkCard(
            'https://software.starkeeper.it/',
            '官网',
            AstroIcon.Voyager,
            'Voyager',
            'A systems integration software,interfacing third-part software products.'
        )
        self.SGPRepoCard = HyperlinkCard(
            'https://www.sequencegeneratorpro.com/sgpro',
            '官网',
            AstroIcon.SGP,
            'SGP',
            'The best in class automation software for astrophotography.'
        )
        self.FireCaptureRepoCard = HyperlinkCard(
            'https://www.firecapture.de/',
            '官网',
            AstroIcon.FireCpature,
            'FireCapture',
            'Can control Telescope,EFW,has Autoguiding and Autorun features,Now ToupTek Astro Camera is fully compatible with this software'
        )
        self.DownloadFiddlerCard = PrimaryPushSettingCard(
            '详细信息',
            FIF.DOWNLOAD,
            'Fiddler',
            '下载代理工具Fiddler'
        )
        self.DownloadMitmdumpCard = PrimaryPushSettingCard(
            '详细信息',
            FIF.DOWNLOAD,
            'Mitmdump',
            '下载代理工具Mitmdump'
        )
        self.ResourceInterface = SettingCardGroup(self.scrollWidget)
        self.ResourceRepoCard = HyperlinkCard(
            'https://github.com/ElementAstro/LunarCore',
            'LunarCore',
            FIF.LINK,
            '项目仓库',
            '打开LunarCore仓库'
        )

    def __initWidget(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # Apply stylesheet
        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        # Bind items to sections
        self.LauncherInterface.addSettingCard(self.LauncherRepoCard)
        self.LauncherInterface.addSettingCard(self.LauncherResourceCard)
        self.EnvironmentInterface.addSettingCard(self.PythonDownloadCard)
        self.EnvironmentInterface.addSettingCard(self.CompilerDownloadCard)
        self.DriverInterface.addSettingCard(self.ASCOMRepoCard)
        self.DriverInterface.addSettingCard(self.INDIRepoCard)
        self.DriverInterface.addSettingCard(self.INDIGORepoCard)
        self.ThirdpartyInterface.addSettingCard(self.NINARepoCard)
        self.ThirdpartyInterface.addSettingCard(self.PHD2RepoCard)
        self.ThirdpartyInterface.addSettingCard(self.SharpCapRepoCard)
        self.ThirdpartyInterface.addSettingCard(self.APTRepoCard)
        self.ThirdpartyInterface.addSettingCard(self.THESkyRepoCard)
        self.ThirdpartyInterface.addSettingCard(self.MaximDLRepoCard)
        self.ThirdpartyInterface.addSettingCard(self.VoyagerRepoCard)
        self.ThirdpartyInterface.addSettingCard(self.SGPRepoCard)
        self.ThirdpartyInterface.addSettingCard(self.FireCaptureRepoCard)
        self.ResourceInterface.addSettingCard(self.ResourceRepoCard)

        # Bind sections to pivot
        self.addSubInterface(self.LauncherInterface, 'LauncherInterface', '启动器', icon=FIF.HOME)
        self.addSubInterface(self.EnvironmentInterface, 'EnvironmentInterface', '环境', icon=FIF.IOT)
        self.addSubInterface(self.DriverInterface, 'DriverInterface', '设备驱动', icon=FIF.IOT)
        self.addSubInterface(self.ThirdpartyInterface, 'ThirdpartyInterface', '第三方软件', icon=FIF.APPLICATION)
        self.addSubInterface(self.ResourceInterface, 'ResourceInterface', '资源', icon=FIF.TILES)

        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(28)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.LauncherInterface)
        self.pivot.setCurrentItem(self.LauncherInterface.objectName())
        qrouter.setDefaultRouteKey(self.stackedWidget, self.LauncherInterface.objectName())

    def __connectSignalToSlot(self):
        self.LauncherResourceCard.clicked.connect(lambda: self.download_check('launcherres'))
        self.PythonDownloadCard.clicked.connect(lambda: self.download_check('python'))
        self.CompilerDownloadCard.clicked.connect(lambda: self.download_check('compiler'))
        self.DownloadFiddlerCard.clicked.connect(lambda: self.download_check('fiddler'))
        self.DownloadMitmdumpCard.clicked.connect(lambda: self.download_check('mitmdump'))

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

    def generate_download_url(self, types, repo_url, mirror_url, mirror_branch=None, is_add=False):
        file = os.path.join("temp", repo_url.split('/')[-1])
        url_cfg = f'curl -o {file} -L '

        if types == 'url':
            if cfg.chinaStatus.value:
                return url_cfg + mirror_url
            elif cfg.proxyStatus.value:
                url_cfg = f'curl -x http://127.0.0.1:7890 -o {file} -L '
            return url_cfg + repo_url

        git_cfg = 'git clone --progress '
        if not is_add:
            if cfg.chinaStatus.value:
                return git_cfg + mirror_branch + mirror_url
            elif cfg.proxyStatus.value:
                git_cfg = 'git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone --progress '
            return git_cfg + repo_url

        if cfg.chinaStatus.value:
            return ''
        elif cfg.proxyStatus.value:
            git_cfg = 'git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone --progress '
        return ' && ' + git_cfg + repo_url

    def download_check(self, name):
        build_jar = ''
        download_mapping = {
            'launcher': (MessageLauncher, 'url', cfg.DOWNLOAD_COMMANDS_LAUNCHER, cfg.DOWNLOAD_COMMANDS_LAUNCHER_MIRROR),
            'python': (MessagePython, 'url', cfg.DOWNLOAD_COMMANDS_PYTHON, cfg.DOWNLOAD_COMMANDS_PYTHON_MIRROR),
            'git': (MessageGit, 'url', cfg.DOWNLOAD_COMMANDS_GIT, cfg.DOWNLOAD_COMMANDS_GIT_MIRROR),
            'java': (MessageJava, 'url', cfg.DOWNLOAD_COMMANDS_JAVA, cfg.DOWNLOAD_COMMANDS_JAVA_MIRROR),
            'mongodb': (MessageMongoDB, 'url', cfg.DOWNLOAD_COMMANDS_MONGODB, cfg.DOWNLOAD_COMMANDS_MONGODB_MIRROR),
            'nina': (MessageNINA, 'git', cfg.DOWNLOAD_COMMANDS_NINA, cfg.DOWNLOAD_COMMANDS_NINA_MIRROR, '--branch nina '),
            'phd2': (MessagePHD2, 'git', cfg.DOWNLOAD_COMMANDS_PHD2, cfg.DOWNLOAD_COMMANDS_PHD2_MIRROR, '--branch phd2 '),
            'sharpcap': (MessageSharpCap, 'git', cfg.DOWNLOAD_COMMANDS_SHARPCAP, cfg.DOWNLOAD_COMMANDS_SHARPCAP_MIRROR, '--branch sharpcap '),
            'lunarcore': (MessageLunarCore, 'git', cfg.DOWNLOAD_COMMANDS_LUNARCORE, cfg.DOWNLOAD_COMMANDS_LUNARCORE_MIRROR, '--branch lunarcore ', 'lunarcore'),
            'lunarcoreres': (MessageLunarCoreRes, 'git', cfg.DOWNLOAD_COMMANDS_LUNARCORE_RES_1, cfg.DOWNLOAD_COMMANDS_LUNARCORE_RES_MIRROR, '--branch lunarcoreres ', 'lunarcore'),
            'fiddler': (MessageFiddler, 'git', cfg.DOWNLOAD_COMMANDS_FIDDLER, cfg.DOWNLOAD_COMMANDS_FIDDLER_MIRROR, '--branch fiddler '),
            'mitmdump': (MessageMitmdump, 'git', cfg.DOWNLOAD_COMMANDS_MITMDUMP, cfg.DOWNLOAD_COMMANDS_MITMDUMP_MIRROR, '--branch mitmdump ')
        }

        message_class, types, repo_url, mirror_url, mirror_branch, build_jar = download_mapping.get(name, (None, None, None, None, None, None))

        if not message_class:
            logger.error(f'Unknown download type: {name}')
            return

        w = message_class(self)
        file_path = os.path.join("temp", repo_url.split('/')[-1])
        command = self.generate_download_url(types, repo_url, mirror_url, mirror_branch, is_add=False)

        if w.exec():
            if not os.path.exists(file_path):
                x = MessageDownload(self)
                x.show()
                x.start_download(types, command, file_path, build_jar)
                if x.exec():
                    InfoBar.success(
                        title='下载成功！',
                        content="",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=1000,
                        parent=self
                    )
                else:
                    InfoBar.error(
                        title='下载失败！',
                        content="",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
            else:
                InfoBar.error(
                    title=f'该目录已存在文件,无法下载！',
                    content="",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                subprocess.Popen('start ' + file_path, shell=True)
