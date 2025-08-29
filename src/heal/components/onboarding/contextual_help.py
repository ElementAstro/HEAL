"""
Contextual Help System

Provides intelligent, context-aware help and tooltips that adapt to user
behavior and experience level.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import QObject, QPoint, QTimer, Signal, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QLabel, QToolTip, QWidget
from qfluentwidgets import InfoBar, InfoBarPosition, TeachingTip, TeachingTipTailPosition

from ...common.i18n_ui import tr
from ...common.logging_config import get_logger
from .user_state_tracker import UserLevel, UserStateTracker


class HelpType(Enum):
    """Types of contextual help"""
    TOOLTIP = "tooltip"
    TEACHING_TIP = "teaching_tip"
    INFO_BAR = "info_bar"
    INLINE_HELP = "inline_help"


class HelpPriority(Enum):
    """Priority levels for help content"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ContextualHelpItem:
    """Represents a contextual help item"""
    
    def __init__(
        self,
        help_id: str,
        content_key: str,
        help_type: HelpType,
        priority: HelpPriority,
        target_widget: Optional[str] = None,
        user_levels: Optional[List[UserLevel]] = None,
        prerequisites: Optional[List[str]] = None,
        max_show_count: int = 3,
        delay_ms: int = 1000,
    ):
        self.help_id = help_id
        self.content_key = content_key
        self.help_type = help_type
        self.priority = priority
        self.target_widget = target_widget
        self.user_levels = user_levels or [UserLevel.BEGINNER, UserLevel.INTERMEDIATE, UserLevel.ADVANCED]
        self.prerequisites = prerequisites or []
        self.max_show_count = max_show_count
        self.delay_ms = delay_ms
        self.show_count = 0
        self.last_shown = None
    
    def get_content(self) -> str:
        """Get the translated help content"""
        return tr(self.content_key, default=f"Help: {self.help_id}")
    
    def can_show(self, user_level: UserLevel, completed_actions: Set[str]) -> bool:
        """Check if this help item can be shown"""
        # Check user level
        if user_level not in self.user_levels:
            return False
        
        # Check show count limit
        if self.show_count >= self.max_show_count:
            return False
        
        # Check prerequisites
        for prereq in self.prerequisites:
            if prereq not in completed_actions:
                return False
        
        return True
    
    def mark_shown(self) -> None:
        """Mark this help item as shown"""
        self.show_count += 1
        from datetime import datetime
        self.last_shown = datetime.now()


