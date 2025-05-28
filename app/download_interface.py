import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from app.common.logging_config import get_logger
from app.common.i18n import t
from app.common.exception_handler import exception_handler, ExceptionType, global_exception_handler
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

# 初始化logger和异常处理器
logger = get_logger('download_interface')
# Use the exception handler decorator directly


class Download(ScrollArea):
    Nav = Pivot

    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(parent=parent)
        logger.debug(t('download.loading_interface', interface=text))

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
        """初始化搜索栏"""
        # 搜索控件
        self.search_box = LineEdit(self.scroll_widget)
        self.search_box.setPlaceholderText(t('download.search_placeholder'))
        self.search_box.textChanged.connect(self.search_items)

        # 按钮控件
        self.search_button = PushButton(t('common.search'), self.scroll_widget)
        self.search_button.clicked.connect(self.search_items)
        self.refresh_button = PushButton(t('common.refresh'), self.scroll_widget)
        self.refresh_button.clicked.connect(self.load_interface_from_json)
        self.toggle_search_button = PushButton(t('download.toggle_search'), self.scroll_widget)
        self.toggle_search_button.clicked.connect(self.toggle_search_box)

    def init_combo_box(self):
        """初始化组合框"""
        self.combo_box = ComboBox(self.scroll_widget)
        self.combo_box.currentIndexChanged.connect(self.navigate_to_section)

    def init_navigation(self):
        """初始化导航"""
        self.pivot = self.Nav(self)
        self.stacked_widget = QStackedWidget(self)
        self.search_box.setVisible(False)

    @exception_handler(exc_type=ExceptionType.DOWNLOAD_ERROR)
    def load_interface_from_json(self):
        """从JSON文件加载界面配置"""
        config_path = Path('./config/interface/download.json')
        try:
            with config_path.open('r', encoding="utf-8") as f:
                self.interface = json.load(f)
                logger.debug(t('download.json_loaded', 
                              filename=config_path.name, 
                              data=str(self.interface)))
                self.populate_combo_box()
                self.load_interface_cards()
        except FileNotFoundError:
            error_msg = t('download.config_not_found', path=str(config_path))
            logger.error(error_msg)
            QMessageBox.critical(self, t('common.error'), error_msg)
        except json.JSONDecodeError as e:
            error_msg = t('download.json_decode_error', error=str(e))
            logger.error(error_msg)
            QMessageBox.critical(self, t('common.error'), error_msg)

    def populate_combo_box(self):
        """填充组合框"""
        self.combo_box.clear()
        self.combo_box.addItem(t('download.select_section'))
        for section in self.interface.get('sections', []):
            section_title = section.get('title', t('download.untitled'))
            self.combo_box.addItem(section_title)

    def toggle_search_box(self):
        """切换搜索框显示状态"""
        current_visibility = self.search_box.isVisible()
        self.search_box.setVisible(not current_visibility)
        logger.debug(t('download.search_box_toggled', visible=not current_visibility))

    def search_items(self):
        """搜索项目"""
        search_text = self.search_box.text().lower()
        matched_index = -1
        for index in range(1, self.combo_box.count()):
            item_text = self.combo_box.itemText(index).lower()
            if search_text in item_text:
                matched_index = index
                break

        if matched_index >= 0:
            self.combo_box.setCurrentIndex(matched_index)
            section_title = self.interface['sections'][matched_index - 1].get('title', '')
            self.copy_to_clipboard(section_title)
            logger.info(t('download.match_found', title=section_title))
        else:
            QMessageBox.warning(self, t('download.not_found'), t('download.no_match'))
            logger.info(t('download.no_match_log'))

    def navigate_to_section(self):
        """导航到指定部分"""
        section_index = self.combo_box.currentIndex() - 1
        if section_index < 0:
            return

        section = self.interface['sections'][section_index]
        section_title = section.get('title', '')
        pivot_item_name = section_title.replace(' ', '-')
        self.pivot.setCurrentItem(pivot_item_name)
        self.stacked_widget.setCurrentIndex(section_index)
        logger.debug(t('download.navigate_to_section', title=section_title))

    @exception_handler(exc_type=ExceptionType.UNKNOWN_ERROR, user_message="Failed to create download card")
    def add_items_to_section(self, section_interface: SettingCardGroup, items: List[Dict[str, Any]]):
        """向部分添加项目"""
        for item in items:
            item_type = item.get('type')
            if not item_type:
                logger.warning(t('download.missing_item_type'))
                continue

            required_fields = {
                'hyperlink': ['url', 'text', 'icon', 'title', 'content'],
                'primary_push_setting': ['text', 'icon', 'title', 'content']
            }.get(item_type)

            if not required_fields or not all(field in item for field in required_fields):
                logger.error(t('download.missing_required_fields', item_type=item_type))
                continue

            item['icon'] = self.resolve_icon(item['icon'])
            try:
                card = self.create_card(item_type, item, required_fields)
                section_interface.addSettingCard(card)
                logger.debug(t('download.card_added', title=item.get("title", t('download.untitled'))))
            except ValueError as e:
                logger.error(t('download.card_creation_failed', error=str(e)))

    def resolve_icon(self, icon_name: str) -> Any:
        """解析图标"""
        if icon_name.startswith('FIF.'):
            return getattr(FIF, icon_name[4:], FIF.DOWNLOAD)
        elif icon_name.startswith('Astro.'):
            return getattr(AstroIcon, icon_name[6:], FIF.DOWNLOAD)
        logger.error(t('download.unknown_icon', icon=icon_name))
        return FIF.DOWNLOAD

    def create_card(self, item_type: str, item: Dict[str, Any], required_fields: List[str]) -> QWidget:
        """创建卡片"""
        card_args = {field: item[field] for field in required_fields}
        if item_type == 'hyperlink':
            return HyperlinkCard(**card_args)
        elif item_type == 'primary_push_setting':
            return PrimaryPushSettingCard(**card_args)
        raise ValueError(t('download.unknown_item_type', item_type=item_type))

    def load_interface_cards(self):
        """加载界面卡片"""
        self.stacked_widget = QStackedWidget(self.scroll_widget)
        for section in self.interface.get('sections', []):
            section_widget = SettingCardGroup(self.scroll_widget)
            self.add_items_to_section(section_widget, section.get('items', []))
            self.add_sub_interface(
                section_widget,
                section.get('id', 'section'),
                section.get('title', t('download.untitled')),
                self.resolve_icon(section.get('icon', 'FIF.DOWNLOAD'))
            )

    def init_widgets(self):
        """初始化窗口组件"""
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        
        self.stacked_widget.currentChanged.connect(self.on_current_index_changed)
        if self.stacked_widget.count() > 0:
            initial_widget = self.stacked_widget.widget(0)
            self.pivot.setCurrentItem(initial_widget.objectName())
            qrouter.setDefaultRouteKey(self.stacked_widget, initial_widget.objectName())
            logger.debug(t('download.initial_interface_set', name=initial_widget.objectName()))

    def add_sub_interface(self, widget: QWidget, object_name: str, text: str, icon: Any = FIF.DOWNLOAD):
        """添加子界面"""
        widget.setObjectName(object_name)
        self.stacked_widget.addWidget(widget)
        self.pivot.addItem(
            icon=icon,
            routeKey=object_name,
            text=text,
            onClick=lambda: self.stacked_widget.setCurrentWidget(widget)
        )
        logger.debug(t('download.sub_interface_added', name=object_name))

    def on_current_index_changed(self, index: int):
        """当前索引改变时的处理"""
        widget = self.stacked_widget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stacked_widget, widget.objectName())
        logger.debug(t('download.current_index_changed', 
                      index=index, 
                      name=widget.objectName()))

    def generate_download_url(
        self, types: str, repo_url: str, mirror_url: Optional[str], 
        mirror_branch: Optional[str] = None, is_add: bool = False
    ) -> str:
        """生成下载URL"""
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

    @exception_handler(exc_type=ExceptionType.DOWNLOAD_ERROR)
    def download_check(self, name: str):
        """检查和处理下载"""
        # 使用默认的下载配置，避免访问不存在的配置属性
        default_url = "https://example.com/default"
        default_mirror = "https://mirror.example.com/default"

        download_mapping: Dict[str, Tuple[Any, str, str, Optional[str], Optional[str]]] = {
            'launcher': (MessageLauncher, 'url', getattr(cfg, 'DOWNLOAD_COMMANDS_LAUNCHER', default_url), 
                        getattr(cfg, 'DOWNLOAD_COMMANDS_LAUNCHER_MIRROR', default_mirror), None),
            'python': (MessagePython, 'url', getattr(cfg, 'DOWNLOAD_COMMANDS_PYTHON', default_url), 
                      getattr(cfg, 'DOWNLOAD_COMMANDS_PYTHON_MIRROR', default_mirror), None),
            'git': (MessageGit, 'url', getattr(cfg, 'DOWNLOAD_COMMANDS_GIT', default_url), 
                   getattr(cfg, 'DOWNLOAD_COMMANDS_GIT_MIRROR', default_mirror), None),
            'java': (MessageJava, 'url', getattr(cfg, 'DOWNLOAD_COMMANDS_JAVA', default_url), 
                    getattr(cfg, 'DOWNLOAD_COMMANDS_JAVA_MIRROR', default_mirror), None),
            'mongodb': (MessageMongoDB, 'url', getattr(cfg, 'DOWNLOAD_COMMANDS_MONGODB', default_url), 
                       getattr(cfg, 'DOWNLOAD_COMMANDS_MONGODB_MIRROR', default_mirror), None),
            'nina': (MessageNINA, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_NINA', default_url), 
                    getattr(cfg, 'DOWNLOAD_COMMANDS_NINA_MIRROR', default_mirror), '--branch nina'),
            'phd2': (MessagePHD2, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_PHD2', default_url), 
                    getattr(cfg, 'DOWNLOAD_COMMANDS_PHD2_MIRROR', default_mirror), '--branch phd2'),
            'sharpcap': (MessageSharpCap, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_SHARPCAP', default_url), 
                        getattr(cfg, 'DOWNLOAD_COMMANDS_SHARPCAP_MIRROR', default_mirror), '--branch sharpcap'),
            'lunarcore': (MessageLunarCore, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_LUNARCORE', default_url), 
                         getattr(cfg, 'DOWNLOAD_COMMANDS_LUNARCORE_MIRROR', default_mirror), '--branch lunarcore'),
            'lunarcoreres': (MessageLunarCoreRes, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_LUNARCORE_RES', default_url), 
                            getattr(cfg, 'DOWNLOAD_COMMANDS_LUNARCORE_RES_MIRROR', default_mirror), '--branch lunarcoreres'),
            'fiddler': (MessageFiddler, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_FIDDLER', default_url), 
                       getattr(cfg, 'DOWNLOAD_COMMANDS_FIDDLER_MIRROR', default_mirror), '--branch fiddler'),
            'mitmdump': (MessageMitmdump, 'git', getattr(cfg, 'DOWNLOAD_COMMANDS_MITMDUMP', default_url), 
                        getattr(cfg, 'DOWNLOAD_COMMANDS_MITMDUMP_MIRROR', default_mirror), '--branch mitmdump')
        }

        mapping = download_mapping.get(name)
        if not mapping:
            logger.error(t('download.unknown_download_type', name=name))
            return

        message_class, types, repo_url, mirror_url, mirror_branch = mapping
        w = message_class(self)
        file_path = Path("temp") / Path(repo_url).name
        command = self.generate_download_url(types, repo_url, mirror_url, mirror_branch, is_add=False)

        if w.exec():
            if not file_path.exists():
                x = MessageDownload(self)
                x.show()
                x.start_download(types, command, str(file_path), '')
                if x.exec():
                    InfoBar.success(
                        title=t('download.success'),
                        content="",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=1000,
                        parent=self
                    )
                    logger.info(t('download.download_success', path=str(file_path)))
                else:
                    InfoBar.error(
                        title=t('download.failed'),
                        content="",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                    logger.error(t('download.download_failed', name=name))
            else:
                InfoBar.error(
                    title=t('download.file_exists'),
                    content="",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                subprocess.Popen(['start', str(file_path)], shell=True)
                logger.warning(t('download.file_exists_open', path=str(file_path)))

    def copy_to_clipboard(self, text: str):
        """复制到剪贴板"""
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(text)
        InfoBar.success(
            title=t('download.copied'),
            content=text,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self
        )
        logger.info(t('download.copied_to_clipboard', text=text))
