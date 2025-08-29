"""
Progressive Feature Discovery System

Gradually introduces features to users based on their experience level,
usage patterns, and onboarding progress.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import InfoBar, InfoBarPosition, TeachingTip, TeachingTipTailPosition

from ...common.i18n_ui import tr
from ...common.logging_config import get_logger
from .user_state_tracker import OnboardingStep, UserLevel, UserStateTracker


class FeatureCategory(Enum):
    """Categories of features"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class DiscoveryTrigger(Enum):
    """Triggers for feature discovery"""
    TIME_BASED = "time_based"
    ACTION_BASED = "action_based"
    USAGE_BASED = "usage_based"
    ONBOARDING_STEP = "onboarding_step"
    USER_LEVEL_CHANGE = "user_level_change"


class Feature:
    """Represents a discoverable feature"""
    
    def __init__(
        self,
        feature_id: str,
        name_key: str,
        description_key: str,
        category: FeatureCategory,
        trigger: DiscoveryTrigger,
        trigger_condition: Any,
        target_widget: Optional[str] = None,
        prerequisites: Optional[List[str]] = None,
        user_levels: Optional[List[UserLevel]] = None,
        priority: int = 1,
        max_show_count: int = 2,
    ):
        self.feature_id = feature_id
        self.name_key = name_key
        self.description_key = description_key
        self.category = category
        self.trigger = trigger
        self.trigger_condition = trigger_condition
        self.target_widget = target_widget
        self.prerequisites = prerequisites or []
        self.user_levels = user_levels or [UserLevel.BEGINNER, UserLevel.INTERMEDIATE, UserLevel.ADVANCED]
        self.priority = priority
        self.max_show_count = max_show_count
        self.show_count = 0
        self.discovered = False
        self.last_shown: Optional[datetime] = None
    
    def get_name(self) -> str:
        """Get the translated feature name"""
        return tr(self.name_key, default=f"Feature: {self.feature_id}")
    
    def get_description(self) -> str:
        """Get the translated feature description"""
        return tr(self.description_key, default=f"Description: {self.feature_id}")
    
    def can_discover(
        self,
        user_level: UserLevel,
        completed_actions: Set[str],
        current_context: str,
    ) -> bool:
        """Check if this feature can be discovered"""
        # Check if already discovered too many times
        if self.show_count >= self.max_show_count:
            return False
        
        # Check user level
        if user_level not in self.user_levels:
            return False
        
        # Check prerequisites
        for prereq in self.prerequisites:
            if prereq not in completed_actions:
                return False
        
        return True
    
    def mark_discovered(self) -> None:
        """Mark this feature as discovered"""
        self.discovered = True
        self.show_count += 1
        self.last_shown = datetime.now()


