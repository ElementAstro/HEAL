"""
Category Grid Widget
Visual category browser for better content discovery
"""

from typing import Dict, List, Optional, Any
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSizePolicy, QFrame
)
from qfluentwidgets import (
    CardWidget, StrongBodyLabel, BodyLabel, CaptionLabel,
    ToolButton, FluentIcon, InfoBadge, InfoLevel,
    HyperlinkButton
)

from app.common.logging_config import get_logger
from app.common.i18n import t


class CategoryCard(CardWidget):
    """Individual category card"""
    
    category_selected = Signal(str, str)  # category_id, category_title
    
    def __init__(self, category_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.category_data = category_data
        self.logger = get_logger('category_card', module='CategoryCard')
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        # Remove fixed size to allow responsive behavior
        self.setMinimumSize(180, 100)
        self.setMaximumSize(240, 140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Use proper layout structure for CardWidget
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Icon and title row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Category icon
        icon_name = self.category_data.get('icon', 'FIF.FOLDER')
        icon = self._resolve_icon(icon_name)
        self.icon_btn = ToolButton(icon)
        self.icon_btn.setFixedSize(32, 32)
        self.icon_btn.setEnabled(False)
        header_layout.addWidget(self.icon_btn)
        
        # Title
        title = self.category_data.get('title', '未知分类')
        self.title_label = StrongBodyLabel(title)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.title_label, 1)
        
        layout.addLayout(header_layout)
        
        # Description
        description = self.category_data.get('description', '')
        if description:
            self.desc_label = BodyLabel(description)
            self.desc_label.setWordWrap(True)
            self.desc_label.setStyleSheet("color: #888; font-size: 11px;")
            self.desc_label.setMaximumHeight(30)
            layout.addWidget(self.desc_label)
        else:
            layout.addStretch()
        
        # Footer with item count and arrow
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)
        
        # Item count
        item_count = len(self.category_data.get('items', []))
        count_text = f"{item_count} 个项目" if item_count > 0 else "暂无项目"
        self.count_label = CaptionLabel(count_text)
        self.count_label.setStyleSheet("color: gray;")
        footer_layout.addWidget(self.count_label, 1)
        
        # Arrow indicator
        arrow_btn = ToolButton(FluentIcon.CHEVRON_RIGHT)
        arrow_btn.setFixedSize(16, 16)
        arrow_btn.setEnabled(False)
        footer_layout.addWidget(arrow_btn)
        
        layout.addLayout(footer_layout)

        # Set the layout to the CardWidget
        self.setLayout(layout)

    def _resolve_icon(self, icon_name: str):
        """Resolve icon from name"""
        if icon_name.startswith('FIF.'):
            return getattr(FluentIcon, icon_name[4:], FluentIcon.FOLDER)
        elif icon_name.startswith('Astro.'):
            try:
                from src.icon.astro import AstroIcon
                return getattr(AstroIcon, icon_name[6:], FluentIcon.FOLDER)
            except ImportError:
                return FluentIcon.FOLDER
        return FluentIcon.FOLDER
        
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.MouseButton.LeftButton:
            category_id = self.category_data.get('id', '')
            category_title = self.category_data.get('title', '')
            self.category_selected.emit(category_id, category_title)
            self.logger.info(f"分类选择: {category_title} ({category_id})")
        super().mousePressEvent(event)
        
    def enterEvent(self, event):
        """Handle mouse enter for hover effect"""
        self.setStyleSheet("""
            CategoryCard {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leave"""
        self.setStyleSheet("")
        super().leaveEvent(event)


class CategoryGridWidget(CardWidget):
    """Category grid widget for visual browsing"""
    
    category_selected = Signal(str, str)  # category_id, category_title
    view_all_categories = Signal()  # User wants to see all categories
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('category_grid_widget', module='CategoryGridWidget')
        self.categories = []
        self.max_visible_categories = 8  # Show max 8 categories in grid
        self.init_ui()
        
    def init_ui(self):
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
        
        title_label = StrongBodyLabel("浏览分类")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        subtitle_label = CaptionLabel("按分类查找所需软件和工具")
        subtitle_label.setStyleSheet("color: gray;")
        title_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(title_layout, 1)
        
        # View all button
        self.view_all_btn = HyperlinkButton("查看全部分类", "")
        self.view_all_btn.clicked.connect(self.view_all_categories)
        header_layout.addWidget(self.view_all_btn)
        
        layout.addLayout(header_layout)
        
        # Category grid container
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(self.grid_widget)
        
        # Load default categories
        self._load_default_categories()

        # Set the layout to the CardWidget
        self.setLayout(layout)

    def _load_default_categories(self):
        """Load default categories"""
        default_categories = [
            {
                'id': 'development',
                'title': '开发工具',
                'description': '编程和开发相关工具',
                'icon': 'FIF.CODE',
                'items': []  # Will be populated from actual data
            },
            {
                'id': 'browsers',
                'title': '浏览器',
                'description': '网络浏览器和相关工具',
                'icon': 'FIF.GLOBE',
                'items': []
            },
            {
                'id': 'multimedia',
                'title': '多媒体',
                'description': '音视频处理和播放工具',
                'icon': 'FIF.MEDIA',
                'items': []
            },
            {
                'id': 'productivity',
                'title': '办公软件',
                'description': '办公和生产力工具',
                'icon': 'FIF.DOCUMENT',
                'items': []
            },
            {
                'id': 'system',
                'title': '系统工具',
                'description': '系统维护和管理工具',
                'icon': 'FIF.SETTING',
                'items': []
            },
            {
                'id': 'security',
                'title': '安全软件',
                'description': '安全防护和隐私工具',
                'icon': 'FIF.SHIELD',
                'items': []
            },
            {
                'id': 'games',
                'title': '游戏娱乐',
                'description': '游戏和娱乐应用',
                'icon': 'FIF.GAME',
                'items': []
            },
            {
                'id': 'education',
                'title': '教育学习',
                'description': '学习和教育相关软件',
                'icon': 'FIF.EDUCATION',
                'items': []
            }
        ]
        
        self.set_categories(default_categories)
        
    def set_categories(self, categories: List[Dict[str, Any]]):
        """Set categories data"""
        self.categories = categories
        self._refresh_grid()
        
    def _refresh_grid(self):
        """Refresh category grid display"""
        # Clear existing cards
        for i in reversed(range(self.grid_layout.count())):
            child = self.grid_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add category cards with responsive column count
        # Determine responsive column count based on parent width
        parent_width = self.parent().width() if self.parent() else 800
        if parent_width < 500:
            columns = 1  # Mobile: 1 column
        elif parent_width < 700:
            columns = 2  # Small tablet: 2 columns
        elif parent_width < 1000:
            columns = 3  # Large tablet: 3 columns
        else:
            columns = 4  # Desktop: 4 columns

        visible_categories = self.categories[:self.max_visible_categories]
        
        for i, category in enumerate(visible_categories):
            card = CategoryCard(category)
            card.category_selected.connect(self.category_selected)
            
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(card, row, col)
            
        # Set column stretch for responsive behavior
        for col in range(columns):
            self.grid_layout.setColumnStretch(col, 1)

        # Clear unused columns
        for col in range(columns, 4):
            self.grid_layout.setColumnStretch(col, 0)
            
    def update_category_counts(self, category_counts: Dict[str, int]):
        """Update category item counts"""
        for category in self.categories:
            category_id = category.get('id', '')
            if category_id in category_counts:
                # Update the items count (this would normally come from actual data)
                category['item_count'] = category_counts[category_id]
                
        self._refresh_grid()
        
    def add_category(self, category: Dict[str, Any]):
        """Add a new category"""
        self.categories.append(category)
        self._refresh_grid()
        
    def remove_category(self, category_id: str):
        """Remove a category"""
        self.categories = [cat for cat in self.categories if cat.get('id') != category_id]
        self._refresh_grid()
        
    def get_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get category data by ID"""
        for category in self.categories:
            if category.get('id') == category_id:
                return category
        return None
        
    def highlight_category(self, category_id: str):
        """Highlight a specific category (for search results)"""
        # This could be implemented to highlight matching categories
        # when user searches or filters
        pass
        
    def set_max_visible_categories(self, max_count: int):
        """Set maximum number of visible categories"""
        self.max_visible_categories = max_count
        self._refresh_grid()


class CategoryDetailView(CardWidget):
    """Detailed view of a specific category"""
    
    back_requested = Signal()  # User wants to go back to grid
    item_selected = Signal(str, Dict)  # item_id, item_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('category_detail_view', module='CategoryDetailView')
        self.current_category = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # Header with back button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # Back button
        self.back_btn = ToolButton(FluentIcon.BACK)
        self.back_btn.setToolTip("返回分类")
        self.back_btn.clicked.connect(self.back_requested)
        header_layout.addWidget(self.back_btn)
        
        # Category title and info
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        self.category_title = StrongBodyLabel("分类详情")
        self.category_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(self.category_title)
        
        self.category_description = CaptionLabel("")
        self.category_description.setStyleSheet("color: gray;")
        title_layout.addWidget(self.category_description)
        
        header_layout.addLayout(title_layout, 1)
        
        layout.addLayout(header_layout)
        
        # Items container (would contain the actual download items)
        self.items_widget = QWidget()
        self.items_layout = QVBoxLayout(self.items_widget)
        layout.addWidget(self.items_widget)
        
    def show_category(self, category_data: Dict[str, Any]):
        """Show details for a specific category"""
        self.current_category = category_data
        
        # Update header
        title = category_data.get('title', '未知分类')
        description = category_data.get('description', '')
        
        self.category_title.setText(title)
        self.category_description.setText(description)
        
        # Clear and populate items
        self._clear_items()
        items = category_data.get('items', [])
        
        if not items:
            # Show empty state
            empty_label = BodyLabel("此分类暂无可用项目")
            empty_label.setStyleSheet("color: gray; text-align: center;")
            self.items_layout.addWidget(empty_label)
        else:
            # Show items (this would integrate with existing card components)
            for item in items:
                # Create item cards here
                pass
                
    def _clear_items(self):
        """Clear all items from the view"""
        for i in reversed(range(self.items_layout.count())):
            child = self.items_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
