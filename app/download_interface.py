import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from app.common.logging_config import get_logger, log_performance, with_correlation_id, log_download, log_exception
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

# Import the new components
from app.components.download import (
    DownloadSearchManager, DownloadCardManager, DownloadHandler,
    DownloadConfigManager, DownloadNavigationManager
)

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

        # 使用关联ID追踪界面初始化过程
        with with_correlation_id() as cid:
            logger.info(f"初始化下载界面: {text}", extra={"interface_name": text, "correlation_id": cid})
            
            # 初始化组件管理器
            self._init_managers()
            
            # 初始化UI组件
            self._init_ui_components()
            
            # 加载配置并设置界面
            self._setup_interface()
            
            logger.info(f"下载界面初始化完成: {text}")

    def _init_managers(self):
        """初始化管理器"""
        self.config_manager = DownloadConfigManager(self.scroll_widget)
        self.search_manager = DownloadSearchManager(self.scroll_widget)
        self.card_manager = DownloadCardManager()
        self.download_handler = DownloadHandler(self.scroll_widget)
        self.navigation_manager = DownloadNavigationManager(self.scroll_widget)
        
        # 连接信号
        self._connect_manager_signals()

    def _init_ui_components(self):
        """初始化UI组件"""
        # 初始化搜索组件
        search_components = self.search_manager.init_search_components()
        self.search_box, self.search_button, self.toggle_search_button, self.combo_box = search_components
        
        # 初始化导航组件
        self.pivot, self.stacked_widget = self.navigation_manager.init_navigation_components(self.Nav)
        
        # 初始化刷新按钮
        self.refresh_button = PushButton(t('common.refresh'), self.scroll_widget)
        self.refresh_button.clicked.connect(self.load_interface_from_json)

    def _connect_manager_signals(self):
        """连接管理器信号"""
        # 配置管理器信号
        self.config_manager.config_loaded.connect(self._on_config_loaded)
        self.config_manager.config_load_failed.connect(self._on_config_load_failed)
        
        # 搜索管理器信号
        self.search_manager.section_found.connect(self._on_section_found)
        self.search_manager.search_performed.connect(self._on_search_performed)
        
        # 下载处理器信号
        self.download_handler.download_started.connect(self._on_download_started)
        self.download_handler.download_completed.connect(self._on_download_completed)
        self.download_handler.file_exists.connect(self._on_file_exists)
        
        # 导航管理器信号
        self.navigation_manager.navigation_changed.connect(self._on_navigation_changed)

    def _setup_interface(self):
        """设置界面"""
        self.load_interface_from_json()
        self.init_widgets()

    def _on_config_loaded(self, interface_data: dict):
        """配置加载完成处理"""
        self.interface = interface_data
        self.search_manager.set_interface_data(interface_data)
        self.load_interface_cards()

    def _on_config_load_failed(self, error_message: str):
        """配置加载失败处理"""
        logger.error(f"配置加载失败: {error_message}")

    def _on_section_found(self, section_title: str):
        """部分找到处理"""
        self.navigation_manager.navigate_to_section_by_title(section_title)
        self.download_handler.copy_to_clipboard(section_title)

    def _on_search_performed(self, search_text: str):
        """搜索执行处理"""
        logger.debug(f"执行搜索: {search_text}")

    def _on_download_started(self, name: str, command: str):
        """下载开始处理"""
        logger.info(f"开始下载: {name}")

    def _on_download_completed(self, name: str, success: bool):
        """下载完成处理"""
        status = "成功" if success else "失败"
        logger.info(f"下载{status}: {name}")

    def _on_file_exists(self, file_path: str):
        """文件已存在处理"""
        logger.info(f"文件已存在: {file_path}")

    def _on_navigation_changed(self, section_title: str, index: int):
        """导航变更处理"""
        logger.debug(f"导航到: {section_title} (索引: {index})")



    @exception_handler(exc_type=ExceptionType.DOWNLOAD_ERROR)
    def load_interface_from_json(self):
        """从JSON文件加载界面配置"""
        self.config_manager.load_configuration()

    def populate_combo_box(self):
        """填充组合框"""
        # 这个方法现在由 search_manager 处理
        pass

    def toggle_search_box(self):
        """切换搜索框显示状态"""
        self.search_manager.toggle_search_box()

    def search_items(self):
        """搜索项目"""
        self.search_manager.search_items()

    def navigate_to_section(self):
        """导航到指定部分"""
        self.search_manager.navigate_to_section()

    def add_items_to_section(self, section_interface: SettingCardGroup, items: List[Dict[str, Any]]):
        """向部分添加项目"""
        self.card_manager.add_items_to_section(section_interface, items)

    def resolve_icon(self, icon_name: str) -> Any:
        """解析图标"""
        return self.card_manager.resolve_icon(icon_name)

    def create_card(self, item_type: str, item: Dict[str, Any], required_fields: List[str]) -> QWidget:
        """创建卡片"""
        return self.card_manager.create_card(item_type, item, required_fields)

    def load_interface_cards(self):
        """加载界面卡片"""
        sections_data = self.config_manager.get_sections()
        section_widgets = self.card_manager.create_section_cards(self.scroll_widget, sections_data)
        
        # 设置导航
        self.navigation_manager.setup_sections(section_widgets, sections_data)
        
        # 完成布局设置
        self._complete_layout_setup()

    def _complete_layout_setup(self):
        """完成布局设置"""
        search_components = (self.search_box, self.search_button, self.toggle_search_button, self.combo_box)
        self.navigation_manager.setup_layout(self.vbox_layout, self.refresh_button, search_components)

    def init_widgets(self):
        """初始化窗口组件"""
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)

        # 应用样式表
        self.scroll_widget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

    def add_sub_interface(self, widget: QWidget, object_name: str, text: str, icon: Any = FIF.DOWNLOAD):
        """添加子界面"""
        self.navigation_manager.add_sub_interface(widget, object_name, text, icon)
        logger.debug(t('download.sub_interface_added', name=object_name))

    def on_current_index_changed(self, index: int):
        """当前索引改变时的处理"""
        self.navigation_manager.navigate_to_index(index)
        widget = self.navigation_manager.get_current_widget()
        if widget:
            logger.debug(t('download.current_index_changed', 
                          index=index, 
                          name=widget.objectName()))

    def generate_download_url(
        self, types: str, repo_url: str, mirror_url: Optional[str], 
        mirror_branch: Optional[str] = None, is_add: bool = False
    ) -> str:
        """生成下载URL"""
        return self.download_handler.generate_download_url(types, repo_url, mirror_url, mirror_branch, is_add)

    @exception_handler(exc_type=ExceptionType.DOWNLOAD_ERROR)
    @log_performance("download_operation")
    def download_check(self, name: str):
        """检查和处理下载 - 带性能监控和结构化日志"""
        logger.info(f"开始下载检查: {name}")
        
        with with_correlation_id() as cid:
            # 记录下载开始
            log_download(
                "下载检查开始",
                name=name,
                correlation_id=cid
            )
            
            # 使用下载处理器处理下载
            self.download_handler.handle_download(name)

    def download(self, name: str):
        """下载方法"""
        self.download_handler.handle_download(name)

    def copy_to_clipboard(self, text: str):
        """复制到剪贴板"""
        self.download_handler.copy_to_clipboard(text)
