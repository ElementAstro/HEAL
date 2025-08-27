"""
Smart Tip System

Intelligent tip system that provides contextual, adaptive tips based on
user behavior, experience level, and current context.
"""

import random
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import QObject, QTimer, Signal

from src.heal.common.i18n_ui import tr
from src.heal.common.logging_config import get_logger
from .user_state_tracker import UserLevel, UserStateTracker


class TipCategory(Enum):
    """Categories of tips"""
    BASIC_USAGE = "basic_usage"
    ADVANCED_FEATURES = "advanced_features"
    SHORTCUTS = "shortcuts"
    TROUBLESHOOTING = "troubleshooting"
    PRODUCTIVITY = "productivity"
    CUSTOMIZATION = "customization"
    BEST_PRACTICES = "best_practices"


class TipContext(Enum):
    """Contexts where tips can be shown"""
    HOME = "home"
    LAUNCHER = "launcher"
    DOWNLOAD = "download"
    ENVIRONMENT = "environment"
    TOOLS = "tools"
    SETTINGS = "settings"
    GENERAL = "general"


class SmartTip:
    """Represents a smart tip with metadata"""
    
    def __init__(
        self,
        tip_id: str,
        content_key: str,
        category: TipCategory,
        context: TipContext,
        user_levels: List[UserLevel],
        priority: int = 1,
        prerequisites: Optional[List[str]] = None,
        frequency_limit: Optional[timedelta] = None,
        action_triggers: Optional[List[str]] = None,
    ):
        self.tip_id = tip_id
        self.content_key = content_key
        self.category = category
        self.context = context
        self.user_levels = user_levels
        self.priority = priority
        self.prerequisites = prerequisites or []
        self.frequency_limit = frequency_limit
        self.action_triggers = action_triggers or []
        self.last_shown: Optional[datetime] = None
        self.show_count = 0
    
    def get_content(self) -> str:
        """Get the translated tip content"""
        return tr(self.content_key, default=f"Tip: {self.tip_id}")
    
    def is_applicable(
        self,
        user_level: UserLevel,
        context: TipContext,
        completed_actions: Set[str],
        last_shown_times: Dict[str, datetime],
    ) -> bool:
        """Check if this tip is applicable in the current context"""
        # Check user level
        if user_level not in self.user_levels:
            return False
        
        # Check context
        if self.context != TipContext.GENERAL and self.context != context:
            return False
        
        # Check prerequisites
        for prereq in self.prerequisites:
            if prereq not in completed_actions:
                return False
        
        # Check frequency limit
        if self.frequency_limit and self.tip_id in last_shown_times:
            time_since_last = datetime.now() - last_shown_times[self.tip_id]
            if time_since_last < self.frequency_limit:
                return False
        
        return True
    
    def mark_shown(self) -> None:
        """Mark this tip as shown"""
        self.last_shown = datetime.now()
        self.show_count += 1


