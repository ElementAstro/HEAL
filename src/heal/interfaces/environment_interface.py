import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    FluentIcon,
    InfoBar,
    InfoBarIcon,
    InfoBarPosition,
    PrimaryPushButton,
    PrimaryPushSettingCard,
    ScrollArea,
)

from .setting_interface import Setting

from ..common.logging_config import get_logger, log_performance, with_correlation_id
from ..components.environment.config_manager import EnvironmentConfigManager

# Import new enhanced components
from ..components.environment.enhanced_cards import (
    EnvironmentStatusCard,
    QuickActionPanel,
    SmartToolCard,
    ToolCategorySection,
)

# Import environment components
from ..components.environment.environment_cards import (
    HyperlinkCardEnvironment,
    PrimaryPushSettingCardDownload,
)
from ..components.environment.platform_detector import get_current_platform_info
from ..components.environment.signal_manager import EnvironmentSignalManager
from ..components.environment.tool_status_manager import ToolStatus, ToolStatusManager
from ..models.config import Info
from ..models.download_process import SubDownloadCMD
from ..models.setting_card import SettingCard, SettingCardGroup
from ..models.style_sheet import StyleSheet

# 使用统一日志配置
logger = get_logger("environment_interface")


class Environment(ScrollArea):
    """优化后的环境配置界面 - 单页面布局，更好的用户体验"""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self._parent_widget = parent
        self.setObjectName(text)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        # 初始化管理器
        self.config_manager = EnvironmentConfigManager(self)
        self.tool_status_manager = ToolStatusManager(self)
        self.signal_manager = EnvironmentSignalManager(self, None)  # 将在后面重新配置
        self.platform_info = get_current_platform_info()

        # UI组件
        self.quick_action_panel: Any = None
        self.status_section: Any = None
        self.runtime_section: Any = None
        self.database_section: Any = None
        self.version_control_section: Any = None
        self.download_section: Any = None

        self.init_widget()

    def init_widget(self) -> None:
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self.scrollWidget.setObjectName("scrollWidget")
        StyleSheet.ENVIRONMENT_INTERFACE.apply(self)

        self.init_new_layout()
        self.connect_signals()
        self.start_status_monitoring()

    def init_new_layout(self) -> None:
        """初始化新的单页面布局"""
        # 设置主布局
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)

        # 1. 页面标题
        self.create_page_header()

        # 2. 快速操作面板
        self.create_quick_action_panel()

        # 3. 环境状态概览
        self.create_status_overview()

        # 4. 开发工具分类
        self.create_tool_categories()

        # 5. 高级选项
        self.create_advanced_options()

        logger.info("新布局初始化完成")

    def create_page_header(self) -> None:
        """创建页面标题"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 0, 16, 0)

        # 主标题
        title_label = BodyLabel("开发环境配置")
        title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #323130;")

        # 副标题
        subtitle_label = CaptionLabel(f"当前平台: {str(self.platform_info)}")
        subtitle_label.setStyleSheet("color: #605e5c; margin-top: 4px;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_layout.addSpacing(10)

        self.vBoxLayout.addWidget(header_widget)

    def create_quick_action_panel(self) -> None:
        """创建快速操作面板"""
        self.quick_action_panel = QuickActionPanel()
        self.quick_action_panel.action_requested.connect(
            self.handle_quick_action)
        self.vBoxLayout.addWidget(self.quick_action_panel)

    def create_status_overview(self) -> None:
        """创建环境状态概览"""
        self.status_section = ToolCategorySection(
            "环境状态概览", "查看已安装工具的状态和快速启动"
        )
        self.vBoxLayout.addWidget(self.status_section)

    def create_tool_categories(self) -> None:
        """创建工具分类区域"""
        # 版本控制工具
        self.version_control_section = ToolCategorySection(
            "版本控制", "Git 等版本控制工具"
        )
        self.vBoxLayout.addWidget(self.version_control_section)

        # 运行时环境
        self.runtime_section = ToolCategorySection(
            "运行时环境", "Java, Node.js, Python 等开发运行时"
        )
        self.vBoxLayout.addWidget(self.runtime_section)

        # 数据库
        self.database_section = ToolCategorySection("数据库", "MongoDB 等数据库系统")
        self.vBoxLayout.addWidget(self.database_section)

    def create_advanced_options(self) -> None:
        """创建高级选项区域"""
        self.download_section = ToolCategorySection(
            "高级选项", "官方下载链接和其他选项"
        )
        self.vBoxLayout.addWidget(self.download_section)

    def connect_signals(self) -> None:
        # 连接工具状态管理器信号
        self.tool_status_manager.status_updated.connect(
            self.on_tool_status_updated)
        self.tool_status_manager.all_status_updated.connect(
            self.on_all_status_updated)

        logger.info("信号已连接到槽。")

    def handle_quick_action(self, action_type: str, target: str) -> None:
        """处理快速操作"""
        if action_type == "refresh":
            self.tool_status_manager.refresh_all_status()
            logger.info("手动刷新所有工具状态")
        elif action_type == "open_folder":
            # 打开工具目录的逻辑
            logger.info("打开工具目录请求")

    def handle_download_request(self, tool_name: str, option_key: str) -> None:
        """处理下载请求"""
        # 使用现有的下载处理逻辑
        self.signal_manager.handle_download_started(option_key)
        logger.info(f"下载请求: {tool_name} - {option_key}")

    def on_tool_status_updated(self, tool_name: str, tool_info: Any) -> None:
        """工具状态更新回调"""
        # 更新对应的状态卡片
        self.update_status_card(tool_name, tool_info)

    def on_all_status_updated(self, all_status: Dict) -> None:
        """所有工具状态更新回调"""
        for tool_name, tool_info in all_status.items():
            self.update_status_card(tool_name, tool_info)

    def update_status_card(self, tool_name: str, tool_info: Any) -> None:
        """更新状态卡片"""
        # 查找或创建状态卡片
        status_card = self.find_or_create_status_card(tool_name, tool_info)
        if status_card:
            status_card.update_status(tool_info)

    def find_or_create_status_card(self, tool_name: str, tool_info: Any) -> Any:
        """查找或创建状态卡片"""
        # 在状态区域查找现有卡片
        if hasattr(self.status_section, "findChild"):
            existing_card = self.status_section.findChild(
                EnvironmentStatusCard, f"status_{tool_name}"
            )
            if existing_card:
                return existing_card

        # 创建新的状态卡片
        status_card = EnvironmentStatusCard(tool_name, tool_info)
        status_card.setObjectName(f"status_{tool_name}")

        # 连接信号
        status_card.launch_requested.connect(self.handle_tool_launch)
        status_card.install_requested.connect(self.handle_tool_install)
        status_card.update_requested.connect(self.handle_tool_update)
        status_card.configure_requested.connect(self.handle_tool_configure)

        # 添加到状态区域
        if self.status_section and hasattr(self.status_section, "add_tool_card"):
            self.status_section.add_tool_card(status_card)

        return status_card

    def handle_tool_launch(self, tool_name: str) -> None:
        """处理工具启动"""
        if tool_name.lower() == "mongodb":
            self.handle_mongo_db_open()
        else:
            logger.info(f"启动工具请求: {tool_name}")

    def handle_tool_install(self, tool_name: str) -> None:
        """处理工具安装"""
        logger.info(f"安装工具请求: {tool_name}")

    def handle_tool_update(self, tool_name: str) -> None:
        """处理工具更新"""
        logger.info(f"更新工具请求: {tool_name}")

    def handle_tool_configure(self, tool_name: str) -> None:
        """处理工具配置"""
        logger.info(f"配置工具请求: {tool_name}")

    def start_status_monitoring(self) -> None:
        """启动状态监控"""
        # 初始化工具状态
        self.tool_status_manager.refresh_all_status()

        # 加载下载配置
        self.load_download_config()

        # 启动自动刷新
        self.tool_status_manager.start_auto_refresh()

    def load_download_config(self) -> None:
        """加载下载配置并创建智能卡片"""
        config_data = self.config_manager.config_data

        for item in config_data:
            if item.get("type") == "link":
                # 创建链接卡片
                link_card = HyperlinkCardEnvironment(
                    item.get("title", ""),
                    item.get("content", ""),
                    FluentIcon.LINK,
                    item.get("links", {}),
                )
                if self.download_section and hasattr(
                    self.download_section, "add_tool_card"
                ):
                    self.download_section.add_tool_card(link_card)

            elif item.get("type") == "download":
                # 创建智能下载卡片
                smart_card = SmartToolCard(
                    item.get("title", ""),
                    item.get("content", ""),
                    item.get("options", []),
                )
                smart_card.download_requested.connect(
                    self.handle_download_request)

                # 根据工具类型添加到相应分类
                tool_name = item.get("title", "").lower()
                if tool_name == "git" and self.version_control_section:
                    self.version_control_section.add_tool_card(smart_card)
                elif tool_name in ["java", "nodejs", "python"] and self.runtime_section:
                    self.runtime_section.add_tool_card(smart_card)
                elif tool_name == "mongodb" and self.database_section:
                    self.database_section.add_tool_card(smart_card)
                elif self.download_section:
                    self.download_section.add_tool_card(smart_card)

    # 移除了旧的导航方法，因为新布局不使用标签页导航

    def handle_mongo_db_open(self) -> None:
        """处理MongoDB打开"""
        mongo_exe = Path("tool") / "mongodb" / "mongod.exe"
        if mongo_exe.exists():
            try:
                subprocess.Popen(
                    [
                        "cmd",
                        "/c",
                        f'cd /d "{mongo_exe.parent}" && mongod --dbpath data --port 27017',
                    ],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
                Info(self, "S", 1000, self.tr("数据库已开始运行!"))
                logger.info("MongoDB 已启动。")
            except Exception as e:
                Info(self, "E", 3000, self.tr("启动数据库失败！"), str(e))
                logger.error(f"启动 MongoDB 失败: {e}")
        else:
            file_error = InfoBar(
                icon=InfoBarIcon.ERROR,
                title=self.tr("找不到数据库!"),
                content="",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            file_error_button = PrimaryPushButton(self.tr("前往下载"), self)
            file_error_button.clicked.connect(
                lambda: self.signal_manager.download_to_page_requested.emit(1)
            )
            file_error.addWidget(file_error_button)
            file_error.show()
            logger.warning("MongoDB 文件不存在。")
