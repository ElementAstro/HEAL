import json
import os
import subprocess
from loguru import logger
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QMessageBox)
from PySide6.QtCore import Qt
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (Pivot, qrouter, PrimaryPushSettingCard, LineEdit, PushButton, ComboBox, ScrollArea,
                            HyperlinkCard, InfoBar, InfoBarPosition)
from app.model.setting_card import SettingCardGroup, SettingIconWidget, CustomDialog, CustomFrame, CustomFrameGroup
from app.model.config import cfg
from app.model.style_sheet import StyleSheet
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
        self.searchBox = LineEdit(self.scrollWidget)
        self.searchButton = PushButton("搜索", self.scrollWidget)
        self.refreshButton = PushButton("刷新", self.scrollWidget)
        self.toggleSearchButton = PushButton("显示/隐藏搜索框", self.scrollWidget)
        self.comboBox = ComboBox(self.scrollWidget)

        self.searchBox.setPlaceholderText("输入搜索内容...")
        self.searchBox.textChanged.connect(self.search_items)
        self.searchButton.clicked.connect(self.search_items)
        self.refreshButton.clicked.connect(self.load_interface_from_json)
        self.toggleSearchButton.clicked.connect(self.toggle_search_box)
        self.comboBox.currentIndexChanged.connect(self.navigate_to_section)

        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        self.searchBox.setVisible(False)

        # Load download interface configuration
        self.interface = None
        self.load_interface_from_json()

        # Initialize additional interface components
        self.__initWidget()

    def load_interface_from_json(self):
        with open('./config/interface/download.json', 'r', encoding="utf-8") as f:
            try:
                self.interface = json.load(f)
                logger.debug(f'Loading JSON file: {f.name}: {self.interface}')
                self.populate_combo_box()
                self.load_interface_cards()
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f'Error loading JSON file: {e}')
                raise

    def populate_combo_box(self):
        self.comboBox.clear()
        self.comboBox.addItem("请选择一个部分")
        for section in self.interface.get('sections', []):
            section_title = section.get('title', '无标题')
            self.comboBox.addItem(section_title)

    def toggle_search_box(self):
        self.searchBox.setVisible(self.searchBox.isVisible())

    def search_items(self):
        search_text = self.searchBox.text().lower()
        matched_index = -1
        for index in range(1, self.comboBox.count()):
            item_text = self.comboBox.itemText(index).lower()
            if search_text in item_text:
                matched_index = index
                break
        
        if matched_index >= 0:
            self.comboBox.setCurrentIndex(matched_index)
        else:
            QMessageBox.warning(self, "未找到", "未找到匹配的项目")

    def navigate_to_section(self):
        section_index = self.comboBox.currentIndex() - 1
        if section_index < 0:
            return

        section = self.interface['sections'][section_index]
        section_title = section.get('title')
        self.pivot.setCurrentItem(section_title.replace(' ', '-'))
        self.stackedWidget.setCurrentIndex(section_index)

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
            print(icon_name)
            return getattr(AstroIcon, icon_name[6:], AstroIcon.PHD)
        logger.error(f'Unknown icon: {icon_name}')
        return FIF.DOWNLOAD

    def create_card(self, item_type, item, required_fields):
        card_args = {field: item[field] for field in required_fields}
        if item_type == 'hyperlink':
            return HyperlinkCard(**card_args)
        elif item_type == 'primary_push_setting':
            return PrimaryPushSettingCard(**card_args)

    def load_interface_cards(self):
        self.stackedWidget = QStackedWidget(self.scrollWidget)
        for section in self.interface.get('sections', []):
            section_widget = SettingCardGroup(self.scrollWidget)
            self.add_items_to_section(section_widget, section.get('items', []))
            self.addSubInterface(section_widget, section['id'], section['title'], self.resolve_icon(section['icon']))

    def __initWidget(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # Apply stylesheet
        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        topLayout = QHBoxLayout()
        topLayout.addWidget(self.searchBox)
        topLayout.addWidget(self.searchButton)
        topLayout.addWidget(self.refreshButton)
        topLayout.addWidget(self.toggleSearchButton)

        self.vBoxLayout.addLayout(topLayout)
        self.vBoxLayout.addWidget(self.comboBox)
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(28)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.pivot.setCurrentItem(self.stackedWidget.widget(0).objectName())
        qrouter.setDefaultRouteKey(self.stackedWidget, self.stackedWidget.widget(0).objectName())

    def addSubInterface(self, widget: QWidget, objectName, text, icon=None):
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
            'lunarcoreres': (MessageLunarCoreRes, 'git', cfg.DOWNLOAD_COMMANDS_LUNARCORE_RES, cfg.DOWNLOAD_COMMANDS_LUNARCORE_RES_MIRROR, '--branch lunarcoreres ', 'lunarcore'),
            'fiddler': (MessageFiddler, 'git', cfg.DOWNLOAD_COMMANDS_FIDDLER, cfg.DOWNLOAD_COMMANDS_FIDDLER_MIRROR, '--branch fiddler '),
            'mitmdump': (MessageMitmdump, 'git', cfg.DOWNLOAD_COMMANDS_MITMDUMP, cfg.DOWNLOAD_COMMANDS_MITMDUMP_MIRROR, '--branch mitmdump ')
        }

        message_class, types, repo_url, mirror_url, mirror_branch, build_jar = download_mapping.get(
            name, (None, None, None, None, None, None))

        if not message_class:
            logger.error(f'Unknown download type: {name}')
            return

        w = message_class(self)
        file_path = os.path.join("temp", repo_url.split('/')[-1])
        command = self.generate_download_url(
            types, repo_url, mirror_url, mirror_branch, is_add=False)

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