class ProgressiveFeatureDiscovery(QObject):
    """Manages progressive feature discovery throughout the application"""
    
    # Signals
    feature_discovered = Signal(str)  # feature_id
    feature_highlighted = Signal(str, str)  # feature_id, widget_name
    discovery_completed = Signal()
    
    def __init__(self, user_tracker: UserStateTracker, main_window: QWidget, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger("feature_discovery", module="ProgressiveFeatureDiscovery")
        self.user_tracker = user_tracker
        self.main_window = main_window
        
        # Feature management
        self.features: Dict[str, Feature] = {}
        self.discovered_features: Set[str] = set()
        self.pending_discoveries: List[Feature] = []
        self.current_context = "general"
        
        # Discovery timers
        self.discovery_timer = QTimer(self)
        self.discovery_timer.timeout.connect(self._check_time_based_discoveries)
        self.discovery_timer.start(30000)  # Check every 30 seconds
        
        self._init_features()
        self._connect_signals()
    
    def _init_features(self) -> None:
        """Initialize discoverable features"""
        features_data = [
            # Basic features for beginners
            {
                "feature_id": "server_context_menu",
                "name_key": "features.server_context_menu.name",
                "description_key": "features.server_context_menu.description",
                "category": FeatureCategory.BASIC,
                "trigger": DiscoveryTrigger.ACTION_BASED,
                "trigger_condition": "server_card_clicked",
                "target_widget": "server_cards",
                "user_levels": [UserLevel.BEGINNER],
                "priority": 5,
            },
            {
                "feature_id": "quick_actions_bar",
                "name_key": "features.quick_actions_bar.name",
                "description_key": "features.quick_actions_bar.description",
                "category": FeatureCategory.BASIC,
                "trigger": DiscoveryTrigger.TIME_BASED,
                "trigger_condition": timedelta(minutes=2),
                "target_widget": "quick_action_bar",
                "user_levels": [UserLevel.BEGINNER],
                "priority": 4,
            },
            {
                "feature_id": "status_monitoring",
                "name_key": "features.status_monitoring.name",
                "description_key": "features.status_monitoring.description",
                "category": FeatureCategory.BASIC,
                "trigger": DiscoveryTrigger.USAGE_BASED,
                "trigger_condition": {"servers_started": 1},
                "target_widget": "status_overview",
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
                "priority": 3,
            },
            
            # Intermediate features
            {
                "feature_id": "batch_operations",
                "name_key": "features.batch_operations.name",
                "description_key": "features.batch_operations.description",
                "category": FeatureCategory.INTERMEDIATE,
                "trigger": DiscoveryTrigger.USAGE_BASED,
                "trigger_condition": {"servers_managed": 3},
                "prerequisites": ["used_server_controls"],
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
                "priority": 3,
            },
            {
                "feature_id": "log_monitoring",
                "name_key": "features.log_monitoring.name",
                "description_key": "features.log_monitoring.description",
                "category": FeatureCategory.INTERMEDIATE,
                "trigger": DiscoveryTrigger.ACTION_BASED,
                "trigger_condition": "server_error_occurred",
                "target_widget": "logs_section",
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
                "priority": 4,
            },
            {
                "feature_id": "module_store",
                "name_key": "features.module_store.name",
                "description_key": "features.module_store.description",
                "category": FeatureCategory.INTERMEDIATE,
                "trigger": DiscoveryTrigger.ONBOARDING_STEP,
                "trigger_condition": OnboardingStep.CUSTOMIZATION,
                "target_widget": "download_tab",
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
                "priority": 3,
            },
            
            # Advanced features
            {
                "feature_id": "module_development",
                "name_key": "features.module_development.name",
                "description_key": "features.module_development.description",
                "category": FeatureCategory.ADVANCED,
                "trigger": DiscoveryTrigger.USER_LEVEL_CHANGE,
                "trigger_condition": UserLevel.INTERMEDIATE,
                "target_widget": "scaffold_tool",
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
                "priority": 2,
            },
            {
                "feature_id": "environment_configuration",
                "name_key": "features.environment_configuration.name",
                "description_key": "features.environment_configuration.description",
                "category": FeatureCategory.ADVANCED,
                "trigger": DiscoveryTrigger.USAGE_BASED,
                "trigger_condition": {"tools_used": 2},
                "target_widget": "environment_tab",
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
                "priority": 2,
            },
            {
                "feature_id": "custom_commands",
                "name_key": "features.custom_commands.name",
                "description_key": "features.custom_commands.description",
                "category": FeatureCategory.ADVANCED,
                "trigger": DiscoveryTrigger.TIME_BASED,
                "trigger_condition": timedelta(days=3),
                "prerequisites": ["used_basic_features"],
                "user_levels": [UserLevel.ADVANCED],
                "priority": 2,
            },
            
            # Expert features
            {
                "feature_id": "api_integration",
                "name_key": "features.api_integration.name",
                "description_key": "features.api_integration.description",
                "category": FeatureCategory.EXPERT,
                "trigger": DiscoveryTrigger.USAGE_BASED,
                "trigger_condition": {"modules_created": 1},
                "prerequisites": ["module_development_used"],
                "user_levels": [UserLevel.ADVANCED],
                "priority": 1,
            },
        ]
        
        # Create Feature objects
        for feature_data in features_data:
            feature = Feature(
                feature_id=feature_data["feature_id"],
                name_key=feature_data["name_key"],
                description_key=feature_data["description_key"],
                category=FeatureCategory(feature_data["category"]),
                trigger=DiscoveryTrigger(feature_data["trigger"]),
                trigger_condition=feature_data["trigger_condition"],
                target_widget=feature_data.get("target_widget"),
                prerequisites=feature_data.get("prerequisites"),
                user_levels=[UserLevel(level) for level in feature_data.get("user_levels", [])],
                priority=feature_data["priority"],
                max_show_count=feature_data.get("max_show_count", 2),
            )
            self.features[feature.feature_id] = feature
        
        self.logger.info(f"Initialized {len(self.features)} discoverable features")
    
    def _connect_signals(self) -> None:
        """Connect to user tracker signals"""
        self.user_tracker.onboarding_step_completed.connect(self._handle_onboarding_step)
        self.user_tracker.user_level_changed.connect(self._handle_user_level_change)
    
    def set_context(self, context: str) -> None:
        """Set the current context for feature discovery"""
        if self.current_context != context:
            self.current_context = context
            self.logger.debug(f"Context changed to: {context}")
            self._check_context_based_discoveries()
    
    def track_action(self, action: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Track a user action that might trigger feature discovery"""
        self.logger.debug(f"Tracking action: {action}")
        
        # Check for action-based discoveries
        for feature in self.features.values():
            if (feature.trigger == DiscoveryTrigger.ACTION_BASED and
                feature.trigger_condition == action and
                not feature.discovered):
                self._trigger_discovery(feature)
    
    def track_usage_metric(self, metric: str, value: Any) -> None:
        """Track a usage metric that might trigger feature discovery"""
        self.logger.debug(f"Tracking usage metric: {metric} = {value}")
        
        # Check for usage-based discoveries
        for feature in self.features.values():
            if (feature.trigger == DiscoveryTrigger.USAGE_BASED and
                isinstance(feature.trigger_condition, dict) and
                metric in feature.trigger_condition and
                value >= feature.trigger_condition[metric] and
                not feature.discovered):
                self._trigger_discovery(feature)
    
    def _check_time_based_discoveries(self) -> None:
        """Check for time-based feature discoveries"""
        current_time = datetime.now()
        
        for feature in self.features.values():
            if (feature.trigger == DiscoveryTrigger.TIME_BASED and
                isinstance(feature.trigger_condition, timedelta) and
                not feature.discovered):
                
                # Check if enough time has passed since user started using the app
                user_start_time = self._get_user_start_time()
                if user_start_time and current_time - user_start_time >= feature.trigger_condition:
                    self._trigger_discovery(feature)
    
    def _check_context_based_discoveries(self) -> None:
        """Check for context-based feature discoveries"""
        # This could trigger discoveries based on current interface context
        pass
    
    def _handle_onboarding_step(self, step_name: str) -> None:
        """Handle onboarding step completion"""
        try:
            step = OnboardingStep(step_name)
            for feature in self.features.values():
                if (feature.trigger == DiscoveryTrigger.ONBOARDING_STEP and
                    feature.trigger_condition == step and
                    not feature.discovered):
                    self._trigger_discovery(feature)
        except ValueError:
            pass
    
    def _handle_user_level_change(self, new_level: str) -> None:
        """Handle user level changes"""
        try:
            level = UserLevel(new_level)
            for feature in self.features.values():
                if (feature.trigger == DiscoveryTrigger.USER_LEVEL_CHANGE and
                    feature.trigger_condition == level and
                    not feature.discovered):
                    self._trigger_discovery(feature)
        except ValueError:
            pass
    
    def _trigger_discovery(self, feature: Feature) -> None:
        """Trigger discovery of a specific feature"""
        user_level = self.user_tracker.get_user_level()
        completed_actions = set()  # Would get from user tracker
        
        if feature.can_discover(user_level, completed_actions, self.current_context):
            self._show_feature_discovery(feature)
    
    def _show_feature_discovery(self, feature: Feature) -> None:
        """Show feature discovery notification"""
        try:
            name = feature.get_name()
            description = feature.get_description()
            
            # Find target widget
            target_widget = self._find_target_widget(feature.target_widget)
            if not target_widget:
                target_widget = self.main_window
            
            # Show discovery notification
            tip = TeachingTip.create(
                target=target_widget,
                icon=None,
                title=tr("features.discovery_title", default="🎉 New Feature"),
                content=f"**{name}**\n\n{description}",
                isClosable=True,
                tailPosition=TeachingTipTailPosition.BOTTOM,
                parent=self.main_window
            )
            
            # Mark as discovered
            feature.mark_discovered()
            self.discovered_features.add(feature.feature_id)
            
            # Emit signals
            self.feature_discovered.emit(feature.feature_id)
            if feature.target_widget:
                self.feature_highlighted.emit(feature.feature_id, feature.target_widget)
            
            self.logger.info(f"Feature discovered: {feature.feature_id}")
            
            # Auto-dismiss after some time
            QTimer.singleShot(8000, tip.close)
            
        except Exception as e:
            self.logger.error(f"Error showing feature discovery: {e}")
    
    def _find_target_widget(self, widget_name: Optional[str]) -> Optional[QWidget]:
        """Find a target widget by name"""
        if not widget_name:
            return None
        
        # This would implement widget lookup logic
        # For now, return main window as fallback
        return self.main_window
    
    def _get_user_start_time(self) -> Optional[datetime]:
        """Get when the user first started using the app"""
        # This would get from user tracker
        return datetime.now() - timedelta(hours=1)  # Placeholder
    
    def get_discovery_progress(self) -> Dict[str, Any]:
        """Get feature discovery progress"""
        total_features = len(self.features)
        discovered_count = len(self.discovered_features)
        
        category_progress = {}
        for category in FeatureCategory:
            category_features = [f for f in self.features.values() if f.category == category]
            category_discovered = [f for f in category_features if f.discovered]
            category_progress[category.value] = {
                "total": len(category_features),
                "discovered": len(category_discovered),
                "percentage": (len(category_discovered) / len(category_features)) * 100 if category_features else 0
            }
        
        return {
            "total_features": total_features,
            "discovered_features": discovered_count,
            "discovery_percentage": (discovered_count / total_features) * 100 if total_features else 0,
            "category_progress": category_progress,
            "current_context": self.current_context,
        }
    
    def force_discover_feature(self, feature_id: str) -> bool:
        """Force discovery of a specific feature"""
        if feature_id in self.features:
            feature = self.features[feature_id]
            self._show_feature_discovery(feature)
            return True
        return False
