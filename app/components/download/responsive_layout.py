"""
Responsive Layout Manager for Download Interface
Handles responsive behavior and mobile-friendly layouts
"""

from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, Signal, QTimer, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSizePolicy, QSplitter, QStackedWidget
)
from PySide6.QtCore import Qt

from app.common.logging_config import get_logger


class ResponsiveLayoutManager(QObject):
    """Manages responsive layout behavior"""
    
    # Signals
    layout_changed = Signal(str)  # layout_mode: "desktop", "tablet", "mobile"
    sidebar_toggled = Signal(bool)  # is_visible
    
    # Breakpoints (in pixels)
    MOBILE_BREAKPOINT = 768
    TABLET_BREAKPOINT = 1024
    DESKTOP_BREAKPOINT = 1200
    
    def __init__(self, parent_widget: QWidget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger('responsive_layout_manager', module='ResponsiveLayoutManager')
        
        # Current state
        self.current_mode = "desktop"
        self.sidebar_visible = True
        self.window_size = QSize(1200, 800)
        
        # Components
        self.main_splitter: Optional[QSplitter] = None
        self.sidebar_widget: Optional[QWidget] = None
        self.main_content: Optional[QWidget] = None
        
        # Responsive timer to debounce resize events
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._handle_resize)
        
    def set_components(self, main_splitter: QSplitter, sidebar: QWidget, main_content: QWidget):
        """Set the main components to manage"""
        self.main_splitter = main_splitter
        self.sidebar_widget = sidebar
        self.main_content = main_content
        
        # Connect to parent widget resize events
        if self.parent_widget:
            self.parent_widget.resizeEvent = self._on_parent_resize
            
    def _on_parent_resize(self, event):
        """Handle parent widget resize"""
        self.window_size = event.size()
        # Debounce resize events
        self.resize_timer.start(100)
        
    def _handle_resize(self):
        """Handle debounced resize event"""
        width = self.window_size.width()
        new_mode = self._determine_layout_mode(width)
        
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self._apply_layout_mode(new_mode)
            self.layout_changed.emit(new_mode)
            self.logger.info(f"Layout mode changed to: {new_mode} (width: {width}px)")
            
    def _determine_layout_mode(self, width: int) -> str:
        """Determine layout mode based on width"""
        if width < self.MOBILE_BREAKPOINT:
            return "mobile"
        elif width < self.TABLET_BREAKPOINT:
            return "tablet"
        else:
            return "desktop"
            
    def _apply_layout_mode(self, mode: str):
        """Apply layout changes for the given mode"""
        if not self.main_splitter or not self.sidebar_widget:
            return
            
        if mode == "mobile":
            self._apply_mobile_layout()
        elif mode == "tablet":
            self._apply_tablet_layout()
        else:
            self._apply_desktop_layout()
            
    def _apply_mobile_layout(self):
        """Apply mobile-specific layout"""
        if self.main_splitter:
            # Hide sidebar by default on mobile
            self.sidebar_widget.setVisible(False)
            self.sidebar_visible = False
            
            # Set splitter to vertical orientation for mobile
            self.main_splitter.setOrientation(Qt.Orientation.Vertical)
            
            # Adjust sizes for mobile
            if self.main_content:
                self.main_content.setMinimumWidth(0)
                
        self.logger.debug("Applied mobile layout")
        
    def _apply_tablet_layout(self):
        """Apply tablet-specific layout"""
        if self.main_splitter:
            # Show sidebar but make it narrower
            self.sidebar_widget.setVisible(True)
            self.sidebar_visible = True
            
            # Keep horizontal orientation
            self.main_splitter.setOrientation(Qt.Orientation.Horizontal)
            
            # Adjust sidebar width for tablet
            self.sidebar_widget.setMaximumWidth(280)
            self.sidebar_widget.setMinimumWidth(250)
            
            # Update splitter sizes
            self.main_splitter.setSizes([600, 280])
            
        self.logger.debug("Applied tablet layout")
        
    def _apply_desktop_layout(self):
        """Apply desktop-specific layout"""
        if self.main_splitter:
            # Show sidebar with full width
            self.sidebar_widget.setVisible(True)
            self.sidebar_visible = True
            
            # Horizontal orientation
            self.main_splitter.setOrientation(Qt.Orientation.Horizontal)
            
            # Full sidebar width for desktop
            self.sidebar_widget.setMaximumWidth(350)
            self.sidebar_widget.setMinimumWidth(300)
            
            # Update splitter sizes
            self.main_splitter.setSizes([800, 350])
            
        self.logger.debug("Applied desktop layout")
        
    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        if not self.sidebar_widget:
            return
            
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar_widget.setVisible(self.sidebar_visible)
        self.sidebar_toggled.emit(self.sidebar_visible)
        
        self.logger.info(f"Sidebar toggled: {'visible' if self.sidebar_visible else 'hidden'}")
        
    def force_layout_mode(self, mode: str):
        """Force a specific layout mode (for testing)"""
        if mode in ["mobile", "tablet", "desktop"]:
            self.current_mode = mode
            self._apply_layout_mode(mode)
            self.layout_changed.emit(mode)
            self.logger.info(f"Forced layout mode: {mode}")
            
    def get_current_mode(self) -> str:
        """Get current layout mode"""
        return self.current_mode
        
    def is_mobile(self) -> bool:
        """Check if current mode is mobile"""
        return self.current_mode == "mobile"
        
    def is_tablet(self) -> bool:
        """Check if current mode is tablet"""
        return self.current_mode == "tablet"
        
    def is_desktop(self) -> bool:
        """Check if current mode is desktop"""
        return self.current_mode == "desktop"


