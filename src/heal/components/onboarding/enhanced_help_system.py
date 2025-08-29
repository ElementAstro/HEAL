"""
Enhanced Help System for HEAL Onboarding

Provides a comprehensive, interactive help system with contextual assistance,
search capabilities, and seamless integration with the application.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QLineEdit, QListWidget, QListWidgetItem, QSplitter, QTabWidget,
    QScrollArea, QFrame, QGroupBox, QTreeWidget, QTreeWidgetItem,
    QDialog, QDialogButtonBox, QComboBox, QCheckBox, QProgressBar,
    QToolButton, QMenu, QAction, QTextBrowser, QApplication, QMainWindow,
    QDockWidget, QStackedWidget, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QUrl, QSize, QPoint
from PySide6.QtGui import QFont, QIcon, QPixmap, QDesktopServices, QKeySequence, QShortcut

from .documentation_integration import DocumentationIntegration, DocumentationType, DocumentationItem
from .user_state_tracker import UserLevel, UserStateTracker
from ...common.logging_config import get_logger

logger = get_logger(__name__)


class HelpSearchWidget(QWidget):
    """Search widget for help content"""
    
    search_requested = Signal(str, object, object)  # query, doc_type, user_level
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the search UI"""
        layout = QVBoxLayout(self)
        
        # Search input
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search help content...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Filters
        filters_layout = QHBoxLayout()
        
        # Document type filter
        type_label = QLabel("Type:")
        filters_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types", None)
        for doc_type in DocumentationType:
            self.type_combo.addItem(doc_type.value.title(), doc_type)
        filters_layout.addWidget(self.type_combo)
        
        # User level filter
        level_label = QLabel("Level:")
        filters_layout.addWidget(level_label)
        
        self.level_combo = QComboBox()
        self.level_combo.addItem("All Levels", None)
        for level in UserLevel:
            self.level_combo.addItem(level.value.title(), level)
        filters_layout.addWidget(self.level_combo)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
    
    def perform_search(self):
        """Perform search with current parameters"""
        query = self.search_input.text().strip()
        if not query:
            return
        
        doc_type = self.type_combo.currentData()
        user_level = self.level_combo.currentData()
        
        self.search_requested.emit(query, doc_type, user_level)


class HelpContentWidget(QWidget):
    """Widget for displaying help content"""
    
    content_requested = Signal(str)  # doc_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the content display UI"""
        layout = QVBoxLayout(self)
        
        # Content browser
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(False)
        self.content_browser.anchorClicked.connect(self._on_link_clicked)
        layout.addWidget(self.content_browser)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        actions_layout.addWidget(self.back_btn)
        
        actions_layout.addStretch()
        
        self.print_btn = QPushButton("Print")
        self.print_btn.clicked.connect(self.print_content)
        actions_layout.addWidget(self.print_btn)
        
        layout.addLayout(actions_layout)
        
        # History for back navigation
        self.content_history = []
        self.current_content_index = -1
    
    def display_content(self, item: DocumentationItem):
        """Display a documentation item"""
        if not item:
            return
        
        # Add to history
        if (self.current_content_index == -1 or 
            self.content_history[self.current_content_index].doc_id != item.doc_id):
            
            # Remove forward history if we're not at the end
            if self.current_content_index < len(self.content_history) - 1:
                self.content_history = self.content_history[:self.current_content_index + 1]
            
            self.content_history.append(item)
            self.current_content_index = len(self.content_history) - 1
        
        # Update back button
        self.back_btn.setEnabled(self.current_content_index > 0)
        
        # Format and display content
        html_content = self._format_content(item)
        self.content_browser.setHtml(html_content)
    
    def _format_content(self, item: DocumentationItem) -> str:
        """Format documentation item as HTML"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                h3 {{ color: #7f8c8d; }}
                .meta {{ background-color: #ecf0f1; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .tags {{ margin-top: 10px; }}
                .tag {{ background-color: #3498db; color: white; padding: 2px 8px; border-radius: 3px; margin-right: 5px; font-size: 12px; }}
                .content {{ line-height: 1.6; }}
                code {{ background-color: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
                pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <h1>{item.title}</h1>
            
            <div class="meta">
                <strong>Type:</strong> {item.doc_type.value.title()}<br>
                <strong>User Levels:</strong> {', '.join([level.value.title() for level in item.user_levels]) if item.user_levels else 'All'}<br>
                <strong>Prerequisites:</strong> {', '.join(item.prerequisites) if item.prerequisites else 'None'}
            </div>
            
            <div class="content">
                {self._markdown_to_html(item.content)}
            </div>
            
            <div class="tags">
                <strong>Tags:</strong>
                {' '.join([f'<span class="tag">{tag}</span>' for tag in item.tags])}
            </div>
        </body>
        </html>
        """
        return html
    
    def _markdown_to_html(self, content: str) -> str:
        """Convert simple markdown to HTML"""
        # Simple markdown conversion
        content = content.replace('\n\n', '</p><p>')
        content = content.replace('\n', '<br>')
        
        # Bold text
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        
        # Italic text
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        
        # Code blocks
        content = re.sub(r'```(.*?)```', r'<pre>\1</pre>', content, flags=re.DOTALL)
        
        # Inline code
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
        
        # Headers
        content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        
        return f'<p>{content}</p>'
    
    def go_back(self):
        """Go back to previous content"""
        if self.current_content_index > 0:
            self.current_content_index -= 1
            item = self.content_history[self.current_content_index]
            
            # Display without adding to history
            html_content = self._format_content(item)
            self.content_browser.setHtml(html_content)
            
            # Update back button
            self.back_btn.setEnabled(self.current_content_index > 0)
    
    def print_content(self):
        """Print current content"""
        # This would integrate with the system's print dialog
        pass
    
    def _on_link_clicked(self, url: QUrl):
        """Handle link clicks"""
        url_str = url.toString()
        
        if url_str.startswith("doc:"):
            # Internal documentation link
            doc_id = url_str[4:]
            self.content_requested.emit(doc_id)
        else:
            # External link
            QDesktopServices.openUrl(url)


