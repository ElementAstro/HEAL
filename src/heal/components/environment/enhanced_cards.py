"""
Enhanced Environment Card Components
New card types with improved visual design and context-aware functionality
"""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    ComboBox,
    FluentIcon,
    IconWidget,
    IndeterminateProgressBar,
    InfoBadge,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    ToolTip,
)

from src.heal.common.logging_config import get_logger
from src.heal.models.setting_card import SettingCard, SettingCardGroup
from .platform_detector import get_current_platform_info
from .tool_status_manager import ToolInfo, ToolStatus


class EnvironmentStatusCard(SettingCard):
    """环境状态卡片 - 显示工具状态和快速操作"""

    launch_requested = Signal(str)  # tool_name
    install_requested = Signal(str)  # tool_name
    update_requested = Signal(str)  # tool_name
    configure_requested = Signal(str)  # tool_name

    def __init__(self, tool_name: str, tool_info: ToolInfo, parent: Any = None) -> None:
        # 根据状态选择图标
        icon = self._get_status_icon(tool_info.status)
        super().__init__(icon, tool_name, tool_info.version or "未安装", parent)

        self.tool_name = tool_name
        self.tool_info = tool_info
        self.logger = get_logger(
            "environment_status_card", module="EnvironmentStatusCard"
        )

        self.init_ui()
        self.update_status(tool_info)

    def _get_status_icon(self, status: ToolStatus) -> FluentIcon:
        """根据状态获取图标"""
        status_icons = {
            ToolStatus.INSTALLED: FluentIcon.ACCEPT,
            ToolStatus.NOT_INSTALLED: FluentIcon.CANCEL,
            ToolStatus.NEEDS_UPDATE: FluentIcon.UPDATE,
            ToolStatus.CHECKING: FluentIcon.SYNC,
            ToolStatus.ERROR: FluentIcon.WARNING,
            ToolStatus.UNKNOWN: FluentIcon.HELP,
        }
        return status_icons.get(status, FluentIcon.HELP)

    def init_ui(self) -> None:
        """初始化UI"""
        # 状态指示器
        self.status_badge = InfoBadge("", self)
        self.status_badge.setFixedSize(80, 20)

        # 主要操作按钮
        self.primary_button = PrimaryPushButton("", self)
        self.primary_button.setFixedWidth(100)

        # 次要操作按钮
        self.secondary_button = PushButton("配置", self)
        self.secondary_button.setFixedWidth(60)
        self.secondary_button.clicked.connect(
            lambda: self.configure_requested.emit(self.tool_name)
        )

        # 进度条（用于显示安装/更新进度）
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(4)

        # 布局
        self.hBoxLayout.addWidget(self.status_badge, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.secondary_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.primary_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        # 在卡片底部添加进度条
        self.vBoxLayout.addWidget(self.progress_bar)

    def update_status(self, tool_info: ToolInfo) -> None:
        """更新状态显示"""
        self.tool_info = tool_info

        # 更新图标
        self.iconWidget.setIcon(self._get_status_icon(tool_info.status))

        # 更新内容文本
        if tool_info.version:
            self.contentLabel.setText(f"版本: {tool_info.version}")
        else:
            self.contentLabel.setText(self._get_status_text(tool_info.status))

        # 更新状态徽章
        self._update_status_badge(tool_info.status)

        # 更新按钮
        self._update_buttons(tool_info.status)

        # 更新进度条
        if tool_info.status == ToolStatus.CHECKING:
            self.progress_bar.setVisible(True)
            self.progress_bar.start()
        else:
            self.progress_bar.setVisible(False)
            self.progress_bar.stop()

    def _get_status_text(self, status: ToolStatus) -> str:
        """获取状态文本"""
        status_texts = {
            ToolStatus.INSTALLED: "已安装",
            ToolStatus.NOT_INSTALLED: "未安装",
            ToolStatus.NEEDS_UPDATE: "需要更新",
            ToolStatus.CHECKING: "检查中...",
            ToolStatus.ERROR: "检查出错",
            ToolStatus.UNKNOWN: "未知状态",
        }
        return status_texts.get(status, "未知")

    def _update_status_badge(self, status: ToolStatus) -> None:
        """更新状态徽章"""
        status_configs = {
            ToolStatus.INSTALLED: ("已安装", "success"),
            ToolStatus.NOT_INSTALLED: ("未安装", "warning"),
            ToolStatus.NEEDS_UPDATE: ("需更新", "attention"),
            ToolStatus.CHECKING: ("检查中", "informational"),
            ToolStatus.ERROR: ("错误", "critical"),
            ToolStatus.UNKNOWN: ("未知", "informational"),
        }

        text, style = status_configs.get(status, ("未知", "informational"))
        self.status_badge.setText(text)
        # 这里可以根据需要设置不同的样式

    def _update_buttons(self, status: ToolStatus) -> None:
        """更新按钮状态"""
        if status == ToolStatus.INSTALLED:
            self.primary_button.setText("启动")
            self.primary_button.clicked.disconnect()
            self.primary_button.clicked.connect(
                lambda: self.launch_requested.emit(self.tool_name)
            )
            self.primary_button.setEnabled(True)
            self.secondary_button.setEnabled(True)

        elif status == ToolStatus.NOT_INSTALLED:
            self.primary_button.setText("安装")
            self.primary_button.clicked.disconnect()
            self.primary_button.clicked.connect(
                lambda: self.install_requested.emit(self.tool_name)
            )
            self.primary_button.setEnabled(True)
            self.secondary_button.setEnabled(False)

        elif status == ToolStatus.NEEDS_UPDATE:
            self.primary_button.setText("更新")
            self.primary_button.clicked.disconnect()
            self.primary_button.clicked.connect(
                lambda: self.update_requested.emit(self.tool_name)
            )
            self.primary_button.setEnabled(True)
            self.secondary_button.setEnabled(True)

        elif status == ToolStatus.CHECKING:
            self.primary_button.setText("检查中")
            self.primary_button.setEnabled(False)
            self.secondary_button.setEnabled(False)

        else:  # ERROR or UNKNOWN
            self.primary_button.setText("重试")
            self.primary_button.clicked.disconnect()
            self.primary_button.clicked.connect(
                lambda: self.install_requested.emit(self.tool_name)
            )
            self.primary_button.setEnabled(True)
            self.secondary_button.setEnabled(False)


class SmartToolCard(SettingCard):
    """智能工具卡片 - 根据平台和状态自适应的下载卡片"""

    download_requested = Signal(str, str)  # tool_name, option_key

    def __init__(
        self,
        title: str,
        content: str,
        options: List[Dict],
        tool_status: Optional[ToolStatus] = None,
        parent: Any = None,
    ) -> None:
        super().__init__(FluentIcon.DOWNLOAD, title, content, parent)

        self.tool_name = title.lower()
        self.options = options
        self.tool_status = tool_status or ToolStatus.NOT_INSTALLED
        self.platform_info = get_current_platform_info()
        self.logger = get_logger("smart_tool_card", module="SmartToolCard")

        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI"""
        # 平台选择器
        self.platform_combo = ComboBox(self)
        self.platform_combo.setFixedWidth(120)

        # 下载按钮
        self.download_button = PrimaryPushButton("下载", self)
        self.download_button.setFixedWidth(80)

        # 填充选项
        self._populate_options()

        # 连接信号
        self.download_button.clicked.connect(self._on_download_clicked)

        # 布局
        self.hBoxLayout.addWidget(self.platform_combo, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.download_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _populate_options(self) -> None:
        """填充下载选项"""
        if not self.options:
            return

        # 根据平台推荐选项
        from .platform_detector import get_recommended_download_options

        sorted_options = get_recommended_download_options(self.options)

        for option in sorted_options:
            display_name = option.get("name", "")
            # 如果是推荐平台，添加标记
            if self.platform_info.get_platform_key() in option.get("key", "").lower():
                display_name += " (推荐)"

            self.platform_combo.addItem(display_name, option)

        # 默认选择第一个（推荐的）
        if sorted_options:
            self.platform_combo.setCurrentIndex(0)

    def _on_download_clicked(self) -> None:
        """处理下载点击"""
        current_data = self.platform_combo.currentData()
        if current_data:
            option_key = current_data.get("key", "")
            self.download_requested.emit(self.tool_name, option_key)
            self.logger.info(f"下载请求: {self.tool_name} - {option_key}")


class ToolCategorySection(SettingCardGroup):
    """工具分类区域 - 可折叠的工具分组"""

    def __init__(self, title: str, description: str = "", parent: Any = None) -> None:
        super().__init__(parent)
        self.title = title
        self.description = description
        self.logger = get_logger("tool_category_section", module="ToolCategorySection")

        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI"""
        # 创建标题区域
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(16, 12, 16, 12)

        # 标题标签
        title_label = BodyLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)

        title_layout.addWidget(title_label)

        # 描述标签
        if self.description:
            desc_label = CaptionLabel(self.description)
            desc_label.setTextColor(QColor(96, 96, 96), QColor(160, 160, 160))
            title_layout.addWidget(desc_label)

        # 添加到布局顶部
        self.vBoxLayout.insertWidget(0, title_widget)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedHeight(1)
        self.vBoxLayout.insertWidget(1, separator)

    def add_tool_card(self, card: SettingCard) -> None:
        """添加工具卡片"""
        self.addSettingCard(card)
        self.logger.debug(
            f"工具卡片已添加到分类 {self.title}: {card.titleLabel.text()}"
        )


class QuickActionPanel(QWidget):
    """快速操作面板"""

    action_requested = Signal(str, str)  # action_type, target

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = get_logger("quick_action_panel", module="QuickActionPanel")
        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # 标题
        title_label = BodyLabel("快速操作")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)

        layout.addWidget(title_label)
        layout.addSpacerItem(
            QSpacerItem(
                40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
            )
        )

        # 快速操作按钮
        self.refresh_button = PushButton("刷新状态", self)
        self.refresh_button.setIcon(FluentIcon.SYNC)
        self.refresh_button.clicked.connect(
            lambda: self.action_requested.emit("refresh", "all")
        )

        self.open_folder_button = PushButton("打开工具目录", self)
        self.open_folder_button.setIcon(FluentIcon.FOLDER)
        self.open_folder_button.clicked.connect(
            lambda: self.action_requested.emit("open_folder", "tools")
        )

        layout.addWidget(self.refresh_button)
        layout.addSpacing(10)
        layout.addWidget(self.open_folder_button)
