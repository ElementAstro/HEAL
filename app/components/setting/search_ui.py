"""
Settings Search UI Components
Modern search interface with filters, suggestions, and results display
"""

from typing import List, Dict, Any, Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QScrollArea, QFrame,
    QCompleter, QListWidget, QListWidgetItem, QButtonGroup,
    QToolButton, QMenu, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QStringListModel, QSize
from PySide6.QtGui import QIcon, QFont, QPalette, QPixmap, QPainter, QAction
from qfluentwidgets import (
    SearchLineEdit, PushButton, ToolButton, ComboBox, CheckBox,
    FluentIcon, CardWidget, BodyLabel, CaptionLabel, IconWidget,
    TransparentToolButton, RoundMenu, Action
)

from app.components.setting.search_engine import (
    SettingsSearchEngine, SearchResult, SearchFilter, SearchType, FilterType
)
from app.common.logging_config import get_logger


class SearchSuggestionWidget(QWidget):
    """Widget for displaying search suggestions"""
    
    suggestion_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('search_suggestions', module='SearchSuggestionWidget')
        self.suggestions = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the suggestion UI"""
        self.setFixedHeight(200)
        self.setStyleSheet("""
            SearchSuggestionWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
            }
            QListWidget::item {
                padding: 6px 12px;
                border-radius: 4px;
                margin: 1px 0;
            }
            QListWidget::item:hover {
                background-color: rgba(0, 120, 212, 0.1);
            }
            QListWidget::item:selected {
                background-color: rgba(0, 120, 212, 0.2);
            }
        """)
        
        self.suggestions_list.itemClicked.connect(self._on_suggestion_clicked)
        layout.addWidget(self.suggestions_list)
    
    def update_suggestions(self, suggestions: List[str]):
        """Update the suggestions list"""
        self.suggestions = suggestions
        self.suggestions_list.clear()
        
        for suggestion in suggestions:
            item = QListWidgetItem(suggestion)
            item.setIcon(QIcon())  # Add search icon if available
            self.suggestions_list.addItem(item)
        
        self.setVisible(len(suggestions) > 0)
    
    def _on_suggestion_clicked(self, item: QListWidgetItem):
        """Handle suggestion click"""
        self.suggestion_selected.emit(item.text())
        self.hide()


class SearchFilterWidget(CardWidget):
    """Widget for search filters"""
    
    filters_changed = Signal(list)  # List[SearchFilter]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('search_filters', module='SearchFilterWidget')
        self.filters: List[SearchFilter] = []
        self.filter_options: Dict[str, List[str]] = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the filter UI"""
        self.setFixedHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Header
        header_layout = QHBoxLayout()
        
        filter_label = BodyLabel("Filters")
        filter_label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        header_layout.addWidget(filter_label)
        
        # Clear filters button
        self.clear_button = TransparentToolButton(FluentIcon.DELETE)
        self.clear_button.setToolTip("Clear all filters")
        self.clear_button.clicked.connect(self.clear_filters)
        header_layout.addWidget(self.clear_button)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Filter controls
        controls_layout = QHBoxLayout()
        
        # Category filter
        self.category_combo = ComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.currentTextChanged.connect(self._on_filter_changed)
        controls_layout.addWidget(QLabel("Category:"))
        controls_layout.addWidget(self.category_combo)
        
        # Type filter
        self.type_combo = ComboBox()
        self.type_combo.addItem("All Types")
        self.type_combo.currentTextChanged.connect(self._on_filter_changed)
        controls_layout.addWidget(QLabel("Type:"))
        controls_layout.addWidget(self.type_combo)
        
        # Recently changed filter
        self.recent_combo = ComboBox()
        self.recent_combo.addItems(["Any time", "Last hour", "Last day", "Last week"])
        self.recent_combo.currentTextChanged.connect(self._on_filter_changed)
        controls_layout.addWidget(QLabel("Changed:"))
        controls_layout.addWidget(self.recent_combo)
        
        # Favorites filter
        self.favorites_checkbox = CheckBox("Favorites only")
        self.favorites_checkbox.stateChanged.connect(self._on_filter_changed)
        controls_layout.addWidget(self.favorites_checkbox)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
    
    def update_filter_options(self, options: Dict[str, List[str]]):
        """Update available filter options"""
        self.filter_options = options
        
        # Update category combo
        self.category_combo.clear()
        self.category_combo.addItem("All Categories")
        self.category_combo.addItems(options.get('categories', []))
        
        # Update type combo
        self.type_combo.clear()
        self.type_combo.addItem("All Types")
        self.type_combo.addItems(options.get('types', []))
    
    def _on_filter_changed(self):
        """Handle filter changes"""
        self.filters.clear()
        
        # Category filter
        category = self.category_combo.currentText()
        if category != "All Categories":
            self.filters.append(SearchFilter(
                filter_type=FilterType.CATEGORY,
                value=category
            ))
        
        # Type filter
        setting_type = self.type_combo.currentText()
        if setting_type != "All Types":
            self.filters.append(SearchFilter(
                filter_type=FilterType.TYPE,
                value=setting_type
            ))
        
        # Recently changed filter
        recent = self.recent_combo.currentText()
        if recent != "Any time":
            seconds_map = {
                "Last hour": 3600,
                "Last day": 86400,
                "Last week": 604800
            }
            if recent in seconds_map:
                self.filters.append(SearchFilter(
                    filter_type=FilterType.RECENTLY_CHANGED,
                    value=seconds_map[recent]
                ))
        
        # Favorites filter
        if self.favorites_checkbox.isChecked():
            self.filters.append(SearchFilter(
                filter_type=FilterType.FAVORITES,
                value=True
            ))
        
        self.filters_changed.emit(self.filters)
    
    def clear_filters(self):
        """Clear all filters"""
        self.category_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.recent_combo.setCurrentIndex(0)
        self.favorites_checkbox.setChecked(False)
        self.filters.clear()
        self.filters_changed.emit(self.filters)