class ContextualHelpSystem(QObject):
    """Manages contextual help and tooltips throughout the application"""
    
    # Signals
    help_shown = Signal(str)  # help_id
    help_dismissed = Signal(str)  # help_id
    
    def __init__(self, main_window: QWidget, onboarding_manager: Any, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger("contextual_help", module="ContextualHelpSystem")
        self.main_window = main_window
        self.onboarding_manager = onboarding_manager
        self.user_tracker = onboarding_manager.get_user_state_tracker()
        
        # Help management
        self.help_items: Dict[str, ContextualHelpItem] = {}
        self.active_helps: Dict[str, Any] = {}  # help_id -> widget
        self.widget_help_map: Dict[QWidget, List[str]] = {}  # widget -> help_ids
        self.completed_actions: Set[str] = set()
        
        # Timers for delayed help
        self.help_timers: Dict[str, QTimer] = {}
        
        self._init_help_items()
        self._setup_global_event_filter()
    
    def _init_help_items(self) -> None:
        """Initialize contextual help items"""
        help_data = [
            # Home interface help
            {
                "help_id": "home_server_cards",
                "content_key": "help.home_server_cards",
                "help_type": HelpType.TEACHING_TIP,
                "priority": HelpPriority.MEDIUM,
                "target_widget": "server_cards_area",
                "user_levels": [UserLevel.BEGINNER],
                "delay_ms": 2000,
            },
            {
                "help_id": "home_quick_actions",
                "content_key": "help.home_quick_actions",
                "help_type": HelpType.TOOLTIP,
                "priority": HelpPriority.LOW,
                "target_widget": "quick_action_bar",
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
            },
            {
                "help_id": "home_status_overview",
                "content_key": "help.home_status_overview",
                "help_type": HelpType.TEACHING_TIP,
                "priority": HelpPriority.MEDIUM,
                "target_widget": "status_overview",
                "user_levels": [UserLevel.BEGINNER],
                "prerequisites": ["viewed_home_page"],
            },
            
            # Launcher interface help
            {
                "help_id": "launcher_server_config",
                "content_key": "help.launcher_server_config",
                "help_type": HelpType.INFO_BAR,
                "priority": HelpPriority.HIGH,
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
                "prerequisites": ["visited_launcher"],
            },
            
            # Download interface help
            {
                "help_id": "download_module_store",
                "content_key": "help.download_module_store",
                "help_type": HelpType.TEACHING_TIP,
                "priority": HelpPriority.MEDIUM,
                "target_widget": "module_store",
                "user_levels": [UserLevel.BEGINNER],
                "prerequisites": ["visited_download"],
            },
            
            # Environment interface help
            {
                "help_id": "environment_setup",
                "content_key": "help.environment_setup",
                "help_type": HelpType.INFO_BAR,
                "priority": HelpPriority.HIGH,
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
                "prerequisites": ["visited_environment"],
            },
            
            # Tools interface help
            {
                "help_id": "tools_scaffold",
                "content_key": "help.tools_scaffold",
                "help_type": HelpType.TEACHING_TIP,
                "priority": HelpPriority.MEDIUM,
                "target_widget": "scaffold_tool",
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
                "prerequisites": ["visited_tools"],
            },
            
            # Settings interface help
            {
                "help_id": "settings_customization",
                "content_key": "help.settings_customization",
                "help_type": HelpType.TOOLTIP,
                "priority": HelpPriority.LOW,
                "target_widget": "settings_tabs",
                "user_levels": [UserLevel.BEGINNER],
                "prerequisites": ["visited_settings"],
            },
            
            # Error recovery help
            {
                "help_id": "connection_error_help",
                "content_key": "help.connection_error_help",
                "help_type": HelpType.INFO_BAR,
                "priority": HelpPriority.CRITICAL,
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
                "max_show_count": 5,
            },
            {
                "help_id": "performance_help",
                "content_key": "help.performance_help",
                "help_type": HelpType.TEACHING_TIP,
                "priority": HelpPriority.HIGH,
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
                "max_show_count": 2,
            },
        ]
        
        # Create ContextualHelpItem objects
        for item_data in help_data:
            help_item = ContextualHelpItem(
                help_id=item_data["help_id"],
                content_key=item_data["content_key"],
                help_type=HelpType(item_data["help_type"]),
                priority=HelpPriority(item_data["priority"]),
                target_widget=item_data.get("target_widget"),
                user_levels=[UserLevel(level) for level in item_data.get("user_levels", [])],
                prerequisites=item_data.get("prerequisites"),
                max_show_count=item_data.get("max_show_count", 3),
                delay_ms=item_data.get("delay_ms", 1000),
            )
            self.help_items[help_item.help_id] = help_item
        
        self.logger.info(f"Initialized {len(self.help_items)} contextual help items")
    
    def _setup_global_event_filter(self) -> None:
        """Setup global event filter for widget interactions"""
        # This would install an event filter to track widget interactions
        # For now, we'll rely on explicit tracking calls
        pass
    
    def register_widget_help(self, widget: QWidget, help_ids: List[str]) -> None:
        """Register help items for a specific widget"""
        self.widget_help_map[widget] = help_ids
        self.logger.debug(f"Registered help for widget {widget.__class__.__name__}: {help_ids}")
    
    def show_contextual_help(self, context: str, widget: Optional[QWidget] = None) -> None:
        """Show contextual help for a specific context"""
        if not self.user_tracker.should_show_contextual_help():
            return
        
        user_level = self.user_tracker.get_user_level()
        applicable_helps = []
        
        # Find applicable help items
        for help_item in self.help_items.values():
            if help_item.can_show(user_level, self.completed_actions):
                # Check if help is relevant to current context
                if (help_item.target_widget == context or 
                    context in help_item.help_id or
                    widget and widget in self.widget_help_map and 
                    help_item.help_id in self.widget_help_map[widget]):
                    applicable_helps.append(help_item)
        
        if applicable_helps:
            # Show highest priority help
            help_item = max(applicable_helps, key=lambda h: h.priority.value)
            self._show_help_item(help_item, widget)
    
    def _show_help_item(self, help_item: ContextualHelpItem, target_widget: Optional[QWidget] = None) -> None:
        """Show a specific help item"""
        if help_item.help_id in self.active_helps:
            return  # Already showing
        
        def show_help():
            try:
                content = help_item.get_content()
                
                if help_item.help_type == HelpType.TOOLTIP:
                    self._show_tooltip(help_item, content, target_widget)
                elif help_item.help_type == HelpType.TEACHING_TIP:
                    self._show_teaching_tip(help_item, content, target_widget)
                elif help_item.help_type == HelpType.INFO_BAR:
                    self._show_info_bar(help_item, content)
                elif help_item.help_type == HelpType.INLINE_HELP:
                    self._show_inline_help(help_item, content, target_widget)
                
                help_item.mark_shown()
                self.help_shown.emit(help_item.help_id)
                self.logger.debug(f"Showed help: {help_item.help_id}")
                
            except Exception as e:
                self.logger.error(f"Error showing help {help_item.help_id}: {e}")
        
        # Show immediately or with delay
        if help_item.delay_ms > 0:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(show_help)
            timer.start(help_item.delay_ms)
            self.help_timers[help_item.help_id] = timer
        else:
            show_help()
    
    def _show_tooltip(self, help_item: ContextualHelpItem, content: str, widget: Optional[QWidget]) -> None:
        """Show a tooltip"""
        if widget:
            QToolTip.showText(widget.mapToGlobal(QPoint(0, widget.height())), content, widget)
        else:
            QToolTip.showText(QCursor.pos(), content)
    
    def _show_teaching_tip(self, help_item: ContextualHelpItem, content: str, widget: Optional[QWidget]) -> None:
        """Show a teaching tip"""
        if not widget:
            widget = self.main_window
        
        tip = TeachingTip.create(
            target=widget,
            icon=None,
            title=tr("help.tip_title", default="💡 Tip"),
            content=content,
            isClosable=True,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            parent=self.main_window
        )
        
        self.active_helps[help_item.help_id] = tip
        
        # Auto-dismiss after some time
        QTimer.singleShot(10000, lambda: self._dismiss_help(help_item.help_id))
    
    def _show_info_bar(self, help_item: ContextualHelpItem, content: str) -> None:
        """Show an info bar"""
        info_bar = InfoBar.info(
            title=tr("help.info_title", default="ℹ️ Help"),
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=8000,
            parent=self.main_window
        )
        
        self.active_helps[help_item.help_id] = info_bar
    
    def _show_inline_help(self, help_item: ContextualHelpItem, content: str, widget: Optional[QWidget]) -> None:
        """Show inline help"""
        # This would create an inline help widget
        # For now, fall back to teaching tip
        self._show_teaching_tip(help_item, content, widget)
    
    def _dismiss_help(self, help_id: str) -> None:
        """Dismiss a specific help item"""
        if help_id in self.active_helps:
            help_widget = self.active_helps[help_id]
            if hasattr(help_widget, 'close'):
                help_widget.close()
            del self.active_helps[help_id]
            self.help_dismissed.emit(help_id)
    
    def track_action(self, action: str) -> None:
        """Track a user action for help prerequisites"""
        self.completed_actions.add(action)
        self.logger.debug(f"Tracked action: {action}")
    
    def show_help_for_error(self, error_type: str, context: str) -> None:
        """Show help for specific error types"""
        error_help_map = {
            "connection_error": "connection_error_help",
            "performance_issue": "performance_help",
        }
        
        help_id = error_help_map.get(error_type)
        if help_id and help_id in self.help_items:
            help_item = self.help_items[help_id]
            user_level = self.user_tracker.get_user_level()
            if help_item.can_show(user_level, self.completed_actions):
                self._show_help_item(help_item)
    
    def dismiss_all_help(self) -> None:
        """Dismiss all active help items"""
        for help_id in list(self.active_helps.keys()):
            self._dismiss_help(help_id)
    
    def get_help_statistics(self) -> Dict[str, Any]:
        """Get statistics about help usage"""
        total_helps = len(self.help_items)
        shown_helps = len([h for h in self.help_items.values() if h.show_count > 0])
        active_helps = len(self.active_helps)
        
        return {
            "total_helps": total_helps,
            "shown_helps": shown_helps,
            "active_helps": active_helps,
            "completed_actions": len(self.completed_actions),
        }