class TouchFriendlyMixin:
    """Mixin to make components touch-friendly"""
    
    def make_touch_friendly(self):
        """Apply touch-friendly modifications"""
        # Increase minimum sizes for touch targets
        if hasattr(self, 'setMinimumSize'):
            current_size = self.minimumSize()
            touch_size = QSize(
                max(current_size.width(), 44),  # 44px minimum for touch
                max(current_size.height(), 44)
            )
            self.setMinimumSize(touch_size)
            
        # Add touch-friendly styling
        if hasattr(self, 'setStyleSheet'):
            current_style = self.styleSheet()
            touch_style = """
                /* Touch-friendly padding and margins */
                padding: 12px;
                margin: 8px;
                
                /* Larger touch targets */
                min-height: 44px;
                min-width: 44px;
                
                /* Better visual feedback */
                border-radius: 8px;
                transition: all 0.2s ease;
            """
            self.setStyleSheet(current_style + touch_style)


class ResponsiveGridLayout(QGridLayout):
    """Grid layout that adapts to screen size"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.responsive_manager = None
        self.desktop_columns = 4
        self.tablet_columns = 3
        self.mobile_columns = 1
        
    def set_responsive_manager(self, manager: ResponsiveLayoutManager):
        """Set the responsive manager"""
        self.responsive_manager = manager
        manager.layout_changed.connect(self._on_layout_changed)
        
    def _on_layout_changed(self, mode: str):
        """Handle layout mode changes"""
        if mode == "mobile":
            self._reorganize_grid(self.mobile_columns)
        elif mode == "tablet":
            self._reorganize_grid(self.tablet_columns)
        else:
            self._reorganize_grid(self.desktop_columns)
            
    def _reorganize_grid(self, columns: int):
        """Reorganize grid items for new column count"""
        # Get all items
        items = []
        for i in range(self.count()):
            item = self.itemAt(i)
            if item and item.widget():
                items.append(item.widget())
                
        # Remove all items
        for item in items:
            self.removeWidget(item)
            
        # Re-add items with new column layout
        for i, item in enumerate(items):
            row = i // columns
            col = i % columns
            self.addWidget(item, row, col)
            
        # Set column stretch
        for col in range(columns):
            self.setColumnStretch(col, 1)


class CollapsibleSidebar(QWidget):
    """Sidebar that can be collapsed/expanded"""
    
    collapsed_changed = Signal(bool)  # is_collapsed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_collapsed = False
        self.expanded_width = 350
        self.collapsed_width = 60
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        self.setFixedWidth(self.expanded_width)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toggle button
        from qfluentwidgets import ToolButton, FluentIcon
        self.toggle_btn = ToolButton(FluentIcon.MENU)
        self.toggle_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self.toggle_btn)
        
        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        layout.addWidget(self.content_widget)
        
    def toggle_collapse(self):
        """Toggle collapsed state"""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.setFixedWidth(self.collapsed_width)
            self.content_widget.setVisible(False)
        else:
            self.setFixedWidth(self.expanded_width)
            self.content_widget.setVisible(True)
            
        self.collapsed_changed.emit(self.is_collapsed)
        
    def add_content(self, widget: QWidget):
        """Add content to the sidebar"""
        self.content_layout.addWidget(widget)
