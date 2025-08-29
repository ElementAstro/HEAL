"""
Download Header Section Component
Provides prominent search, quick downloads, and status indicator
"""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    ComboBox,
    FluentIcon,
    InfoBadge,
    InfoLevel,
    PrimaryPushButton,
    PushButton,
    SearchLineEdit,
    StrongBodyLabel,
    ToolButton,
)

from ...common.i18n import t
from ...common.logging_config import get_logger


class QuickDownloadSection(CardWidget):
    """Quick download section with popular downloads"""

    download_requested = Signal(str, str)  # name, url

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(
            "quick_download_section", module="QuickDownloadSection"
        )
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize UI"""
        # Set proper CardWidget properties
        self.setMinimumHeight(120)
        self.setBorderRadius(8)

        # Use proper CardWidget layout structure
        layout = QVBoxLayout(self)
        # Standard CardWidget margins
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)  # Standard spacing

        # Title with proper styling
        title_label = StrongBodyLabel("快速下载")
        title_label.setObjectName("quickDownloadTitle")
        layout.addWidget(title_label)

        # Quick download buttons grid with proper container
        buttons_widget = QWidget()
        buttons_widget.setObjectName("quickDownloadButtons")
        buttons_layout = QGridLayout(buttons_widget)
        # Increased spacing for better touch targets
        buttons_layout.setSpacing(12)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        # Popular download buttons
        self.download_buttons = [
            ("Git", "https://git-scm.com/download/win", FluentIcon.CODE),
            ("Python", "https://www.python.org/downloads/",
             FluentIcon.DEVELOPER_TOOLS),
            ("Node.js", "https://nodejs.org/en/download/", FluentIcon.GLOBE),
            ("VS Code", "https://code.visualstudio.com/download", FluentIcon.EDIT),
            (
                "Docker",
                "https://www.docker.com/products/docker-desktop",
                FluentIcon.CLOUD,
            ),
            ("Chrome", "https://www.google.com/chrome/", FluentIcon.GLOBE),
        ]

        # Create buttons in responsive grid layout
        for i, (name, url, icon) in enumerate(self.download_buttons):
            btn = PushButton(name)
            btn.setIcon(icon)
            # Larger minimum size for better usability
            btn.setMinimumSize(120, 40)
            btn.setMaximumSize(160, 40)  # Maximum size to prevent stretching
            btn.setObjectName(f"quickDownloadBtn_{name.lower()}")
            btn.clicked.connect(
                lambda checked, n=name, u=url: self.download_requested.emit(
                    n, u)
            )

            # Responsive grid: 3 columns on desktop, 2 on tablet, 1 on mobile
            row = i // 3
            col = i % 3
            buttons_layout.addWidget(btn, row, col)

        # Set column stretch for responsive behavior
        for col in range(3):
            buttons_layout.setColumnStretch(col, 1)

        layout.addWidget(buttons_widget)

        # Note: CardWidget automatically manages its layout, no need to call setLayout()

    def update_quick_downloads(self, downloads: List[Dict[str, Any]]) -> None:
        """Update quick download buttons from configuration"""
        # This method can be used to dynamically update buttons from config
        pass


class SearchSection(CardWidget):
    """Enhanced search section with category filtering"""

    search_requested = Signal(str, str)  # search_text, category
    category_selected = Signal(str)  # category

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = get_logger("search_section", module="SearchSection")
        self.categories: list[Any] = []
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize UI"""
        # Set proper CardWidget properties
        self.setMinimumHeight(80)
        self.setBorderRadius(8)

        # Use proper CardWidget layout structure
        layout = QHBoxLayout(self)
        # Standard CardWidget margins
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)  # Standard spacing

        # Search icon and label
        search_icon = ToolButton(FluentIcon.SEARCH)
        search_icon.setEnabled(False)
        layout.addWidget(search_icon)

        search_label = BodyLabel("搜索下载:")
        layout.addWidget(search_label)

        # Search input with proper sizing
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("搜索软件、工具或资源...")
        self.search_input.setMinimumHeight(40)  # Larger for better usability
        self.search_input.setObjectName("mainSearchInput")
        self.search_input.searchSignal.connect(self._on_search)
        self.search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_input, 1)

        # Category filter with proper sizing
        category_label = BodyLabel("分类:")
        category_label.setObjectName("categoryLabel")
        layout.addWidget(category_label)

        self.category_combo = ComboBox()
        self.category_combo.setMinimumSize(
            160, 40)  # Larger for better usability
        self.category_combo.setMaximumSize(200, 40)
        self.category_combo.setObjectName("categoryCombo")
        self.category_combo.addItem("全部分类", "all")
        self.category_combo.currentTextChanged.connect(
            self._on_category_changed)
        layout.addWidget(self.category_combo)

        # Search button with proper sizing
        self.search_btn = PrimaryPushButton("搜索")
        self.search_btn.setIcon(FluentIcon.SEARCH)
        self.search_btn.setMinimumSize(100, 40)  # Larger for better usability
        self.search_btn.setObjectName("searchButton")
        self.search_btn.clicked.connect(self._on_search_clicked)
        layout.addWidget(self.search_btn)

        # Note: CardWidget automatically manages its layout, no need to call setLayout()

    def set_categories(self, categories: List[Dict[str, Any]]) -> None:
        """Set available categories"""
        self.categories = categories
        self.category_combo.clear()
        self.category_combo.addItem("全部分类", "all")

        for category in categories:
            title = category.get("title", "")
            category_id = category.get("id", "")
            if title and category_id:
                self.category_combo.addItem(title, category_id)

    def _on_search(self, text: str) -> None:
        """Handle search signal"""
        category = self.category_combo.currentData() or "all"
        self.search_requested.emit(text, category)

    def _on_text_changed(self, text: str) -> None:
        """Handle text change for real-time search"""
        if len(text) >= 2:  # Start searching after 2 characters
            category = self.category_combo.currentData() or "all"
            self.search_requested.emit(text, category)

    def _on_category_changed(self, text: str) -> None:
        """Handle category selection change"""
        category = self.category_combo.currentData() or "all"
        self.category_selected.emit(category)

        # Trigger search with current text if any
        search_text = self.search_input.text()
        if search_text:
            self.search_requested.emit(search_text, category)

    def _on_search_clicked(self) -> None:
        """Handle search button click"""
        search_text = self.search_input.text()
        category = self.category_combo.currentData() or "all"
        self.search_requested.emit(search_text, category)