class SearchResultWidget(CardWidget):
    """Widget for displaying a single search result"""
    
    result_clicked = Signal(object)  # SearchResult
    
    def __init__(self, result: SearchResult, parent=None):
        super().__init__(parent)
        self.result = result
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the result UI"""
        self.setFixedHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Icon based on setting type
        icon_widget = IconWidget(self._get_type_icon())
        icon_widget.setFixedSize(32, 32)
        layout.addWidget(icon_widget)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Title with highlighting
        title_label = BodyLabel(self.result.item.title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        content_layout.addWidget(title_label)
        
        # Description
        desc_text = self.result.item.description
        if len(desc_text) > 100:
            desc_text = desc_text[:97] + "..."
        
        desc_label = CaptionLabel(desc_text)
        desc_label.setStyleSheet("color: #605e5c;")
        content_layout.addWidget(desc_label)
        
        layout.addLayout(content_layout)
        
        # Score and match info
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        # Category badge
        category_label = CaptionLabel(self.result.item.category)
        category_label.setStyleSheet("""
            background-color: rgba(0, 120, 212, 0.1);
            color: #0078d4;
            padding: 2px 8px;
            border-radius: 10px;
        """)
        info_layout.addWidget(category_label)
        
        # Match score (for debugging)
        if hasattr(self.result, 'score'):
            score_label = CaptionLabel(f"Score: {self.result.score:.2f}")
            score_label.setStyleSheet("color: #999;")
            info_layout.addWidget(score_label)
        
        layout.addLayout(info_layout)
    
    def _get_type_icon(self) -> FluentIcon:
        """Get icon based on setting type"""
        type_icons = {
            'appearance': FluentIcon.PALETTE,
            'behavior': FluentIcon.TILES,
            'network': FluentIcon.CERTIFICATE,
            'system': FluentIcon.SETTING,
            'switch': FluentIcon.TOGGLE_LEFT,
            'combo': FluentIcon.MENU,
            'button': FluentIcon.PLAY,
            'text': FluentIcon.EDIT
        }
        
        setting_type = self.result.item.setting_type.lower()
        return type_icons.get(setting_type, FluentIcon.SETTING)
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.result_clicked.emit(self.result)
        super().mousePressEvent(event)


class SearchResultsWidget(QScrollArea):
    """Widget for displaying search results"""
    
    result_selected = Signal(object)  # SearchResult
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('search_results', module='SearchResultsWidget')
        self.results: List[SearchResult] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the results UI"""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)
        
        # No results label
        self.no_results_label = BodyLabel("No settings found matching your search.")
        self.no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_results_label.setStyleSheet("color: #999; padding: 40px;")
        self.no_results_label.hide()
        self.content_layout.addWidget(self.no_results_label)
        
        # Results info
        self.results_info_label = CaptionLabel("")
        self.results_info_label.setStyleSheet("color: #666; padding: 8px 16px;")
        self.content_layout.addWidget(self.results_info_label)
        
        self.content_layout.addStretch()
        self.setWidget(self.content_widget)
    
    def update_results(self, results: List[SearchResult], query: str = ""):
        """Update the search results display"""
        self.results = results
        
        # Clear existing results
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), SearchResultWidget):
                item.widget().deleteLater()
        
        if not results:
            self.no_results_label.show()
            self.results_info_label.hide()
            if query:
                self.no_results_label.setText(f"No settings found for '{query}'")
            else:
                self.no_results_label.setText("No settings found matching your filters.")
        else:
            self.no_results_label.hide()
            self.results_info_label.show()
            
            # Update info label
            info_text = f"Found {len(results)} setting"
            if len(results) != 1:
                info_text += "s"
            if query:
                info_text += f" for '{query}'"
            self.results_info_label.setText(info_text)
            
            # Add result widgets
            for result in results:
                result_widget = SearchResultWidget(result)
                result_widget.result_clicked.connect(self.result_selected)
                self.content_layout.insertWidget(
                    self.content_layout.count() - 1,  # Before stretch
                    result_widget
                )
        
        self.logger.debug(f"Updated results display with {len(results)} results")


