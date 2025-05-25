import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard
from qfluentwidgets import (
    FluentIcon as FIF, Pivot, qrouter, PrimaryPushSettingCard, LineEdit, PushButton,
    ComboBox, ScrollArea, HyperlinkCard, InfoBar, InfoBarPosition
)
from app.model.setting_card import SettingCardGroup
from app.model.config import cfg
from app.model.style_sheet import StyleSheet
from app.model.message_download import (
    MessageDownload, MessageNINA, MessagePHD2, MessageSharpCap,
    MessageLunarCore, MessageLunarCoreRes, MessageLauncher,
    MessagePython, MessageGit, MessageJava, MessageMongoDB,
    MessageFiddler, MessageMitmdump
)
from src.icon.astro import AstroIcon


logger.add("download_interface.log", rotation="1 MB")


class Download(ScrollArea):
    Nav = Pivot

    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(parent=parent)
        logger.debug(f'加载下载界面: {text}')

        self.parent_widget = parent  # 重命名避免与QWidget.parent()冲突
        self.setObjectName(text.replace(' ', '-'))
        self.scroll_widget = QWidget()
        self.vbox_layout = QVBoxLayout(self.scroll_widget)

        self.init_search_bar()
        self.init_combo_box()
        self.init_navigation()
        self.load_interface_from_json()
        self.init_widgets()

    def init_search_bar(self):
        # 搜索控件
        self.search_box = LineEdit(self.scroll_widget)
        self.search_box.setPlaceholderText("输入搜索内容...")
        self.search_box.textChanged.connect(self.search_items)

        # 按钮控件
        self.search_button = PushButton("搜索", self.scroll_widget)
        self.search_button.clicked.connect(self.search_items)
        self.refresh_button = PushButton("刷新", self.scroll_widget)
        self.refresh_button.clicked.connect(self.load_interface_from_json)
        self.toggle_search_button = PushButton("显示/隐藏搜索框", self.scroll_widget)
        self.toggle_search_button.clicked.connect(self.toggle_search_box)

    def init_combo_box(self):
        # 组合框
        self.combo_box = ComboBox(self.scroll_widget)
        self.combo_box.currentIndexChanged.connect(self.navigate_to_section)

    def init_navigation(self):
        # 导航与堆叠窗口
        self.pivot = self.Nav(self)
        self.stacked_widget = QStackedWidget(self)
        self.search_box.setVisible(False)

    def load_interface_from_json(self):
        config_path = Path('./config/interface/download.json')
        try:
            with config_path.open('r', encoding="utf-8") as f:
                self.interface = json.load(f)
                logger.debug(f'加载 JSON 文件: {config_path.name}: {
                             self.interface}')
                self.populate_combo_box()
                self.load_interface_cards()
        except FileNotFoundError:
            logger.error(f'配置文件未找到: {config_path}')
            QMessageBox.critical(self, "错误", f"配置文件未找到: {config_path}")
        except json.JSONDecodeError as e:
            logger.error(f'JSON 解码错误: {e}')
            QMessageBox.critical(self, "错误", f"JSON 解码错误: {e}")

    def populate_combo_box(self):
        self.combo_box.clear()
        self.combo_box.addItem("请选择一个部分")
        for section in self.interface.get('sections', []):
            section_title = section.get('title', '无标题')
            self.combo_box.addItem(section_title)

    def toggle_search_box(self):
        current_visibility = self.search_box.isVisible()
        self.search_box.setVisible(not current_visibility)
        logger.debug(f'Search box visibility toggled to {
                     not current_visibility}')

    def search_items(self):
        search_text = self.search_box.text().lower()
        matched_index = -1
        for index in range(1, self.combo_box.count()):
            item_text = self.combo_box.itemText(index).lower()
            if search_text in item_text:
                matched_index = index
                break

        if matched_index >= 0:
            self.combo_box.setCurrentIndex(matched_index)
            section_title = self.interface['sections'][matched_index - 1].get(
                'title', '')
            self.copy_to_clipboard(section_title)
            logger.info(f'找到匹配项: {section_title}')
        else:
            QMessageBox.warning(self, "未找到", "未找到匹配的项目")
            logger.info('未找到匹配的搜索项')

    def navigate_to_section(self):
        section_index = self.combo_box.currentIndex() - 1
        if section_index < 0:
            return

        section = self.interface['sections'][section_index]
        section_title = section.get('title', '')
        pivot_item_name = section_title.replace(' ', '-')
        self.pivot.setCurrentItem(pivot_item_name)
        self.stacked_widget.setCurrentIndex(section_index)
        logger.debug(f'导航到部分: {section_title}')

    def add_items_to_section(self, section_interface: SettingCardGroup, items: List[Dict[str, Any]]):
        for item in items:
            item_type = item.get('type')
            if not item_type:
                logger.warning('项目类型缺失')
                continue

            required_fields = {
                'hyperlink': ['url', 'text', 'icon', 'title', 'content'],
                'primary_push_setting': ['text', 'icon', 'title', 'content']
            }.get(item_type)

            if not required_fields or not all(field in item for field in required_fields):
                logger.error(f'{item_type.capitalize()} 缺少必需字段')
                continue

            item['icon'] = self.resolve_icon(item['icon'])
            try:
                card = self.create_card(item_type, item, required_fields)
                section_interface.addSettingCard(card)
                logger.debug(f'添加卡片: {item.get("title", "无标题")}')
            except ValueError as e:
                logger.error(f'创建卡片失败: {e}')

    def resolve_icon(self, icon_name: str) -> Any:
        if icon_name.startswith('FIF.'):
            return getattr(FIF, icon_name[4:], FIF.DOWNLOAD)
        elif icon_name.startswith('Astro.'):
            # 使用默认图标而不是不存在的属性
            return getattr(AstroIcon, icon_name[6:], FIF.DOWNLOAD)
        logger.error(f'未知图标: {icon_name}')
        return FIF.DOWNLOAD

    def create_card(self, item_type: str, item: Dict[str, Any], required_fields: List[str]) -> QWidget:
        card_args = {field: item[field] for field in required_fields}
        if item_type == 'hyperlink':
            return HyperlinkCard(**card_args)
        elif item_type == 'primary_push_setting':
            return PrimaryPushSettingCard(**card_args)
        raise ValueError(f'未知的项目类型: {item_type}')

    def load_interface_cards(self):
        self.stacked_widget = QStackedWidget(self.scroll_widget)
        for section in self.interface.get('sections', []):
            section_widget = SettingCardGroup(self.scroll_widget)
            self.add_items_to_section(section_widget, section.get('items', []))
            self.add_sub_interface(
                section_widget,
                section.get('id', 'section'),
                section.get('title', '无标题'),
                self.resolve_icon(section.get('icon', 'FIF.DOWNLOAD'))
            )

    def init_widgets(self):
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)

        # 应用样式表
        self.scroll_widget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        # 布局
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.search_box)
        top_layout.addWidget(self.search_button)
        top_layout.addWidget(self.refresh_button)
        top_layout.addWidget(self.toggle_search_button)

        self.vbox_layout.addLayout(top_layout)
        self.vbox_layout.addWidget(self.combo_box)
        self.vbox_layout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.vbox_layout.addWidget(self.stacked_widget)
        self.vbox_layout.setSpacing(28)
        self.vbox_layout.setContentsMargins(0, 10, 10, 0)
        self.stacked_widget.currentChanged.connect(
            self.on_current_index_changed)
        if self.stacked_widget.count() > 0:
            initial_widget = self.stacked_widget.widget(0)
            self.pivot.setCurrentItem(initial_widget.objectName())
            qrouter.setDefaultRouteKey(
                self.stacked_widget, initial_widget.objectName())
            logger.debug(f'初始界面设置为: {initial_widget.objectName()}')

    def add_sub_interface(self, widget: QWidget, object_name: str, text: str, icon: Any = FIF.DOWNLOAD):
        widget.setObjectName(object_name)
        self.stacked_widget.addWidget(widget)
        self.pivot.addItem(
            icon=icon,
            routeKey=object_name,
            text=text,
            onClick=lambda: self.stacked_widget.setCurrentWidget(widget)
        )
        logger.debug(f"子界面添加: {object_name}")

    def on_current_index_changed(self, index: int):
        widget = self.stacked_widget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stacked_widget, widget.objectName())
        logger.debug(f'当前索引已更改为 {index} - {widget.objectName()}')

    def generate_download_url(
        self, types: str, repo_url: str, mirror_url: Optional[str], mirror_branch: Optional[str] = None, is_add: bool = False
    ) -> str:
        file = Path("temp") / Path(repo_url).name
        url_cfg = f'curl -o {file} -L '

        if types == 'url':
            if cfg.chinaStatus.value and mirror_url:
                return f"{url_cfg}{mirror_url}"
            elif cfg.proxyStatus.value:
                url_cfg = f'curl -x http://127.0.0.1:7890 -o {file} -L '
            return f"{url_cfg}{repo_url}"

        git_cfg = 'git clone --progress '
        if not is_add:
            if cfg.chinaStatus.value and mirror_url:
                branch = f' --branch {mirror_branch}' if mirror_branch else ''
                return f"{git_cfg}{branch} {mirror_url}"
            elif cfg.proxyStatus.value:
                git_cfg = 'git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone --progress '
            return f"{git_cfg}{repo_url}"

        if cfg.chinaStatus.value:
            return ''
        elif cfg.proxyStatus.value:
            git_cfg = 'git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone --progress '
        return f' && {git_cfg}{repo_url}'

    def download_check(self, name: str):
        # 使用默认的下载配置，避免访问不存在的配置属性
        default_url = "https://example.com/default"
        default_mirror = "https://mirror.example.com/default"

        download_mapping: Dict[str, Tuple[Any, str, str, Optional[str], Optional[str]]] = {
            'launcher': (MessageLauncher, 'url', getattr(cfg, 'DOWNLOAD_COMMANDS_LAUNCHER', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_LAUNCHER_MIRROR', default_mirror), None),
            'python': (MessagePython, 'url', getattr(cfg, 'DOWNLOAD_COMMANDS_PYTHON', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_PYTHON_MIRROR', default_mirror), None),
            'git': (MessageGit, 'url', getattr(cfg, 'DOWNLOAD_COMMANDS_GIT', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_GIT_MIRROR', default_mirror), None),
            'java': (MessageJava, 'url', getattr(cfg, 'DOWNLOAD_COMMANDS_JAVA', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_JAVA_MIRROR', default_mirror), None),
            'mongodb': (MessageMongoDB, 'url', getattr(cfg, 'DOWNLOAD_COMMANDS_MONGODB', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_MONGODB_MIRROR', default_mirror), None),
            'nina': (MessageNINA, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_NINA', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_NINA_MIRROR', default_mirror), '--branch nina'),
            'phd2': (MessagePHD2, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_PHD2', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_PHD2_MIRROR', default_mirror), '--branch phd2'),
            'sharpcap': (MessageSharpCap, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_SHARPCAP', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_SHARPCAP_MIRROR', default_mirror), '--branch sharpcap'),
            'lunarcore': (MessageLunarCore, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_LUNARCORE', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_LUNARCORE_MIRROR', default_mirror), '--branch lunarcore'),
            'lunarcoreres': (MessageLunarCoreRes, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_LUNARCORE_RES', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_LUNARCORE_RES_MIRROR', default_mirror), '--branch lunarcoreres'),
            'fiddler': (MessageFiddler, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_FIDDLER', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_FIDDLER_MIRROR', default_mirror), '--branch fiddler'),
            'mitmdump': (MessageMitmdump, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_MITMDUMP', default_url), getattr(cfg, 'DOWNLOAD_COMMANDS_MITMDUMP_MIRROR', default_mirror), '--branch mitmdump')
        }

        mapping = download_mapping.get(name)
        if not mapping:
            logger.error(f'未知的下载类型: {name}')
            return

        message_class, types, repo_url, mirror_url, mirror_branch = mapping
        w = message_class(self)
        file_path = Path("temp") / Path(repo_url).name
        command = self.generate_download_url(
            types, repo_url, mirror_url, mirror_branch, is_add=False)

        if w.exec():
            if not file_path.exists():
                x = MessageDownload(self)
                x.show()
                x.start_download(types, command, str(file_path), '')
                if x.exec():
                    InfoBar.success(
                        title='下载成功！',
                        content="",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=1000,
                        parent=self
                    )
                    logger.info(f'下载成功: {file_path}')
                else:
                    InfoBar.error(
                        title='下载失败！',
                        content="",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                    logger.error(f'下载失败: {name}')
            else:
                InfoBar.error(
                    title='该目录已存在文件，无法下载！',
                    content="",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                subprocess.Popen(['start', str(file_path)], shell=True)
                logger.warning(f'文件已存在，打开文件: {file_path}')

    def copy_to_clipboard(self, text: str):
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(text)
        InfoBar.success(
            title='已复制',
            content=text,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self
        )
        logger.info(f'复制到剪贴板: {text}')
