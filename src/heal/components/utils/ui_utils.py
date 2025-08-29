"""
UI Utilities
Consolidated UI-related utility functions including scaffolding,
dispatch mechanisms, and UI helper functions.
"""

from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import time

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPixmap, QIcon

from ...common.logging_config import get_logger

# Re-export from existing modules for backward compatibility
from .dispatch import CommandDispatcher
from .scaffold import query_user, create_component_main

logger = get_logger(__name__)


class UIUtilities:
    """
    Consolidated UI utilities that provide comprehensive
    UI-related operations and helper functions.
    """
    
    @staticmethod
    def center_widget(widget: QWidget, parent: Optional[QWidget] = None) -> None:
        """Center widget on screen or parent"""
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - widget.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - widget.height()) // 2
        else:
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - widget.width()) // 2
            y = (screen.height() - widget.height()) // 2
        
        widget.move(x, y)
    
    @staticmethod
    def apply_theme_to_widget(widget: QWidget, theme_data: Dict[str, Any]) -> None:
        """Apply theme styling to widget"""
        try:
            if 'stylesheet' in theme_data:
                widget.setStyleSheet(theme_data['stylesheet'])
            
            if 'properties' in theme_data:
                for prop, value in theme_data['properties'].items():
                    widget.setProperty(prop, value)
            
            # Apply to child widgets if specified
            if theme_data.get('apply_to_children', False):
                for child in widget.findChildren(QWidget):
                    UIUtilities.apply_theme_to_widget(child, theme_data)
                    
        except Exception as e:
            logger.error(f"Failed to apply theme to widget: {e}")
    
    @staticmethod
    def create_icon_from_path(icon_path: str, size: Optional[tuple] = None) -> Optional[QIcon]:
        """Create QIcon from file path"""
        try:
            if not Path(icon_path).exists():
                logger.warning(f"Icon file not found: {icon_path}")
                return None
            
            pixmap = QPixmap(icon_path)
            if size:
                pixmap = pixmap.scaled(size[0], size[1])
            
            return QIcon(pixmap)
            
        except Exception as e:
            logger.error(f"Failed to create icon from {icon_path}: {e}")
            return None
    
    @staticmethod
    def get_widget_hierarchy(widget: QWidget) -> Dict[str, Any]:
        """Get widget hierarchy information"""
        hierarchy = {
            'class_name': widget.__class__.__name__,
            'object_name': widget.objectName(),
            'size': (widget.width(), widget.height()),
            'position': (widget.x(), widget.y()),
            'visible': widget.isVisible(),
            'enabled': widget.isEnabled(),
            'children': []
        }
        
        # Get child widgets
        for child in widget.findChildren(QWidget, options=1):  # Direct children only
            if child.parent() == widget:
                hierarchy['children'].append(UIUtilities.get_widget_hierarchy(child))
        
        return hierarchy
    
    @staticmethod
    def find_widgets_by_type(parent: QWidget, widget_type: type) -> List[QWidget]:
        """Find all widgets of specific type under parent"""
        return parent.findChildren(widget_type)
    
    @staticmethod
    def find_widget_by_name(parent: QWidget, object_name: str) -> Optional[QWidget]:
        """Find widget by object name"""
        return parent.findChild(QWidget, object_name)
    
    @staticmethod
    def batch_update_widgets(widgets: List[QWidget], update_func: Callable[[QWidget], None]) -> None:
        """Apply update function to multiple widgets efficiently"""
        try:
            # Disable updates during batch operation
            for widget in widgets:
                widget.setUpdatesEnabled(False)
            
            # Apply updates
            for widget in widgets:
                try:
                    update_func(widget)
                except Exception as e:
                    logger.error(f"Failed to update widget {widget.objectName()}: {e}")
            
            # Re-enable updates
            for widget in widgets:
                widget.setUpdatesEnabled(True)
                widget.update()
                
        except Exception as e:
            logger.error(f"Batch widget update failed: {e}")
    
    @staticmethod
    def create_responsive_layout(widgets: List[QWidget], max_columns: int = 3) -> Dict[str, Any]:
        """Create responsive layout configuration"""
        widget_count = len(widgets)
        
        if widget_count <= max_columns:
            columns = widget_count
            rows = 1
        else:
            columns = max_columns
            rows = (widget_count + max_columns - 1) // max_columns
        
        return {
            'columns': columns,
            'rows': rows,
            'total_widgets': widget_count,
            'layout_type': 'grid',
            'responsive': True
        }
    
    @staticmethod
    def animate_widget_property(
        widget: QWidget, 
        property_name: str, 
        start_value: Any, 
        end_value: Any, 
        duration: int = 300
    ) -> None:
        """Animate widget property change"""
        try:
            from PySide6.QtCore import QPropertyAnimation, QEasingCurve
            
            animation = QPropertyAnimation(widget, property_name.encode())
            animation.setDuration(duration)
            animation.setStartValue(start_value)
            animation.setEndValue(end_value)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.start()
            
        except Exception as e:
            logger.error(f"Failed to animate widget property: {e}")
            # Fallback to immediate change
            widget.setProperty(property_name, end_value)
    
    @staticmethod
    def capture_widget_screenshot(widget: QWidget, file_path: Optional[str] = None) -> Optional[str]:
        """Capture screenshot of widget"""
        try:
            pixmap = widget.grab()
            
            if not file_path:
                timestamp = int(time.time())
                file_path = f"debug/widget_screenshot_{timestamp}.png"
            
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save screenshot
            if pixmap.save(file_path):
                logger.info(f"Widget screenshot saved: {file_path}")
                return file_path
            else:
                logger.error("Failed to save widget screenshot")
                return None
                
        except Exception as e:
            logger.error(f"Failed to capture widget screenshot: {e}")
            return None
    
    @staticmethod
    def get_widget_performance_info(widget: QWidget) -> Dict[str, Any]:
        """Get performance information for widget"""
        info = {
            'class_name': widget.__class__.__name__,
            'object_name': widget.objectName(),
            'child_count': len(widget.findChildren(QWidget)),
            'size': (widget.width(), widget.height()),
            'visible': widget.isVisible(),
            'updates_enabled': widget.updatesEnabled(),
            'has_focus': widget.hasFocus(),
            'memory_estimate': 0  # Placeholder for actual memory calculation
        }
        
        # Estimate memory usage (simplified)
        info['memory_estimate'] = info['child_count'] * 1024  # Rough estimate
        
        return info
    
    @staticmethod
    def optimize_widget_performance(widget: QWidget) -> Dict[str, Any]:
        """Optimize widget performance and return optimization report"""
        optimizations = {
            'applied': [],
            'skipped': [],
            'performance_before': UIUtilities.get_widget_performance_info(widget),
            'performance_after': None
        }
        
        try:
            # Disable updates during optimization
            updates_enabled = widget.updatesEnabled()
            widget.setUpdatesEnabled(False)
            
            # Apply optimizations
            if widget.findChildren(QWidget):
                # Optimize child widgets
                for child in widget.findChildren(QWidget):
                    if not child.isVisible():
                        child.hide()  # Ensure hidden widgets are properly hidden
                        optimizations['applied'].append(f"Hidden invisible child: {child.objectName()}")
            
            # Re-enable updates
            widget.setUpdatesEnabled(updates_enabled)
            
            # Get performance after optimization
            optimizations['performance_after'] = UIUtilities.get_widget_performance_info(widget)
            
        except Exception as e:
            logger.error(f"Widget optimization failed: {e}")
            optimizations['error'] = str(e)
        
        return optimizations


