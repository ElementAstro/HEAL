"""
Download Header Section Component
Provides prominent search, quick downloads, and status indicator
"""

from typing import Dict, List, Optional, Any
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSizePolicy, QSpacerItem
)
from qfluentwidgets import (
    CardWidget, SearchLineEdit, ComboBox, PushButton, ToolButton,
    FluentIcon, StrongBodyLabel, BodyLabel, CaptionLabel,
    InfoBadge, InfoLevel, PrimaryPushButton
)

from app.common.logging_config import get_logger
from app.common.i18n import t


class QuickDownloadSection(CardWidget):
    """Quick download section with popular downloads"""
    
    download_requested = Signal(str, str)  # name, url
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('quick_download_section', module='QuickDownloadSection')
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        # Remove fixed height to allow responsive behavior
        self.setMinimumHeight(100)

        # Use CardWidget's built-in layout structure
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title
        title_label = StrongBodyLabel("快速下载")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # Quick download buttons grid
        buttons_widget = QWidget()
        buttons_layout = QGridLayout(buttons_widget)
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        # Popular download buttons
        self.download_buttons = [
            ("Git", "https://git-scm.com/download/win", FluentIcon.CODE),
            ("Python", "https://www.python.org/downloads/", FluentIcon.DEVELOPER_TOOLS),
            ("Node.js", "https://nodejs.org/en/download/", FluentIcon.GLOBE),
            ("VS Code", "https://code.visualstudio.com/download", FluentIcon.EDIT),
            ("Docker", "https://www.docker.com/products/docker-desktop", FluentIcon.CLOUD),
            ("Chrome", "https://www.google.com/chrome/", FluentIcon.GLOBE)
        ]

        # Create buttons in grid layout (3 columns)
        for i, (name, url, icon) in enumerate(self.download_buttons):
            btn = PushButton(name)
            btn.setIcon(icon)
            btn.setFixedSize(100, 36)
            btn.clicked.connect(lambda checked, n=name, u=url: self.download_requested.emit(n, u))

            row = i // 3
            col = i % 3
            buttons_layout.addWidget(btn, row, col)

        layout.addWidget(buttons_widget)

        # Set the layout to the CardWidget
        self.setLayout(layout)
        
    def update_quick_downloads(self, downloads: List[Dict[str, Any]]):
        """Update quick download buttons from configuration"""
        # This method can be used to dynamically update buttons from config
        pass


class SearchSection(CardWidget):
    """Enhanced search section with category filtering"""
    
    search_requested = Signal(str, str)  # search_text, category
    category_selected = Signal(str)  # category
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('search_section', module='SearchSection')
        self.categories = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        # Remove fixed height to allow responsive behavior
        self.setMinimumHeight(60)

        # Use proper layout structure
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Search icon and label
        search_icon = ToolButton(FluentIcon.SEARCH)
        search_icon.setEnabled(False)
        layout.addWidget(search_icon)

        search_label = BodyLabel("搜索下载:")
        layout.addWidget(search_label)

        # Search input
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("搜索软件、工具或资源...")
        self.search_input.setFixedHeight(36)
        self.search_input.searchSignal.connect(self._on_search)
        self.search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_input, 1)

        # Category filter
        category_label = BodyLabel("分类:")
        layout.addWidget(category_label)

        self.category_combo = ComboBox()
        self.category_combo.setFixedSize(150, 36)
        self.category_combo.addItem("全部分类", "all")
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        layout.addWidget(self.category_combo)

        # Search button
        self.search_btn = PrimaryPushButton("搜索")
        self.search_btn.setIcon(FluentIcon.SEARCH)
        self.search_btn.setFixedSize(80, 36)
        self.search_btn.clicked.connect(self._on_search_clicked)
        layout.addWidget(self.search_btn)

        # Set the layout to the CardWidget
        self.setLayout(layout)
        
    def set_categories(self, categories: List[Dict[str, Any]]):
        """Set available categories"""
        self.categories = categories
        self.category_combo.clear()
        self.category_combo.addItem("全部分类", "all")
        
        for category in categories:
            title = category.get('title', '')
            category_id = category.get('id', '')
            if title and category_id:
                self.category_combo.addItem(title, category_id)
                
    def _on_search(self, text: str):
        """Handle search signal"""
        category = self.category_combo.currentData() or "all"
        self.search_requested.emit(text, category)
        
    def _on_text_changed(self, text: str):
        """Handle text change for real-time search"""
        if len(text) >= 2:  # Start searching after 2 characters
            category = self.category_combo.currentData() or "all"
            self.search_requested.emit(text, category)
            
    def _on_category_changed(self, text: str):
        """Handle category selection change"""
        category = self.category_combo.currentData() or "all"
        self.category_selected.emit(category)
        
        # Trigger search with current text if any
        search_text = self.search_input.text()
        if search_text:
            self.search_requested.emit(search_text, category)
            
    def _on_search_clicked(self):
        """Handle search button click"""
        search_text = self.search_input.text()
        category = self.category_combo.currentData() or "all"
        self.search_requested.emit(search_text, category)


