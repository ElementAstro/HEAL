"""
Enhanced Download Cards
Provides improved download cards with additional functionality
"""

from typing import Any, Dict, Optional, Union

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon,
    HyperlinkCard,
    InfoBar,
    InfoBarPosition,
    PrimaryPushSettingCard,
    PushButton,
    ToolButton,
)

from ...common.i18n import t
from ...common.logging_config import get_logger


class EnhancedHyperlinkCard(HyperlinkCard):
    """增强的超链接卡片"""

    # 新增信号
    favorited = Signal(str)  # title
    quick_download = Signal(str, str)  # title, url

    def __init__(
        self, url: str, text: str, icon: Union[FluentIcon, str], title: str, content: str, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(url, text, icon, title, content, parent)
        self.logger = get_logger(
            "enhanced_hyperlink_card", module="EnhancedHyperlinkCard"
        )
        self.is_favorited = False
        self._add_enhanced_features()

    def _add_enhanced_features(self) -> None:
        """添加增强功能"""
        # 获取现有布局
        layout = self.layout()
        if not layout:
            return

        # 创建增强功能容器
        enhanced_container = QWidget()
        enhanced_layout = QHBoxLayout(enhanced_container)
        enhanced_layout.setContentsMargins(0, 0, 0, 0)
        enhanced_layout.setSpacing(4)

        # 收藏按钮
        self.favorite_btn = ToolButton(FluentIcon.HEART)
        self.favorite_btn.setToolTip("收藏")
        self.favorite_btn.clicked.connect(self._toggle_favorite)

        # 快速下载按钮
        self.quick_download_btn = ToolButton(FluentIcon.DOWNLOAD)
        self.quick_download_btn.setToolTip("快速下载")
        self.quick_download_btn.clicked.connect(self._quick_download)

        # 复制链接按钮
        self.copy_btn = ToolButton(FluentIcon.COPY)
        self.copy_btn.setToolTip("复制链接")
        self.copy_btn.clicked.connect(self._copy_link)

        enhanced_layout.addWidget(self.favorite_btn)
        enhanced_layout.addWidget(self.quick_download_btn)
        enhanced_layout.addWidget(self.copy_btn)
        enhanced_layout.addStretch()

        # 添加到主布局
        layout.addWidget(enhanced_container)

    def _toggle_favorite(self) -> None:
        """切换收藏状态"""
        self.is_favorited = not self.is_favorited

        if self.is_favorited:
            self.favorite_btn.setIcon(FluentIcon.HEART_FILL)
            self.favorite_btn.setToolTip("取消收藏")
            InfoBar.success(
                title="已收藏",
                content=f"已将 {self.titleLabel.text()} 添加到收藏",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self,
            )
        else:
            self.favorite_btn.setIcon(FluentIcon.HEART)
            self.favorite_btn.setToolTip("收藏")
            InfoBar.info(
                title="已取消收藏",
                content=f"已将 {self.titleLabel.text()} 从收藏中移除",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self,
            )

        self.favorited.emit(self.titleLabel.text())
        self.logger.info(
            f"收藏状态变更: {self.titleLabel.text()} - {self.is_favorited}"
        )

    def _quick_download(self) -> None:
        """快速下载"""
        title = self.titleLabel.text()
        url = self.urlText

        self.quick_download.emit(title, url)
        self.logger.info(f"快速下载请求: {title} - {url}")

        InfoBar.success(
            title="下载开始",
            content=f"开始下载 {title}",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self,
        )

    def _copy_link(self) -> None:
        """复制链接"""
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(self.urlText)

        InfoBar.success(
            title="链接已复制",
            content="链接已复制到剪贴板",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self,
        )

        self.logger.debug(f"链接已复制: {self.urlText}")


class EnhancedPrimaryPushSettingCard(PrimaryPushSettingCard):
    """增强的主要推送设置卡片"""

    # 新增信号
    favorited = Signal(str)  # title
    options_requested = Signal(str)  # title

    def __init__(self, text: str, icon: Union[FluentIcon, str], title: str, content: Optional[str] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, icon, title, content, parent)
        self.logger = get_logger(
            "enhanced_primary_push_card", module="EnhancedPrimaryPushSettingCard"
        )
        self.is_favorited = False
        self._add_enhanced_features()

    def _add_enhanced_features(self) -> None:
        """添加增强功能"""
        # 获取现有的按钮布局
        button_layout = self.hBoxLayout

        # 收藏按钮
        self.favorite_btn = ToolButton(FluentIcon.HEART)
        self.favorite_btn.setToolTip("收藏")
        self.favorite_btn.clicked.connect(self._toggle_favorite)

        # 选项按钮
        self.options_btn = ToolButton(FluentIcon.SETTING)
        self.options_btn.setToolTip("下载选项")
        self.options_btn.clicked.connect(self._show_options)

        # 插入到按钮前面
        button_layout.insertWidget(
            button_layout.count() - 1, self.favorite_btn)
        button_layout.insertWidget(button_layout.count() - 1, self.options_btn)

    def _toggle_favorite(self) -> None:
        """切换收藏状态"""
        self.is_favorited = not self.is_favorited

        if self.is_favorited:
            self.favorite_btn.setIcon(FluentIcon.HEART_FILL)
            self.favorite_btn.setToolTip("取消收藏")
        else:
            self.favorite_btn.setIcon(FluentIcon.HEART)
            self.favorite_btn.setToolTip("收藏")

        self.favorited.emit(self.titleLabel.text())
        self.logger.info(
            f"收藏状态变更: {self.titleLabel.text()} - {self.is_favorited}"
        )

    def _show_options(self) -> None:
        """显示下载选项"""
        title = self.titleLabel.text()
        self.options_requested.emit(title)
        self.logger.info(f"下载选项请求: {title}")


class DownloadCategoryCard(CardWidget):
    """下载分类卡片"""

    category_selected = Signal(str)  # category_name

    def __init__(self, category_name: str, item_count: int, icon: Optional[Union[FluentIcon, str]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.category_name = category_name
        self.item_count = item_count
        self.init_ui(icon)

    def init_ui(self, icon: Optional[Union[FluentIcon, str]]) -> None:
        """初始化UI"""
        self.setFixedHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # 图标
        if icon:
            icon_btn = ToolButton(icon)
            icon_btn.setEnabled(False)
            layout.addWidget(icon_btn)

        # 信息
        info_layout = QVBoxLayout()

        title_label = BodyLabel(self.category_name)
        title_label.setStyleSheet("font-weight: bold;")

        count_label = CaptionLabel(f"{self.item_count} 个项目")
        count_label.setStyleSheet("color: gray;")

        info_layout.addWidget(title_label)
        info_layout.addWidget(count_label)

        layout.addLayout(info_layout, 1)

        # 箭头
        arrow_btn = ToolButton(FluentIcon.CHEVRON_RIGHT)
        arrow_btn.setEnabled(False)
        layout.addWidget(arrow_btn)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.category_selected.emit(self.category_name)
        super().mousePressEvent(event)


class FavoriteCard(CardWidget):
    """收藏卡片"""

    favorite_clicked = Signal(str, str)  # title, url
    favorite_removed = Signal(str)  # title

    def __init__(self, title: str, url: str, category: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.title = title
        self.url = url
        self.category = category
        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI"""
        self.setFixedHeight(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        # 信息
        info_layout = QVBoxLayout()

        title_label = BodyLabel(self.title)
        category_label = CaptionLabel(f"分类: {self.category}")
        category_label.setStyleSheet("color: gray;")

        info_layout.addWidget(title_label)
        info_layout.addWidget(category_label)

        layout.addLayout(info_layout, 1)

        # 操作按钮
        open_btn = ToolButton(FluentIcon.LINK)
        open_btn.setToolTip("打开链接")
        open_btn.clicked.connect(
            lambda: self.favorite_clicked.emit(self.title, self.url)
        )

        remove_btn = ToolButton(FluentIcon.DELETE)
        remove_btn.setToolTip("移除收藏")
        remove_btn.clicked.connect(
            lambda: self.favorite_removed.emit(self.title))

        layout.addWidget(open_btn)
        layout.addWidget(remove_btn)