class HelpResultsWidget(QWidget):
    """Widget for displaying search results"""
    
    item_selected = Signal(object)  # DocumentationItem
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the results UI"""
        layout = QVBoxLayout(self)
        
        # Results header
        self.results_header = QLabel("Search Results")
        self.results_header.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(self.results_header)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.results_list)
    
    def display_results(self, results: List[DocumentationItem], query: str = ""):
        """Display search results"""
        self.results_list.clear()
        
        if not results:
            self.results_header.setText("No results found")
            return
        
        self.results_header.setText(f"Found {len(results)} result(s)" + (f" for '{query}'" if query else ""))
        
        for item in results:
            list_item = QListWidgetItem()
            
            # Create result display text
            result_text = f"{item.title}\n"
            result_text += f"Type: {item.doc_type.value.title()}"
            
            if item.user_levels:
                levels = ", ".join([level.value.title() for level in item.user_levels])
                result_text += f" | Levels: {levels}"
            
            if item.tags:
                result_text += f"\nTags: {', '.join(item.tags[:5])}"  # Show first 5 tags
            
            list_item.setText(result_text)
            list_item.setData(Qt.UserRole, item)
            
            self.results_list.addItem(list_item)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle item click"""
        doc_item = item.data(Qt.UserRole)
        if doc_item:
            self.item_selected.emit(doc_item)