class UIEventTracker(QObject):
    """
    Utility for tracking UI events and user interactions
    for debugging and analytics purposes.
    """
    
    event_tracked = Signal(str, dict)  # event_type, event_data
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.UIEventTracker")
        
        self.tracked_events: List[Dict[str, Any]] = []
        self.event_handlers: Dict[str, List[Callable]] = {}
        
    def track_widget_event(self, widget: QWidget, event_type: str, event_data: Dict[str, Any]) -> None:
        """Track a widget event"""
        event_record = {
            'timestamp': time.time(),
            'event_type': event_type,
            'widget_class': widget.__class__.__name__,
            'widget_name': widget.objectName(),
            'event_data': event_data
        }
        
        self.tracked_events.append(event_record)
        self.event_tracked.emit(event_type, event_record)
        
        # Call registered handlers
        for handler in self.event_handlers.get(event_type, []):
            try:
                handler(event_record)
            except Exception as e:
                self.logger.error(f"Event handler failed: {e}")
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register handler for specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        self.logger.debug(f"Registered handler for event type: {event_type}")
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get event tracking statistics"""
        stats = {
            'total_events': len(self.tracked_events),
            'event_types': {},
            'widget_classes': {},
            'recent_events': len([e for e in self.tracked_events if time.time() - e['timestamp'] < 3600])
        }
        
        for event in self.tracked_events:
            event_type = event['event_type']
            widget_class = event['widget_class']
            
            stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1
            stats['widget_classes'][widget_class] = stats['widget_classes'].get(widget_class, 0) + 1
        
        return stats


# Convenience functions for backward compatibility
def center_on_screen(widget: QWidget) -> None:
    """Center widget on screen (backward compatibility)"""
    UIUtilities.center_widget(widget)

def apply_stylesheet(widget: QWidget, stylesheet: str) -> None:
    """Apply stylesheet to widget (backward compatibility)"""
    widget.setStyleSheet(stylesheet)