class DownloadStatusIndicator(CardWidget):
    """Download status indicator showing active downloads"""
    
    status_clicked = Signal()  # User wants to see download details
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('download_status_indicator', module='DownloadStatusIndicator')
        self.active_count = 0
        self.total_progress = 0
        self.init_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(2000)  # Update every 2 seconds
        
    def init_ui(self):
        """Initialize UI"""
        # Remove fixed height to allow responsive behavior
        self.setMinimumHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Use proper layout structure
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Download icon
        self.download_icon = ToolButton(FluentIcon.DOWNLOAD)
        self.download_icon.setEnabled(False)
        layout.addWidget(self.download_icon)
        
        # Status info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.status_label = BodyLabel("无活动下载")
        self.progress_label = CaptionLabel("")
        self.progress_label.setStyleSheet("color: gray;")
        
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.progress_label)
        
        layout.addLayout(info_layout, 1)
        
        # Status badge
        self.status_badge = InfoBadge.info("0", self)
        self.status_badge.setVisible(False)
        layout.addWidget(self.status_badge)
        
        # Arrow
        arrow_btn = ToolButton(FluentIcon.CHEVRON_RIGHT)
        arrow_btn.setEnabled(False)
        layout.addWidget(arrow_btn)

        # Set the layout to the CardWidget
        self.setLayout(layout)
        
    def mousePressEvent(self, event):
        """Handle click to show download details"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.status_clicked.emit()
        super().mousePressEvent(event)
        
    def update_status(self):
        """Update download status (placeholder - should connect to actual download manager)"""
        # This would normally get data from the download manager
        # For now, using placeholder logic
        pass
        
    def set_download_status(self, active_count: int, total_progress: int = 0):
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('download_header_section', module='DownloadHeaderSection')
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(12)
        
        # Top row: Search and Status
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        
        # Search section
        self.search_section = SearchSection()
        self.search_section.search_requested.connect(self.search_requested)
        self.search_section.category_selected.connect(self.category_selected)
        top_row.addWidget(self.search_section, 1)
        
        # Status indicator
        self.status_indicator = DownloadStatusIndicator()
        self.status_indicator.status_clicked.connect(self.status_clicked)
        self.status_indicator.setFixedWidth(250)
        top_row.addWidget(self.status_indicator)
        
        layout.addLayout(top_row)
        
        # Quick download section
        self.quick_download_section = QuickDownloadSection()
        self.quick_download_section.download_requested.connect(self.download_requested)
        layout.addWidget(self.quick_download_section)
        
    def set_categories(self, categories: List[Dict[str, Any]]):
        """Set available categories for search filter"""
        self.search_section.set_categories(categories)
        
    def update_download_status(self, active_count: int, total_progress: int = 0):
        """Update download status indicator"""
        self.status_indicator.set_download_status(active_count, total_progress)
        
    def update_quick_downloads(self, downloads: List[Dict[str, Any]]):
        """Update quick download buttons"""
        self.quick_download_section.update_quick_downloads(downloads)