class EnhancedHelpSystem(QMainWindow):
    """Main enhanced help system window"""
    
    def __init__(self, documentation_integration: DocumentationIntegration,
                 user_tracker: Optional[UserStateTracker] = None, parent=None):
        super().__init__(parent)
        
        self.documentation_integration = documentation_integration
        self.user_tracker = user_tracker
        
        self.setup_ui()
        self.setup_connections()
        self.load_initial_content()
    
    def setup_ui(self):
        """Setup the help system UI"""
        self.setWindowTitle("HEAL Help System")
        self.setMinimumSize(800, 600)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel (search and results)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Search widget
        self.search_widget = HelpSearchWidget()
        left_layout.addWidget(self.search_widget)
        
        # Results widget
        self.results_widget = HelpResultsWidget()
        left_layout.addWidget(self.results_widget)
        
        splitter.addWidget(left_panel)
        
        # Right panel (content display)
        self.content_widget = HelpContentWidget()
        splitter.addWidget(self.content_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.statusBar().showMessage("Ready")
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        print_action = QAction("Print", self)
        print_action.setShortcut(QKeySequence.Print)
        print_action.triggered.connect(self.content_widget.print_content)
        file_menu.addAction(print_action)
        
        file_menu.addSeparator()
        
        close_action = QAction("Close", self)
        close_action.setShortcut(QKeySequence.Close)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.triggered.connect(self.refresh_content)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create toolbar"""
        toolbar = self.addToolBar("Main")
        
        # Back button
        back_action = QAction("← Back", self)
        back_action.triggered.connect(self.content_widget.go_back)
        toolbar.addAction(back_action)
        
        toolbar.addSeparator()
        
        # Home button
        home_action = QAction("🏠 Home", self)
        home_action.triggered.connect(self.show_home)
        toolbar.addAction(home_action)
        
        # Refresh button
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.triggered.connect(self.refresh_content)
        toolbar.addAction(refresh_action)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.search_widget.search_requested.connect(self.perform_search)
        self.results_widget.item_selected.connect(self.display_content)
        self.content_widget.content_requested.connect(self.load_content_by_id)
    
    def load_initial_content(self):
        """Load initial help content"""
        # Show getting started content by default
        try:
            getting_started = self.documentation_integration.get_documentation_by_tags(["getting_started"])
            if getting_started:
                self.display_content(getting_started[0])
            else:
                # Show welcome message
                self.show_welcome()
        except:
            # Show welcome message if documentation loading fails
            self.show_welcome()
    
    def show_welcome(self):
        """Show welcome message"""
        welcome_html = """
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h1>Welcome to HEAL Help System</h1>
            <p>This comprehensive help system provides:</p>
            <ul>
                <li><strong>Contextual Help:</strong> Get help relevant to what you're doing</li>
                <li><strong>Search:</strong> Find specific information quickly</li>
                <li><strong>Tutorials:</strong> Step-by-step guides for learning</li>
                <li><strong>Reference:</strong> Detailed technical information</li>
                <li><strong>Troubleshooting:</strong> Solutions to common problems</li>
            </ul>
            
            <h2>Getting Started</h2>
            <p>Use the search box on the left to find help topics, or browse by category.</p>
            
            <h2>Tips</h2>
            <ul>
                <li>Use keywords to search for specific topics</li>
                <li>Filter by document type and user level</li>
                <li>Click on links to navigate between related topics</li>
                <li>Use the back button to return to previous content</li>
            </ul>
        </body>
        </html>
        """
        self.content_widget.content_browser.setHtml(welcome_html)
    
    def perform_search(self, query: str, doc_type: DocumentationType, user_level: UserLevel):
        """Perform search and display results"""
        try:
            results = self.documentation_manager.search_documentation(query, doc_type, user_level)
            self.results_widget.display_results(results, query)
            
            self.statusBar().showMessage(f"Found {len(results)} result(s) for '{query}'")
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.statusBar().showMessage("Search failed")
    
    def display_content(self, item: DocumentationItem):
        """Display documentation content"""
        try:
            self.content_widget.display_content(item)
            self.statusBar().showMessage(f"Displaying: {item.title}")
            
        except Exception as e:
            logger.error(f"Failed to display content: {e}")
            self.statusBar().showMessage("Failed to display content")
    
    def load_content_by_id(self, doc_id: str):
        """Load content by documentation ID"""
        item = self.documentation_manager.get_documentation_item(doc_id)
        if item:
            self.display_content(item)
        else:
            self.statusBar().showMessage(f"Content not found: {doc_id}")
    
    def show_home(self):
        """Show home/welcome content"""
        self.show_welcome()
        self.results_widget.results_list.clear()
        self.results_widget.results_header.setText("Search Results")
        self.statusBar().showMessage("Home")
    
    def refresh_content(self):
        """Refresh help content"""
        try:
            # Reload documentation
            self.documentation_manager.load_documentation()
            self.statusBar().showMessage("Content refreshed")
            
        except Exception as e:
            logger.error(f"Failed to refresh content: {e}")
            self.statusBar().showMessage("Failed to refresh content")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>HEAL Help System</h2>
        <p>Version 1.0.0</p>
        <p>Comprehensive help and documentation system for HEAL.</p>
        <p>© 2024 HEAL Team</p>
        """
        
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("About HEAL Help")
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_text)
        msg.exec()


def show_help_system(documentation_integration: DocumentationIntegration,
                    user_tracker: Optional[UserStateTracker] = None,
                    parent=None) -> EnhancedHelpSystem:
    """Show the enhanced help system"""
    help_system = EnhancedHelpSystem(documentation_integration, user_tracker, parent)
    help_system.show()
    return help_system