class DownloadStatusIndicator(CardWidget):
    """Download status indicator showing active downloads"""

    status_clicked = Signal()  # User wants to see download details

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(
            "download_status_indicator", module="DownloadStatusIndicator"
        )
        self.active_count = 0
        self.total_progress = 0
        self.init_ui()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(2000)  # Update every 2 seconds

    def init_ui(self) -> None:
        """Initialize UI"""
        # Set proper CardWidget properties
        self.setMinimumHeight(80)
        self.setBorderRadius(8)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Use proper CardWidget layout structure
        layout = QHBoxLayout(self)
        # Standard CardWidget margins
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)  # Standard spacing

        # Download icon with proper sizing
        self.download_icon = ToolButton(FluentIcon.DOWNLOAD)
        self.download_icon.setEnabled(False)
        self.download_icon.setFixedSize(32, 32)  # Consistent icon size
        self.download_icon.setObjectName("downloadStatusIcon")
        layout.addWidget(self.download_icon)

        # Status info with proper spacing
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)  # Slightly more spacing for readability

        self.status_label = BodyLabel("无活动下载")
        self.status_label.setObjectName("downloadStatusLabel")

        self.progress_label = CaptionLabel("")
        self.progress_label.setObjectName("downloadProgressLabel")

        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.progress_label)

        layout.addLayout(info_layout, 1)

        # Status badge with proper positioning
        self.status_badge = InfoBadge.info("0", self)
        self.status_badge.setVisible(False)
        self.status_badge.setObjectName("downloadStatusBadge")
        layout.addWidget(self.status_badge)

        # Arrow with proper sizing
        arrow_btn = ToolButton(FluentIcon.CHEVRON_RIGHT)
        arrow_btn.setEnabled(False)
        arrow_btn.setFixedSize(24, 24)  # Consistent arrow size
        arrow_btn.setObjectName("downloadStatusArrow")
        layout.addWidget(arrow_btn)

        # Note: CardWidget automatically manages its layout, no need to call setLayout()

    def mousePressEvent(self, event: Any) -> None:
        """Handle click to show download details"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.status_clicked.emit()
        super().mousePressEvent(event)

    def update_status(self) -> None:
        """Update download status (placeholder - should connect to actual download manager)"""
        # This would normally get data from the download manager
        # For now, using placeholder logic
        pass

    def set_download_status(self, active_count: int, total_progress: int = 0) -> None:
        """Set download status"""
        self.active_count = active_count
        self.total_progress = total_progress

        if active_count == 0:
            self.status_label.setText("无活动下载")
            self.progress_label.setText("")
            self.status_badge.setVisible(False)
            self.download_icon.setIcon(FluentIcon.DOWNLOAD)
        else:
            self.status_label.setText(f"{active_count} 个下载进行中")
            if total_progress > 0:
                self.progress_label.setText(f"总进度: {total_progress}%")
            else:
                self.progress_label.setText("正在下载...")

            self.status_badge.setText(str(active_count))
            self.status_badge.setVisible(True)
            self.download_icon.setIcon(FluentIcon.SYNC)


class DownloadHeaderSection(QWidget):
    """Main header section combining search, quick downloads, and status"""

    # Signals
    search_requested = Signal(str, str)  # search_text, category
    category_selected = Signal(str)  # category
    download_requested = Signal(str, str)  # name, url
    status_clicked = Signal()  # User wants to see download details

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(
            "download_header_section", module="DownloadHeaderSection"
        )
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize UI"""
        # Use proper container layout with standard spacing
        layout = QVBoxLayout(self)
        # Bottom margin for section separation
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(16)  # Standard spacing between sections

        # Top row: Search and Status with responsive behavior
        top_row = QHBoxLayout()
        top_row.setSpacing(16)  # Standard spacing

        # Search section (takes most space)
        self.search_section = SearchSection()
        self.search_section.search_requested.connect(self.search_requested)
        self.search_section.category_selected.connect(self.category_selected)
        top_row.addWidget(self.search_section, 2)  # Give more weight to search

        # Status indicator (fixed width but responsive)
        self.status_indicator = DownloadStatusIndicator()
        self.status_indicator.status_clicked.connect(self.status_clicked)
        self.status_indicator.setMinimumWidth(280)  # Minimum width for content
        # Maximum width to prevent stretching
        self.status_indicator.setMaximumWidth(350)
        top_row.addWidget(self.status_indicator, 0)  # Fixed size

        layout.addLayout(top_row)

        # Quick download section
        self.quick_download_section = QuickDownloadSection()
        self.quick_download_section.download_requested.connect(
            self.download_requested)
        layout.addWidget(self.quick_download_section)

    def set_categories(self, categories: List[Dict[str, Any]]) -> None:
        """Set available categories for search filter"""
        self.search_section.set_categories(categories)

    def update_download_status(self, active_count: int, total_progress: int = 0) -> None:
        """Update download status indicator"""
        self.status_indicator.set_download_status(active_count, total_progress)

    def update_quick_downloads(self, downloads: List[Dict[str, Any]]) -> None:
        """Update quick download buttons"""
        self.quick_download_section.update_quick_downloads(downloads)
