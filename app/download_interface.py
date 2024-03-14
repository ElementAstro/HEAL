import os
import subprocess
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget
from PySide6.QtCore import Qt
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (Pivot, qrouter, ScrollArea, SettingCardGroup,
                            PrimaryPushSettingCard, HyperlinkCard, InfoBar, InfoBarPosition)
from src.module.config import cfg
from src.component.style_sheet import StyleSheet
from src.component.common import (MessageDownload,MessageNINA, MessagePHD2, MessageSharpCap, MessageLunarCore, MessageLunarCoreRes, HyperlinkCard_LunarCore, HyperlinkCard_Tool,
                                       HyperlinkCard_Environment, MessageLauncher, MessagePython, MessageGit, MessageJava, MessageMongoDB,
                                       MessageFiddler, MessageMitmdump)


class Download(ScrollArea):
    Nav = Pivot
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.setObjectName(text.replace(' ', '-'))
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        # 栏定义
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        # 添加项 , 名字会隐藏
        # 启动器组件，通常用于修复启动器问题
        self.LauncherInterface = SettingCardGroup('启动器', self.scrollWidget)
        self.LauncherRepoCard = HyperlinkCard(
            'https://github.com/ElementAstro/Lithium',
            'Hello-ElementAstro-Launcher',
            FIF.LINK,
            '项目仓库',
            '打开HEAL项目仓库'
        )
        self.LauncherDownloadCard = PrimaryPushSettingCard(
            '详细信息',
            FIF.DOWNLOAD,
            '项目下载',
            '下载Hello-ElementAstro-Launcher启动器'
        )
        self.LauncherResourceCard = PrimaryPushSettingCard(
            '启动器资源',
            FIF.MENU,
            '资源下载',
            '下载启动器相关资源'
        )
        self.EnvironmentInterface = SettingCardGroup('环境', self.scrollWidget)
        self.EnvironmentRepoCard = HyperlinkCard_Environment(
            'https://www.python.org/',
            'Python',
            'https://git-scm.com/download/win',
            'Git',
            'https://www.oracle.com/java/technologies/javase-downloads.html',
            'Java',
            'https://www.mongodb.com/try/download/community',
            'MongoDB',
            FIF.LINK,
            '项目仓库',
            '打开各环境仓库'
        )
        self.PythonDownloadCard = PrimaryPushSettingCard(
            '详细信息',
            FIF.DOWNLOAD,
            '项目下载',
            '下载Python安装包'
        )
        self.GitDownloadCard = PrimaryPushSettingCard(
            '详细信息',
            FIF.DOWNLOAD,
            '项目下载',
            '下载Git安装包'
        )
        self.CompilerDownloadCard = PrimaryPushSettingCard(
            '详细信息',
            FIF.DOWNLOAD,
            '项目下载',
            '下载编译环境'
        )
        self.JavaDownloadCard = PrimaryPushSettingCard(
            '详细信息',
            FIF.DOWNLOAD,
            '项目下载',
            '下载Java安装包'
        )
        #self.MongoDBDownloadCard = PrimaryPushSettingCard(
        #    '详细信息',
        #    FIF.DOWNLOAD,
        #    '项目下载',
        #    '下载MongoDB安装包'
        #)
        self.ThirdpartyInterface = SettingCardGroup('第三方软件', self.scrollWidget)

        self.NINARepoCard = HyperlinkCard(
            'https://nighttime-imaging.eu/download/',
            '官网',
            FIF.DOWNLOAD,
            'NINA',
            'NIGHTTIME IMAGING "N" ASTRONOMY - An astrophotography imaging suite'
        )
        self.PHD2RepoCard = HyperlinkCard(
            'https://openphdguiding.org/downloads/',
            '官网',
            FIF.DOWNLOAD,
            'PHD2',
            'PHD2 is telescope guiding software that simplifies the process of tracking a guide star, letting you concentrate on other aspects of deep-sky imaging or spectroscopy.'
        )

        self.SharpCapRepoCard = HyperlinkCard(
            'https://github.com/ElementAstro/SharpCap',
            '官网',
            FIF.DOWNLOAD,
            'SharpCap',
            'SharpCap is an easy-to-use and powerful astronomy camera capture tool. It supports a wide range of dedicated astronomy cameras as well as webcams and USB frame grabbers.'
        )

        
        self.ToolInterface = SettingCardGroup('工具', self.scrollWidget)
        self.ToolRepoCard = HyperlinkCard_Tool(
            'https://www.telerik.com/fiddler#fiddler-classic',
            'Fiddler',
            'https://mitmproxy.org/',
            'Mitmdump',
            FIF.LINK,
            '项目仓库',
            '打开代理工具仓库'
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

        self.__initWidget()

    def __initWidget(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)     # 水平滚动条关闭
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)    # 必须设置！！！
        
        # 使用qss设置样式
        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        # 项绑定到栏目
        self.LauncherInterface.addSettingCard(self.LauncherRepoCard)
        self.LauncherInterface.addSettingCard(self.LauncherDownloadCard)
        self.LauncherInterface.addSettingCard(self.LauncherResourceCard)
        # 环境
        self.EnvironmentInterface.addSettingCard(self.EnvironmentRepoCard)
        self.EnvironmentInterface.addSettingCard(self.PythonDownloadCard)
        self.EnvironmentInterface.addSettingCard(self.GitDownloadCard)
        self.EnvironmentInterface.addSettingCard(self.CompilerDownloadCard)
        self.EnvironmentInterface.addSettingCard(self.JavaDownloadCard)
        #self.EnvironmentInterface.addSettingCard(self.MongoDBDownloadCard)
        # 第三方软件下载
        self.ThirdpartyInterface.addSettingCard(self.NINARepoCard)
        self.ThirdpartyInterface.addSettingCard(self.PHD2RepoCard)
        self.ThirdpartyInterface.addSettingCard(self.SharpCapRepoCard)
        # 其他
        #self.LunarCoreInterface.addSettingCard(self.LunarCoreRepoCard)
        #self.LunarCoreInterface.addSettingCard(self.LunarCoreDownloadCard)
        #self.LunarCoreInterface.addSettingCard(self.LunarCoreResDownloadCard)
        self.ToolInterface.addSettingCard(self.ToolRepoCard)
        self.ToolInterface.addSettingCard(self.DownloadFiddlerCard)
        self.ToolInterface.addSettingCard(self.DownloadMitmdumpCard)

        # 目前无法做到导航栏各个页面独立分组 , 故隐藏组标题
        self.LauncherInterface.titleLabel.setHidden(True)
        self.EnvironmentInterface.titleLabel.setHidden(True)
        self.ThirdpartyInterface.titleLabel.setHidden(True)
        self.ToolInterface.titleLabel.setHidden(True)

        # 栏绑定界面
        self.addSubInterface(self.LauncherInterface, 'LauncherInterface','启动器', icon=FIF.HOME)
        self.addSubInterface(self.EnvironmentInterface, 'EnvironmentInterface','环境', icon=FIF.IOT)
        self.addSubInterface(self.ThirdpartyInterface, 'ThirdpartyInterface','第三方软件', icon=FIF.APPLICATION)
        self.addSubInterface(self.ToolInterface, 'ToolInterface','工具', icon=FIF.TAG)

        # 初始化配置界面
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(28)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.LauncherInterface)
        self.pivot.setCurrentItem(self.LauncherInterface.objectName())
        qrouter.setDefaultRouteKey(self.stackedWidget, self.LauncherInterface.objectName())
        
    def __connectSignalToSlot(self):
        self.LauncherDownloadCard.clicked.connect(lambda: self.download_check('launcher'))
        self.LauncherResourceCard.clicked.connect(lambda: self.download_check('launcherres'))
        self.PythonDownloadCard.clicked.connect(lambda: self.download_check('python'))
        self.GitDownloadCard.clicked.connect(lambda: self.download_check('git'))
        self.CompilerDownloadCard.clicked.connect(lambda: self.download_check('compiler'))
        self.JavaDownloadCard.clicked.connect(lambda: self.download_check('java'))
        #self.MongoDBDownloadCard.clicked.connect(lambda: self.download_check('mongodb'))
        #self.NINADownloadCard.clicked.connect(lambda: self.download_check('nina'))
        #self.PHD2DownloadCard.clicked.connect(lambda: self.download_check('phd2'))
        #self.SharpCapDownloadCard.clicked.connect(lambda: self.download_check('sharpcap'))
        #self.LunarCoreDownloadCard.clicked.connect(lambda: self.download_check('lunarcore'))
        #self.LunarCoreResDownloadCard.clicked.connect(lambda: self.download_check('lunarcoreres'))
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
        if types == 'url':
            file = os.path.join("temp", repo_url.split('/')[-1])
            url_cfg = f'curl -o {file} -L '
            if cfg.chinaStatus.value:
                return url_cfg + mirror_url
            elif cfg.proxyStatus.value:
                url_cfg = f'curl -x http://127.0.0.1:7890 -o {file} -L '
            return url_cfg + repo_url
        elif types == 'git':
            git_cfg = 'git clone --progress '
            if not is_add:
                if cfg.chinaStatus.value:
                    return git_cfg + mirror_branch + mirror_url
                elif cfg.proxyStatus.value:
                    git_cfg = 'git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone --progress '
                return git_cfg + repo_url
            else:
                if cfg.chinaStatus.value:
                    return ''
                elif cfg.proxyStatus.value:
                    git_cfg = 'git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone --progress '
                return ' && ' + git_cfg + repo_url

    def download_check(self, name):
        build_jar = ''
        if name == 'launcher':
            w = MessageLauncher(self)
            types = 'url'
            file_path = os.path.join("temp", cfg.DOWNLOAD_COMMANDS_LAUNCHER.split('/')[-1])
            command = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_LAUNCHER, cfg.DOWNLOAD_COMMANDS_LAUNCHER_MIRROR)
        elif name == 'python':
            w = MessagePython(self)
            types = 'url'
            file_path = os.path.join("temp", cfg.DOWNLOAD_COMMANDS_PYTHON.split('/')[-1])
            command = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_PYTHON, cfg.DOWNLOAD_COMMANDS_PYTHON_MIRROR)
        elif name == 'git':
            w = MessageGit(self)
            types = 'url'
            file_path = os.path.join("temp", cfg.DOWNLOAD_COMMANDS_GIT.split('/')[-1])
            command = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_GIT, cfg.DOWNLOAD_COMMANDS_GIT_MIRROR)
        elif name == 'java':
            w = MessageJava(self)
            types = 'url'
            file_path = os.path.join("temp", cfg.DOWNLOAD_COMMANDS_JAVA.split('/')[-1])
            command = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_JAVA, cfg.DOWNLOAD_COMMANDS_JAVA_MIRROR)
        elif name =='mongodb':
            w = MessageMongoDB(self)
            types = 'url'
            file_path = os.path.join("temp", cfg.DOWNLOAD_COMMANDS_MONGODB.split('/')[-1])
            command = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_MONGODB, cfg.DOWNLOAD_COMMANDS_MONGODB_MIRROR)
        elif name == 'nina':
            w = MessageNINA(self)
            types = 'git'
            file_path = 'server\\NINA'
            command = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_NINA, cfg.DOWNLOAD_COMMANDS_NINA_MIRROR, '--branch nina ')
        elif name == 'phd2':
            w = MessagePHD2(self)
            types = 'git'
            file_path = 'server\\PHD2'
            command = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_PHD2, cfg.DOWNLOAD_COMMANDS_PHD2_MIRROR, '--branch phd2 ')
        elif name == 'sharpcap':
            w = MessageSharpCap(self)
            types = 'git'
            file_path = 'server\\SharpCap'
            command = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_SHARPCAP, cfg.DOWNLOAD_COMMANDS_SHARPCAP_MIRROR, '--branch sharpcap ')
        elif name == 'lunarcore':
            w = MessageLunarCore(self)
            types = 'git'
            file_path = 'server\\LunarCore'
            command = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_LUNARCORE, cfg.DOWNLOAD_COMMANDS_LUNARCORE_MIRROR, '--branch lunarcore ')
            build_jar = 'lunarcore'
        elif name == 'lunarcoreres':
            w = MessageLunarCoreRes(self)
            types = 'git'
            file_path = 'server\\LunarCore\\resources'
            command_1 = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_LUNARCORE_RES_1, cfg.DOWNLOAD_COMMANDS_LUNARCORE_RES_MIRROR, '--branch lunarcoreres ')
            command_2 = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_LUNARCORE_RES_2, '', '', True)
            command = command_1 + command_2
        elif name == 'fiddler':
            w = MessageFiddler(self)
            types = 'git'
            file_path = 'tool\\Fiddler'
            command = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_FIDDLER, cfg.DOWNLOAD_COMMANDS_FIDDLER_MIRROR, '--branch fiddler ')
        elif name == 'mitmdump':
            w = MessageMitmdump(self)
            types = 'git'
            file_path = 'tool\\Mitmdump'
            command = self.generate_download_url(types, cfg.DOWNLOAD_COMMANDS_MITMDUMP, cfg.DOWNLOAD_COMMANDS_MITMDUMP_MIRROR, '--branch mitmdump ')
        print(command)

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