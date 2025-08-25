"""
Featured Downloads Component
Showcases popular and recommended downloads prominently
"""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon,
    HyperlinkButton,
    InfoBadge,
    InfoLevel,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    ToolButton,
)

from src.heal.common.i18n import t
from src.heal.common.logging_config import get_logger


class FeaturedDownloadCard(CardWidget):
    """Individual featured download card"""

    download_requested = Signal(str, str, str)  # name, url, category
    favorite_toggled = Signal(str, bool)  # name, is_favorited

    def __init__(self, item_data: Dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self.item_data = item_data
        self.is_favorited = False
        self.logger = get_logger(
            "featured_download_card", module="FeaturedDownloadCard"
        )
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize UI"""
        # Remove fixed size to allow responsive behavior
        self.setMinimumSize(260, 140)
        self.setMaximumSize(320, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Use proper layout structure for CardWidget
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Header with icon and favorite button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Icon
        icon_name = self.item_data.get("icon", "FIF.DOWNLOAD")
        icon = self._resolve_icon(icon_name)
        self.icon_btn = ToolButton(icon)
        self.icon_btn.setFixedSize(32, 32)
        self.icon_btn.setEnabled(False)
        header_layout.addWidget(self.icon_btn)

        # Title and category
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        self.title_label = StrongBodyLabel(self.item_data.get("title", "未知"))
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(self.title_label)

        category = self.item_data.get("category", "其他")
        self.category_label = CaptionLabel(f"分类: {category}")
        self.category_label.setStyleSheet("color: gray;")
        title_layout.addWidget(self.category_label)

        header_layout.addLayout(title_layout, 1)

        # Favorite button
        self.favorite_btn = ToolButton(FluentIcon.HEART)
        self.favorite_btn.setFixedSize(24, 24)
        self.favorite_btn.setToolTip("收藏")
        self.favorite_btn.clicked.connect(self._toggle_favorite)
        header_layout.addWidget(self.favorite_btn)

        layout.addLayout(header_layout)

        # Description
        description = self.item_data.get(
            "content", self.item_data.get("description", "")
        )
        if description:
            self.desc_label = BodyLabel(description)
            self.desc_label.setWordWrap(True)
            self.desc_label.setStyleSheet("color: #888; font-size: 12px;")
            # Limit description height
            self.desc_label.setMaximumHeight(40)
            layout.addWidget(self.desc_label)

        # Tags/badges (if any)
        tags = self.item_data.get("tags", [])
        if tags:
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(4)

            for tag in tags[:3]:  # Show max 3 tags
                badge = InfoBadge.info(tag, self)
                badge.setFixedHeight(20)
                tags_layout.addWidget(badge)

            tags_layout.addStretch()
            layout.addLayout(tags_layout)

        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        # Download button
        self.download_btn = PrimaryPushButton("下载")
        self.download_btn.setIcon(FluentIcon.DOWNLOAD)
        self.download_btn.setFixedHeight(32)
        self.download_btn.clicked.connect(self._on_download_clicked)
        actions_layout.addWidget(self.download_btn, 1)

        # More info button (if URL available)
        url = self.item_data.get("url", "")
        if url:
            self.info_btn = PushButton("详情")
            self.info_btn.setIcon(FluentIcon.INFO)
            self.info_btn.setFixedHeight(32)
            self.info_btn.clicked.connect(self._on_info_clicked)
            actions_layout.addWidget(self.info_btn)

        layout.addLayout(actions_layout)

        # Set the layout to the CardWidget
        self.setLayout(layout)

    def _resolve_icon(self, icon_name: str) -> None:
        """Resolve icon from name"""
        if icon_name.startswith("FIF."):
            return getattr(FluentIcon, icon_name[4:], FluentIcon.DOWNLOAD)
        elif icon_name.startswith("Astro."):
            # Import AstroIcon if available
            try:
                from src.icon.astro import AstroIcon

                return getattr(AstroIcon, icon_name[6:], FluentIcon.DOWNLOAD)
            except ImportError:
                return FluentIcon.DOWNLOAD
        return FluentIcon.DOWNLOAD

    def _toggle_favorite(self) -> None:
        """Toggle favorite status"""
        self.is_favorited = not self.is_favorited

        if self.is_favorited:
            self.favorite_btn.setIcon(FluentIcon.HEART_FILL)
            self.favorite_btn.setToolTip("取消收藏")
        else:
            self.favorite_btn.setIcon(FluentIcon.HEART)
            self.favorite_btn.setToolTip("收藏")

        name = self.item_data.get("title", "")
        self.favorite_toggled.emit(name, self.is_favorited)
        self.logger.info(f"收藏状态变更: {name} - {self.is_favorited}")

    def _on_download_clicked(self) -> None:
        """Handle download button click"""
        name = self.item_data.get("title", "")
        url = self.item_data.get("url", "")
        category = self.item_data.get("category", "")

        self.download_requested.emit(name, url, category)
        self.logger.info(f"下载请求: {name} - {url}")

    def _on_info_clicked(self) -> None:
        """Handle info button click"""
        url = self.item_data.get("url", "")
        if url:
            import webbrowser

            webbrowser.open(url)
            self.logger.info(f"打开详情页面: {url}")


class FeaturedDownloadsSection(CardWidget):
    """Featured downloads section with multiple cards"""

    download_requested = Signal(str, str, str)  # name, url, category
    favorite_toggled = Signal(str, bool)  # name, is_favorited
    view_all_requested = Signal()  # User wants to see all downloads

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.logger = get_logger(
            "featured_downloads_section", module="FeaturedDownloadsSection"
        )
        self.featured_items: list[Any] = []
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize UI"""
        # Use proper layout structure for CardWidget
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Title and subtitle
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title_label = StrongBodyLabel("精选下载")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)

        subtitle_label = CaptionLabel("热门推荐和常用工具")
        subtitle_label.setStyleSheet("color: gray;")
        title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout, 1)

        # View all button
        self.view_all_btn = HyperlinkButton("查看全部", "")
        self.view_all_btn.clicked.connect(self.view_all_requested)
        header_layout.addWidget(self.view_all_btn)

        layout.addLayout(header_layout)

        # Featured cards container
        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.cards_widget)

        # Load default featured items
        self._load_default_featured_items()

        # Set the layout to the CardWidget
        self.setLayout(layout)

    def _load_default_featured_items(self) -> None:
        """Load default featured items"""
        default_items = [
            {
                "title": "Git",
                "description": "分布式版本控制系统",
                "url": "https://git-scm.com/download/win",
                "icon": "FIF.CODE",
                "category": "开发工具",
                "tags": ["版本控制", "开发必备"],
            },
            {
                "title": "Visual Studio Code",
                "description": "轻量级代码编辑器",
                "url": "https://code.visualstudio.com/download",
                "icon": "FIF.EDIT",
                "category": "开发工具",
                "tags": ["编辑器", "微软", "免费"],
            },
            {
                "title": "Python",
                "description": "简单易学的编程语言",
                "url": "https://www.python.org/downloads/",
                "icon": "FIF.DEVELOPER_TOOLS",
                "category": "编程语言",
                "tags": ["编程", "数据科学", "AI"],
            },
            {
                "title": "Node.js",
                "description": "JavaScript运行时环境",
                "url": "https://nodejs.org/en/download/",
                "icon": "FIF.GLOBE",
                "category": "开发工具",
                "tags": ["JavaScript", "后端", "npm"],
            },
            {
                "title": "Docker Desktop",
                "description": "容器化应用平台",
                "url": "https://www.docker.com/products/docker-desktop",
                "icon": "FIF.CLOUD",
                "category": "开发工具",
                "tags": ["容器", "DevOps"],
            },
            {
                "title": "Google Chrome",
                "description": "快速安全的网络浏览器",
                "url": "https://www.google.com/chrome/",
                "icon": "FIF.GLOBE",
                "category": "浏览器",
                "tags": ["浏览器", "谷歌"],
            },
        ]

        self.set_featured_items(default_items)

    def set_featured_items(self, items: List[Dict[str, Any]]) -> None:
        """Set featured items"""
        self.featured_items = items
        self._refresh_cards()

    def _refresh_cards(self) -> None:
        """Refresh featured cards display"""
        # Clear existing cards
        for i in reversed(range(self.cards_layout.count())):
            child = self.cards_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Add new cards with responsive column count
        max_items = 6

        # Determine responsive column count based on parent width
        parent_width = self.parent().width() if self.parent() else 800
        if parent_width < 600:
            columns = 1  # Mobile: 1 column
        elif parent_width < 900:
            columns = 2  # Tablet: 2 columns
        else:
            columns = 3  # Desktop: 3 columns

        for i, item in enumerate(self.featured_items[:max_items]):
            card = FeaturedDownloadCard(item)
            card.download_requested.connect(self.download_requested)
            card.favorite_toggled.connect(self.favorite_toggled)

            row = i // columns
            col = i % columns
            self.cards_layout.addWidget(card, row, col)

        # Set column stretch for responsive behavior
        for col in range(columns):
            self.cards_layout.setColumnStretch(col, 1)

        # Clear unused columns
        for col in range(columns, 3):
            self.cards_layout.setColumnStretch(col, 0)

    def add_featured_item(self, item: Dict[str, Any]) -> None:
        """Add a new featured item"""
        self.featured_items.append(item)
        self._refresh_cards()

    def remove_featured_item(self, title: str) -> None:
        """Remove a featured item by title"""
        self.featured_items = [
            item for item in self.featured_items if item.get("title") != title
        ]
        self._refresh_cards()

    def update_featured_item(self, title: str, updated_data: Dict[str, Any]) -> None:
        """Update a featured item"""
        for i, item in enumerate(self.featured_items):
            if item.get("title") == title:
                self.featured_items[i].update(updated_data)
                self._refresh_cards()
                break
