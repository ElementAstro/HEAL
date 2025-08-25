import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    ComboBox,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (
    HyperlinkCard,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    Pivot,
    PrimaryPushSettingCard,
    PushButton,
    ScrollArea,
    qrouter,
)

from src.heal.common.exception_handler import (
    ExceptionType,
    exception_handler,
    global_exception_handler,
)
from src.heal.common.i18n import t
from src.heal.common.logging_config import (
    get_logger,
    log_download,
    log_exception,
    log_performance,
    with_correlation_id,
)

# Import the new components
from src.heal.components.download import (
    DownloadCardManager,
    DownloadConfigManager,
    DownloadHandler,
    DownloadNavigationManager,
    DownloadSearchManager,
)
from src.heal.components.download.category_grid import CategoryGridWidget
from src.heal.components.download.download_panel import DownloadPanel
from src.heal.components.download.featured_downloads import FeaturedDownloadsSection
from src.heal.components.download.header_section import DownloadHeaderSection
from src.heal.components.download.responsive_layout import ResponsiveLayoutManager
from src.heal.models.config import cfg
from src.heal.models.setting_card import SettingCardGroup
from src.heal.models.style_sheet import StyleSheet

# 初始化logger和异常处理器
logger = get_logger("download_interface")
# Use the exception handler decorator directly