class SettingsSearchWidget(QWidget):
    """Main search widget combining all search components"""
    
    setting_selected = Signal(object)  # SettingItem
    search_mode_changed = Signal(bool)  # True when search is active
    
    def __init__(self, search_engine: SettingsSearchEngine, parent=None):
        super().__init__(parent)
        self.search_engine = search_engine
        self.logger = get_logger('settings_search_widget', module='SettingsSearchWidget')
        self.is_search_active = False
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the main search UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Search bar container
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("Search settings...")
        self.search_input.setFixedHeight(40)
        search_layout.addWidget(self.search_input)
        
        # Search type button
        self.search_type_button = ToolButton()
        self.search_type_button.setIcon(FluentIcon.SEARCH)
        self.search_type_button.setToolTip("Search options")
        self.setup_search_type_menu()
        search_layout.addWidget(self.search_type_button)
        
        # Clear search button
        self.clear_button = ToolButton()
        self.clear_button.setIcon(FluentIcon.CLOSE)
        self.clear_button.setToolTip("Clear search")
        self.clear_button.clicked.connect(self.clear_search)
        self.clear_button.hide()
        search_layout.addWidget(self.clear_button)
        
        layout.addWidget(search_container)
        
        # Suggestions widget (initially hidden)
        self.suggestions_widget = SearchSuggestionWidget()
        self.suggestions_widget.hide()
        layout.addWidget(self.suggestions_widget)
        
        # Filter widget
        self.filter_widget = SearchFilterWidget()
        self.filter_widget.hide()
        layout.addWidget(self.filter_widget)
        
        # Results widget
        self.results_widget = SearchResultsWidget()
        self.results_widget.hide()
        layout.addWidget(self.results_widget)
    
    def setup_search_type_menu(self):
        """Setup the search type menu"""
        menu = RoundMenu(parent=self)
        # Note: setAnimationType is not available in current qfluentwidgets version
        
        # Search types
        fuzzy_action = Action(FluentIcon.SEARCH, "Fuzzy Search")
        fuzzy_action.setCheckable(True)
        fuzzy_action.setChecked(True)
        fuzzy_action.triggered.connect(lambda: self.set_search_type(SearchType.FUZZY))
        
        exact_action = Action(FluentIcon.SEARCH, "Exact Match")
        exact_action.setCheckable(True)
        exact_action.triggered.connect(lambda: self.set_search_type(SearchType.EXACT))
        
        keyword_action = Action(FluentIcon.TAG, "Keyword Search")
        keyword_action.setCheckable(True)
        keyword_action.triggered.connect(lambda: self.set_search_type(SearchType.KEYWORD))
        
        regex_action = Action(FluentIcon.CODE, "Regex Search")
        regex_action.setCheckable(True)
        regex_action.triggered.connect(lambda: self.set_search_type(SearchType.REGEX))
        
        menu.addActions([fuzzy_action, exact_action, keyword_action, regex_action])
        
        # Toggle filters action
        menu.addSeparator()
        filters_action = Action(FluentIcon.FILTER, "Show Filters")
        filters_action.setCheckable(True)
        filters_action.triggered.connect(self.toggle_filters)
        menu.addAction(filters_action)
        
        self.search_type_button.setMenu(menu)
        self.current_search_type = SearchType.FUZZY
    
    def connect_signals(self):
        """Connect all signals"""
        # Search input
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.perform_search)
        
        # Search engine
        self.search_engine.search_completed.connect(self.on_search_completed)
        
        # Suggestions
        self.suggestions_widget.suggestion_selected.connect(self.on_suggestion_selected)
        
        # Filters
        self.filter_widget.filters_changed.connect(self.on_filters_changed)
        
        # Results
        self.results_widget.result_selected.connect(self.on_result_selected)
    
    def on_search_text_changed(self, text: str):
        """Handle search text changes"""
        if not text.strip():
            self.clear_search()
            return
        
        # Show/hide clear button
        self.clear_button.setVisible(bool(text.strip()))
        
        # Get suggestions
        suggestions = self.search_engine.get_suggestions(text, limit=8)
        self.suggestions_widget.update_suggestions(suggestions)
        
        # Perform real-time search
        filters = self.filter_widget.filters if self.filter_widget.isVisible() else []
        self.search_engine.search_realtime(text, filters, delay_ms=300)
    
    def perform_search(self):
        """Perform immediate search"""
        query = self.search_input.text().strip()
        if not query:
            return
        
        self.suggestions_widget.hide()
        filters = self.filter_widget.filters if self.filter_widget.isVisible() else []
        self.search_engine.search(query, filters, self.current_search_type)
    
    def on_search_completed(self, results: List[SearchResult]):
        """Handle search completion"""
        query = self.search_input.text().strip()
        self.results_widget.update_results(results, query)
        
        # Show/hide results
        if results or query:
            self.results_widget.show()
            self.is_search_active = True
        else:
            self.results_widget.hide()
            self.is_search_active = False
        
        self.search_mode_changed.emit(self.is_search_active)
        self.suggestions_widget.hide()
    
    def on_suggestion_selected(self, suggestion: str):
        """Handle suggestion selection"""
        self.search_input.setText(suggestion)
        self.perform_search()
    
    def on_filters_changed(self, filters: List[SearchFilter]):
        """Handle filter changes"""
        query = self.search_input.text().strip()
        if query or filters:
            self.search_engine.search(query, filters, self.current_search_type)
    
    def on_result_selected(self, result: SearchResult):
        """Handle result selection"""
        self.setting_selected.emit(result.item)
        self.logger.info(f"Selected setting: {result.item.key}")
    
    def set_search_type(self, search_type: SearchType):
        """Set the search type"""
        self.current_search_type = search_type
        query = self.search_input.text().strip()
        if query:
            self.perform_search()
    
    def toggle_filters(self):
        """Toggle filter visibility"""
        if self.filter_widget.isVisible():
            self.filter_widget.hide()
        else:
            # Update filter options from search engine
            options = self.search_engine.get_filter_options()
            self.filter_widget.update_filter_options(options)
            self.filter_widget.show()
    
    def clear_search(self):
        """Clear search and return to normal view"""
        self.search_input.clear()
        self.suggestions_widget.hide()
        self.results_widget.hide()
        self.clear_button.hide()
        self.is_search_active = False
        self.search_mode_changed.emit(False)
    
    def focus_search(self):
        """Focus the search input"""
        self.search_input.setFocus()
        self.search_input.selectAll()