class SmartTipSystem(QObject):
    """Intelligent tip system that adapts to user behavior"""
    
    # Signals
    tip_requested = Signal(str)  # tip_content
    tip_shown = Signal(str)  # tip_id
    
    def __init__(self, user_tracker: UserStateTracker, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger("smart_tip_system", module="SmartTipSystem")
        self.user_tracker = user_tracker
        
        # Tip management
        self.tips: Dict[str, SmartTip] = {}
        self.last_shown_times: Dict[str, datetime] = {}
        self.completed_actions: Set[str] = set()
        self.current_context = TipContext.GENERAL
        
        # Tip rotation
        self.rotation_timer = QTimer(self)
        self.rotation_timer.timeout.connect(self._rotate_tip)
        
        self._init_tips()
        self._load_tip_history()
    
    def _init_tips(self) -> None:
        """Initialize the tip database"""
        tips_data = [
            # Basic usage tips
            {
                "tip_id": "server_management_basics",
                "content_key": "tips.server_management_basics",
                "category": TipCategory.BASIC_USAGE,
                "context": TipContext.HOME,
                "user_levels": [UserLevel.BEGINNER],
                "priority": 5,
            },
            {
                "tip_id": "quick_actions_bar",
                "content_key": "tips.quick_actions_bar",
                "category": TipCategory.BASIC_USAGE,
                "context": TipContext.HOME,
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
                "priority": 4,
            },
            {
                "tip_id": "context_menus",
                "content_key": "tips.context_menus",
                "category": TipCategory.BASIC_USAGE,
                "context": TipContext.GENERAL,
                "user_levels": [UserLevel.BEGINNER],
                "priority": 3,
            },
            
            # Keyboard shortcuts
            {
                "tip_id": "keyboard_shortcuts_basic",
                "content_key": "tips.keyboard_shortcuts_basic",
                "category": TipCategory.SHORTCUTS,
                "context": TipContext.GENERAL,
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
                "priority": 3,
                "frequency_limit": timedelta(hours=24),
            },
            {
                "tip_id": "keyboard_shortcuts_advanced",
                "content_key": "tips.keyboard_shortcuts_advanced",
                "category": TipCategory.SHORTCUTS,
                "context": TipContext.GENERAL,
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
                "priority": 2,
                "prerequisites": ["used_basic_shortcuts"],
            },
            
            # Advanced features
            {
                "tip_id": "module_development",
                "content_key": "tips.module_development",
                "category": TipCategory.ADVANCED_FEATURES,
                "context": TipContext.TOOLS,
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
                "priority": 2,
                "prerequisites": ["visited_tools_section"],
            },
            {
                "tip_id": "environment_configuration",
                "content_key": "tips.environment_configuration",
                "category": TipCategory.ADVANCED_FEATURES,
                "context": TipContext.ENVIRONMENT,
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
                "priority": 3,
            },
            
            # Productivity tips
            {
                "tip_id": "batch_operations",
                "content_key": "tips.batch_operations",
                "category": TipCategory.PRODUCTIVITY,
                "context": TipContext.HOME,
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
                "priority": 2,
                "prerequisites": ["managed_multiple_servers"],
            },
            {
                "tip_id": "log_monitoring",
                "content_key": "tips.log_monitoring",
                "category": TipCategory.PRODUCTIVITY,
                "context": TipContext.HOME,
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
                "priority": 2,
                "action_triggers": ["server_error_occurred"],
            },
            
            # Customization tips
            {
                "tip_id": "interface_customization",
                "content_key": "tips.interface_customization",
                "category": TipCategory.CUSTOMIZATION,
                "context": TipContext.SETTINGS,
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
                "priority": 2,
                "frequency_limit": timedelta(days=7),
            },
            {
                "tip_id": "theme_selection",
                "content_key": "tips.theme_selection",
                "category": TipCategory.CUSTOMIZATION,
                "context": TipContext.SETTINGS,
                "user_levels": [UserLevel.BEGINNER],
                "priority": 1,
            },
            
            # Troubleshooting tips
            {
                "tip_id": "connection_issues",
                "content_key": "tips.connection_issues",
                "category": TipCategory.TROUBLESHOOTING,
                "context": TipContext.GENERAL,
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
                "priority": 4,
                "action_triggers": ["connection_failed"],
            },
            {
                "tip_id": "performance_optimization",
                "content_key": "tips.performance_optimization",
                "category": TipCategory.TROUBLESHOOTING,
                "context": TipContext.GENERAL,
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
                "priority": 3,
                "action_triggers": ["performance_issue_detected"],
            },
        ]
        
        # Create SmartTip objects
        for tip_data in tips_data:
            tip = SmartTip(
                tip_id=tip_data["tip_id"],
                content_key=tip_data["content_key"],
                category=TipCategory(tip_data["category"]),
                context=TipContext(tip_data["context"]),
                user_levels=[UserLevel(level) for level in tip_data["user_levels"]],
                priority=tip_data["priority"],
                prerequisites=tip_data.get("prerequisites"),
                frequency_limit=tip_data.get("frequency_limit"),
                action_triggers=tip_data.get("action_triggers"),
            )
            self.tips[tip.tip_id] = tip
        
        self.logger.info(f"Initialized {len(self.tips)} smart tips")
    
    def _load_tip_history(self) -> None:
        """Load tip showing history from user data"""
        # This would load from persistent storage
        # For now, we'll start fresh each session
        pass
    
    def set_context(self, context: TipContext) -> None:
        """Set the current context for tip selection"""
        if self.current_context != context:
            self.current_context = context
            self.logger.debug(f"Context changed to: {context.value}")
            
            # Immediately show a contextual tip if appropriate
            if self.user_tracker.should_show_tips():
                self._show_contextual_tip()
    
    def track_action(self, action: str) -> None:
        """Track a user action that might trigger tips"""
        self.completed_actions.add(action)
        
        # Check for action-triggered tips
        triggered_tips = [
            tip for tip in self.tips.values()
            if action in tip.action_triggers
        ]
        
        if triggered_tips and self.user_tracker.should_show_tips():
            # Show the highest priority triggered tip
            tip = max(triggered_tips, key=lambda t: t.priority)
            if self._is_tip_applicable(tip):
                self._show_tip(tip)
    
    def start_rotation(self, interval_ms: int = 8000) -> None:
        """Start automatic tip rotation"""
        if self.user_tracker.should_show_tips():
            self.rotation_timer.start(interval_ms)
            self.logger.info(f"Started tip rotation with {interval_ms}ms interval")
    
    def stop_rotation(self) -> None:
        """Stop automatic tip rotation"""
        self.rotation_timer.stop()
        self.logger.info("Stopped tip rotation")
    
    def _rotate_tip(self) -> None:
        """Rotate to the next appropriate tip"""
        if not self.user_tracker.should_show_tips():
            return
        
        applicable_tips = self._get_applicable_tips()
        if applicable_tips:
            # Select tip based on priority and randomness
            tip = self._select_tip(applicable_tips)
            self._show_tip(tip)
    
    def _show_contextual_tip(self) -> None:
        """Show a tip relevant to the current context"""
        context_tips = [
            tip for tip in self.tips.values()
            if tip.context == self.current_context and self._is_tip_applicable(tip)
        ]
        
        if context_tips:
            tip = max(context_tips, key=lambda t: t.priority)
            self._show_tip(tip)
    
    def _get_applicable_tips(self) -> List[SmartTip]:
        """Get all tips applicable in the current context"""
        user_level = self.user_tracker.get_user_level()
        
        applicable = []
        for tip in self.tips.values():
            if tip.is_applicable(
                user_level, self.current_context, 
                self.completed_actions, self.last_shown_times
            ):
                applicable.append(tip)
        
        return applicable
    
    def _is_tip_applicable(self, tip: SmartTip) -> bool:
        """Check if a specific tip is applicable"""
        user_level = self.user_tracker.get_user_level()
        return tip.is_applicable(
            user_level, self.current_context,
            self.completed_actions, self.last_shown_times
        )
    
    def _select_tip(self, tips: List[SmartTip]) -> SmartTip:
        """Select a tip from applicable tips using weighted random selection"""
        if not tips:
            return None
        
        # Weight by priority and inverse of show count
        weights = []
        for tip in tips:
            weight = tip.priority * (1.0 / (tip.show_count + 1))
            weights.append(weight)
        
        # Weighted random selection
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(tips)
        
        r = random.uniform(0, total_weight)
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if r <= cumulative:
                return tips[i]
        
        return tips[-1]  # Fallback
    
    def _show_tip(self, tip: SmartTip) -> None:
        """Show a specific tip"""
        if tip is None:
            return
        
        content = tip.get_content()
        tip.mark_shown()
        self.last_shown_times[tip.tip_id] = datetime.now()
        
        self.tip_requested.emit(content)
        self.tip_shown.emit(tip.tip_id)
        
        self.logger.debug(f"Showed tip: {tip.tip_id}")
    
    def get_tip_for_context(self, context: TipContext) -> Optional[str]:
        """Get a specific tip for a context"""
        old_context = self.current_context
        self.set_context(context)
        
        applicable_tips = self._get_applicable_tips()
        if applicable_tips:
            tip = self._select_tip(applicable_tips)
            content = tip.get_content()
            self.set_context(old_context)  # Restore context
            return content
        
        self.set_context(old_context)  # Restore context
        return None
    
    def force_show_tip(self, tip_id: str) -> bool:
        """Force show a specific tip by ID"""
        if tip_id in self.tips:
            tip = self.tips[tip_id]
            self._show_tip(tip)
            return True
        return False
    
    def get_tip_statistics(self) -> Dict[str, Any]:
        """Get statistics about tip usage"""
        total_tips = len(self.tips)
        shown_tips = len([tip for tip in self.tips.values() if tip.show_count > 0])
        
        category_counts = {}
        for tip in self.tips.values():
            category = tip.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_tips": total_tips,
            "shown_tips": shown_tips,
            "category_distribution": category_counts,
            "current_context": self.current_context.value,
            "rotation_active": self.rotation_timer.isActive(),
        }