class Download(ScrollArea):
    Nav = Pivot

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        logger.debug(t("download.loading_interface", interface=text))

        self.parent_widget = parent  # 重命名避免与QWidget.parent()冲突
        self.setObjectName(text.replace(" ", "-"))
        self.scroll_widget = QWidget()
        self.vbox_layout = QVBoxLayout(self.scroll_widget)

        # 使用关联ID追踪界面初始化过程
        with with_correlation_id() as cid:
            logger.info(
                f"初始化下载界面: {text}",
                extra={"interface_name": text, "correlation_id": cid},
            )

            # 初始化组件管理器
            self._init_managers()

            # 初始化UI组件
            self._init_ui_components()

            # 加载配置并设置界面
            self._setup_interface()

            logger.info(f"下载界面初始化完成: {text}")

    def _init_managers(self) -> None:
        """初始化管理器"""
        self.config_manager = DownloadConfigManager(self.scroll_widget)
        self.search_manager = DownloadSearchManager(self.scroll_widget)
        self.card_manager = DownloadCardManager()
        self.download_handler = DownloadHandler(self.scroll_widget)
        self.navigation_manager = DownloadNavigationManager(self.scroll_widget)

        # 连接信号
        self._connect_manager_signals()

    def _init_ui_components(self) -> None:
        """初始化UI组件"""
        # 初始化新的头部组件
        self.header_section = DownloadHeaderSection(self.scroll_widget)
        self.header_section.search_requested.connect(self._on_search_requested)
        self.header_section.category_selected.connect(self._on_category_selected)
        self.header_section.download_requested.connect(
            self._on_quick_download_requested
        )
        self.header_section.status_clicked.connect(self._on_download_status_clicked)

        # 初始化精选下载组件
        self.featured_section = FeaturedDownloadsSection(self.scroll_widget)
        self.featured_section.download_requested.connect(
            self._on_featured_download_requested
        )
        self.featured_section.favorite_toggled.connect(self._on_favorite_toggled)
        self.featured_section.view_all_requested.connect(self._on_view_all_requested)

        # 初始化分类网格组件
        self.category_grid = CategoryGridWidget(self.scroll_widget)
        self.category_grid.category_selected.connect(self._on_category_grid_selected)
        self.category_grid.view_all_categories.connect(self._on_view_all_categories)

        # 初始化搜索组件（保留用于兼容性）
        search_components = self.search_manager.init_search_components()
        self.search_container, self.search_box, self.combo_box = search_components

        # 初始化导航组件
        self.pivot, self.stacked_widget = (
            self.navigation_manager.init_navigation_components(self.Nav)
        )

        # 初始化下载管理面板（转换为侧边栏）
        self.download_panel = DownloadPanel(self.scroll_widget)
        self.download_panel.download_requested.connect(
            self._on_quick_download_requested
        )

        # 初始化刷新按钮
        self.refresh_button = PushButton(t("common.refresh"), self.scroll_widget)
        self.refresh_button.clicked.connect(self.load_interface_from_json)

        # 初始化响应式布局管理器
        self.responsive_manager = ResponsiveLayoutManager(self.scroll_widget)

    def _connect_manager_signals(self) -> None:
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

    def _setup_interface(self) -> None:
        """设置界面"""
        self.load_interface_from_json()
        self.init_widgets()

    def _on_config_loaded(self, interface_data: dict) -> None:
        """配置加载完成处理"""
        self.interface = interface_data
        self.search_manager.set_interface_data(interface_data)

        # 设置新组件的数据
        sections = interface_data.get("sections", [])
        self.header_section.set_categories(sections)
        self.category_grid.set_categories(sections)

        # 更新分类项目计数
        category_counts = {}
        for section in sections:
            section_id = section.get("id", "")
            items = section.get("items", [])
            category_counts[section_id] = len(items)
        self.category_grid.update_category_counts(category_counts)

        self.load_interface_cards()

    def _on_config_load_failed(self, error_message: str) -> None:
        """配置加载失败处理"""
        logger.error(f"配置加载失败: {error_message}")

    def _on_section_found(self, section_title: str) -> None:
        """部分找到处理"""
        self.navigation_manager.navigate_to_section_by_title(section_title)
        self.download_handler.copy_to_clipboard(section_title)

    def _on_search_performed(self, search_text: str) -> None:
        """搜索执行处理"""
        logger.debug(f"执行搜索: {search_text}")

    def _on_download_started(self, name: str, command: str) -> None:
        """下载开始处理"""
        logger.info(f"开始下载: {name}")

    def _on_download_completed(self, name: str, success: bool) -> None:
        """下载完成处理"""
        status = "成功" if success else "失败"
        logger.info(f"下载{status}: {name}")

    def _on_file_exists(self, file_path: str) -> None:
        """文件已存在处理"""
        logger.info(f"文件已存在: {file_path}")

    def _on_navigation_changed(self, section_title: str, index: int) -> None:
        """导航变更处理"""
        logger.debug(f"导航到: {section_title} (索引: {index})")

    def _on_quick_download_requested(self, name: str, url: str) -> None:
        """快速下载请求处理"""
        logger.info(f"快速下载请求: {name} - {url}")
        # 这里可以集成实际的下载逻辑
        InfoBar.success(
            title="下载开始",
            content=f"开始下载 {name}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self.scroll_widget,
        )

    def _on_search_requested(self, search_text: str, category: str) -> None:
        """搜索请求处理"""
        logger.info(f"搜索请求: {search_text} in {category}")
        # 集成现有搜索逻辑
        self.search_manager.perform_search(search_text, category)

    def _on_category_selected(self, category: str) -> None:
        """分类选择处理"""
        logger.info(f"分类选择: {category}")
        # 导航到指定分类
        self.navigation_manager.navigate_to_category(category)

    def _on_download_status_clicked(self) -> None:
        """下载状态点击处理"""
        logger.info("下载状态被点击")
        # 显示下载管理面板或切换到下载页面
        self.download_panel.setVisible(not self.download_panel.isVisible())

    def _on_featured_download_requested(self, name: str, url: str, category: str) -> None:
        """精选下载请求处理"""
        logger.info(f"精选下载请求: {name} - {url} ({category})")
        # 处理精选下载
        self._on_quick_download_requested(name, url)

    def _on_favorite_toggled(self, name: str, is_favorited: bool) -> None:
        """收藏状态切换处理"""
        logger.info(f"收藏状态变更: {name} - {is_favorited}")
        # 这里可以添加收藏管理逻辑

    def _on_view_all_requested(self) -> None:
        """查看全部请求处理"""
        logger.info("查看全部下载请求")
        # 切换到完整下载列表视图

    def _on_category_grid_selected(self, category_id: str, category_title: str) -> None:
        """分类网格选择处理"""
        logger.info(f"分类网格选择: {category_title} ({category_id})")
        # 导航到指定分类
        self.navigation_manager.navigate_to_section_by_id(category_id)

    def _on_view_all_categories(self) -> None:
        """查看全部分类处理"""
        logger.info("查看全部分类请求")
        # 显示完整分类列表

    def _on_layout_mode_changed(self, mode: str) -> None:
        """响应式布局模式变更处理"""
        logger.info(f"布局模式变更: {mode}")
        # 根据布局模式调整组件显示
        if mode == "mobile":
            # 移动端优化
            self.header_section.setVisible(True)  # 保持头部可见
            self.featured_section.setVisible(True)  # 保持精选可见
            # 可以隐藏一些次要组件
        elif mode == "tablet":
            # 平板端优化
            self.header_section.setVisible(True)
            self.featured_section.setVisible(True)
            self.category_grid.setVisible(True)
        else:
            # 桌面端显示所有组件
            self.header_section.setVisible(True)
            self.featured_section.setVisible(True)
            self.category_grid.setVisible(True)

    def _on_sidebar_toggled(self, is_visible: bool) -> None:
        """侧边栏切换处理"""
        logger.info(f"侧边栏切换: {'显示' if is_visible else '隐藏'}")
        # 可以添加额外的侧边栏切换逻辑

    def toggle_sidebar(self) -> None:
        """切换侧边栏显示"""
        if self.responsive_manager:
            self.responsive_manager.toggle_sidebar()

    @exception_handler(exc_type=ExceptionType.DOWNLOAD_ERROR)
    def load_interface_from_json(self) -> None:
        """从JSON文件加载界面配置"""
        self.config_manager.load_configuration()

    def populate_combo_box(self) -> None:
        """填充组合框"""
        # 这个方法现在由 search_manager 处理
        pass

    def toggle_search_box(self) -> None:
        """切换搜索框显示状态"""
        self.search_manager.toggle_search_box()

    def search_items(self) -> None:
        """搜索项目"""
        self.search_manager.search_items()

    def navigate_to_section(self) -> None:
        """导航到指定部分"""
        self.search_manager.navigate_to_section()

    def add_items_to_section(
        self, section_interface: SettingCardGroup, items: List[Dict[str, Any]]
    ):
        """向部分添加项目"""
        self.card_manager.add_items_to_section(section_interface, items)

    def resolve_icon(self, icon_name: str) -> Any:
        """解析图标"""
        return self.card_manager.resolve_icon(icon_name)

    def create_card(
        self, item_type: str, item: Dict[str, Any], required_fields: List[str]
    ) -> QWidget:
        """创建卡片"""
        return self.card_manager.create_card(item_type, item, required_fields)

    def load_interface_cards(self) -> None:
        """加载界面卡片"""
        sections_data = self.config_manager.get_sections()
        section_widgets = self.card_manager.create_section_cards(
            self.scroll_widget, sections_data
        )

        # 设置导航
        self.navigation_manager.setup_sections(section_widgets, sections_data)

        # 完成布局设置
        self._complete_layout_setup()

    def _complete_layout_setup(self) -> None:
        """完成布局设置 - 使用改进的响应式布局"""
        # 创建主分割器（水平方向，右侧为可折叠侧边栏）
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setObjectName("downloadMainSplitter")

        # 左侧：主内容区域（垂直布局）
        main_content = QWidget()
        main_content.setObjectName("downloadMainContent")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Standard margins
        main_layout.setSpacing(24)  # Standard spacing between sections

        # 添加头部组件
        main_layout.addWidget(self.header_section)

        # 添加精选下载组件
        main_layout.addWidget(self.featured_section)

        # 添加分类网格组件
        main_layout.addWidget(self.category_grid)

        # 添加传统的导航和内容区域（保持兼容性）
        traditional_content = QWidget()
        traditional_content.setObjectName("downloadTraditionalContent")
        traditional_layout = QVBoxLayout(traditional_content)
        traditional_layout.setContentsMargins(0, 20, 0, 0)  # Standard top margin
        traditional_layout.setSpacing(16)  # Standard spacing

        # 导航和内容区域
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)  # Standard spacing
        content_layout.addWidget(self.pivot)
        content_layout.addWidget(self.stacked_widget, 1)
        traditional_layout.addLayout(content_layout)

        # 刷新按钮区域
        refresh_layout = QHBoxLayout()
        refresh_layout.setContentsMargins(0, 16, 0, 0)  # Standard margin
        refresh_layout.addStretch()
        refresh_layout.addWidget(self.refresh_button)
        traditional_layout.addLayout(refresh_layout)

        main_layout.addWidget(traditional_content)

        # 右侧：下载管理面板（可折叠侧边栏）
        self.download_panel.setMaximumWidth(400)  # Optimal maximum width
        self.download_panel.setMinimumWidth(300)  # Optimal minimum width
        self.download_panel.setObjectName("downloadSidePanel")

        # 添加到分割器
        main_splitter.addWidget(main_content)
        main_splitter.addWidget(self.download_panel)

        # 设置更合理的初始大小比例（基于黄金比例）
        main_splitter.setSizes([1000, 350])  # 主内容区域更大，侧边栏适中
        main_splitter.setStretchFactor(0, 1)  # 主内容区域可拉伸
        main_splitter.setStretchFactor(1, 0)  # 侧边栏固定大小

        # 设置分割器样式
        main_splitter.setHandleWidth(2)  # Thin splitter handle
        main_splitter.setChildrenCollapsible(True)  # Allow collapsing

        # 添加到主布局
        self.vbox_layout.addWidget(main_splitter)

        # 设置响应式布局管理器
        self.responsive_manager.set_components(
            main_splitter, self.download_panel, main_content
        )
        self.responsive_manager.layout_changed.connect(self._on_layout_mode_changed)
        self.responsive_manager.sidebar_toggled.connect(self._on_sidebar_toggled)

    def init_widgets(self) -> None:
        """初始化窗口组件"""
        # 设置ScrollArea属性以获得最佳性能和用户体验
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setViewportMargins(0, 0, 0, 0)  # 移除边距，让组件自己控制
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)

        # 启用平滑滚动
        self.enableTransparentBackground()

        # 设置滚动行为
        self.verticalScrollBar().setSingleStep(20)  # 更平滑的滚动步长
        self.verticalScrollBar().setPageStep(100)   # 页面滚动步长

        # 应用样式表和对象名称
        self.scroll_widget.setObjectName("downloadScrollWidget")
        self.setObjectName("downloadScrollArea")
        StyleSheet.SETTING_INTERFACE.apply(self)

    def add_sub_interface(
        self, widget: QWidget, object_name: str, text: str, icon: Any = FIF.DOWNLOAD
    ):
        """添加子界面"""
        self.navigation_manager.add_sub_interface(widget, object_name, text, icon)
        logger.debug(t("download.sub_interface_added", name=object_name))

    def on_current_index_changed(self, index: int) -> None:
        """当前索引改变时的处理"""
        self.navigation_manager.navigate_to_index(index)
        widget = self.navigation_manager.get_current_widget()
        if widget:
            logger.debug(
                t(
                    "download.current_index_changed",
                    index=index,
                    name=widget.objectName(),
                )
            )

    def generate_download_url(
        self,
        types: str,
        repo_url: str,
        mirror_url: Optional[str],
        mirror_branch: Optional[str] = None,
        is_add: bool = False,
    ) -> str:
        """生成下载URL"""
        return self.download_handler.generate_download_url(
            types, repo_url, mirror_url, mirror_branch, is_add
        )

    @exception_handler(exc_type=ExceptionType.DOWNLOAD_ERROR)
    @log_performance("download_operation")
    def download_check(self, name: str) -> None:
        """检查和处理下载 - 带性能监控和结构化日志"""
        logger.info(f"开始下载检查: {name}")

        with with_correlation_id() as cid:
            # 记录下载开始
            log_download("下载检查开始", name=name, correlation_id=cid)

            # 使用下载处理器处理下载
            self.download_handler.handle_download(name)

    def download(self, name: str) -> None:
        """下载方法"""
        self.download_handler.handle_download(name)

    def copy_to_clipboard(self, text: str) -> None:
        """复制到剪贴板"""
        self.download_handler.copy_to_clipboard(text)
