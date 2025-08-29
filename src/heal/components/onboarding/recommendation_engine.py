"""
Intelligent Recommendation Engine

Provides smart recommendations for actions, configurations, and features
based on user behavior patterns, preferences, and system state.
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from PySide6.QtCore import QObject, QTimer, Signal

from ...common.i18n_ui import tr
from ...common.logging_config import get_logger
from .user_state_tracker import UserLevel, UserStateTracker


class RecommendationType(Enum):
    """Types of recommendations"""
    ACTION = "action"
    CONFIGURATION = "configuration"
    FEATURE = "feature"
    WORKFLOW = "workflow"
    OPTIMIZATION = "optimization"
    TROUBLESHOOTING = "troubleshooting"


class RecommendationPriority(Enum):
    """Priority levels for recommendations"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class RecommendationTrigger(Enum):
    """Triggers for recommendations"""
    USER_BEHAVIOR = "user_behavior"
    SYSTEM_STATE = "system_state"
    TIME_BASED = "time_based"
    ERROR_PATTERN = "error_pattern"
    PERFORMANCE_ISSUE = "performance_issue"
    USAGE_PATTERN = "usage_pattern"


class Recommendation:
    """Represents a single recommendation"""
    
    def __init__(
        self,
        rec_id: str,
        title_key: str,
        description_key: str,
        rec_type: RecommendationType,
        priority: RecommendationPriority,
        trigger: RecommendationTrigger,
        action_data: Optional[Dict[str, Any]] = None,
        prerequisites: Optional[List[str]] = None,
        user_levels: Optional[List[UserLevel]] = None,
        expiry_hours: int = 24,
        max_show_count: int = 3,
    ):
        self.rec_id = rec_id
        self.title_key = title_key
        self.description_key = description_key
        self.rec_type = rec_type
        self.priority = priority
        self.trigger = trigger
        self.action_data = action_data or {}
        self.prerequisites = prerequisites or []
        self.user_levels = user_levels or [UserLevel.BEGINNER, UserLevel.INTERMEDIATE, UserLevel.ADVANCED]
        self.expiry_hours = expiry_hours
        self.max_show_count = max_show_count
        
        self.created_at = datetime.now()
        self.show_count = 0
        self.last_shown: Optional[datetime] = None
        self.dismissed = False
        self.accepted = False
    
    def get_title(self) -> str:
        """Get the translated recommendation title"""
        return tr(self.title_key, default=f"Recommendation: {self.rec_id}")
    
    def get_description(self) -> str:
        """Get the translated recommendation description"""
        return tr(self.description_key, default=f"Description: {self.rec_id}")
    
    def is_valid(self, user_level: UserLevel, completed_actions: Set[str]) -> bool:
        """Check if this recommendation is still valid"""
        # Check if expired
        if datetime.now() - self.created_at > timedelta(hours=self.expiry_hours):
            return False
        
        # Check if dismissed or shown too many times
        if self.dismissed or self.show_count >= self.max_show_count:
            return False
        
        # Check user level
        if user_level not in self.user_levels:
            return False
        
        # Check prerequisites
        for prereq in self.prerequisites:
            if prereq not in completed_actions:
                return False
        
        return True
    
    def mark_shown(self) -> None:
        """Mark this recommendation as shown"""
        self.show_count += 1
        self.last_shown = datetime.now()
    
    def mark_accepted(self) -> None:
        """Mark this recommendation as accepted"""
        self.accepted = True
    
    def mark_dismissed(self) -> None:
        """Mark this recommendation as dismissed"""
        self.dismissed = True


class RecommendationEngine(QObject):
    """Intelligent recommendation engine that analyzes user behavior and suggests improvements"""
    
    # Signals
    recommendation_generated = Signal(str)  # recommendation_id
    recommendation_shown = Signal(str)  # recommendation_id
    recommendation_accepted = Signal(str)  # recommendation_id
    recommendation_dismissed = Signal(str)  # recommendation_id
    
    def __init__(self, user_tracker: UserStateTracker, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger("recommendation_engine", module="RecommendationEngine")
        self.user_tracker = user_tracker
        
        # Recommendation management
        self.recommendations: Dict[str, Recommendation] = {}
        self.user_behavior_patterns: Dict[str, Any] = {}
        self.system_state_cache: Dict[str, Any] = {}
        self.error_patterns: List[Dict[str, Any]] = []
        
        # Analysis timers
        self.analysis_timer = QTimer(self)
        self.analysis_timer.timeout.connect(self._analyze_and_recommend)
        self.analysis_timer.start(60000)  # Analyze every minute
        
        self._init_recommendation_templates()
        self._load_user_patterns()
    
    def _init_recommendation_templates(self) -> None:
        """Initialize recommendation templates"""
        self.recommendation_templates = {
            # Action recommendations
            "setup_first_server": {
                "title_key": "recommendations.setup_first_server.title",
                "description_key": "recommendations.setup_first_server.description",
                "type": RecommendationType.ACTION,
                "priority": RecommendationPriority.HIGH,
                "trigger": RecommendationTrigger.USER_BEHAVIOR,
                "action_data": {"target": "launcher_tab", "action": "navigate"},
                "user_levels": [UserLevel.BEGINNER],
            },
            "explore_modules": {
                "title_key": "recommendations.explore_modules.title",
                "description_key": "recommendations.explore_modules.description",
                "type": RecommendationType.FEATURE,
                "priority": RecommendationPriority.MEDIUM,
                "trigger": RecommendationTrigger.TIME_BASED,
                "action_data": {"target": "download_tab", "action": "navigate"},
                "prerequisites": ["completed_basic_setup"],
            },
            "optimize_performance": {
                "title_key": "recommendations.optimize_performance.title",
                "description_key": "recommendations.optimize_performance.description",
                "type": RecommendationType.OPTIMIZATION,
                "priority": RecommendationPriority.HIGH,
                "trigger": RecommendationTrigger.PERFORMANCE_ISSUE,
                "action_data": {"target": "settings_tab", "action": "navigate", "section": "performance"},
            },
            
            # Configuration recommendations
            "configure_proxy": {
                "title_key": "recommendations.configure_proxy.title",
                "description_key": "recommendations.configure_proxy.description",
                "type": RecommendationType.CONFIGURATION,
                "priority": RecommendationPriority.MEDIUM,
                "trigger": RecommendationTrigger.ERROR_PATTERN,
                "action_data": {"target": "proxy_settings", "action": "configure"},
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
            },
            "setup_environment": {
                "title_key": "recommendations.setup_environment.title",
                "description_key": "recommendations.setup_environment.description",
                "type": RecommendationType.CONFIGURATION,
                "priority": RecommendationPriority.MEDIUM,
                "trigger": RecommendationTrigger.USER_BEHAVIOR,
                "action_data": {"target": "environment_tab", "action": "navigate"},
                "prerequisites": ["used_tools_section"],
            },
            
            # Workflow recommendations
            "batch_server_management": {
                "title_key": "recommendations.batch_server_management.title",
                "description_key": "recommendations.batch_server_management.description",
                "type": RecommendationType.WORKFLOW,
                "priority": RecommendationPriority.MEDIUM,
                "trigger": RecommendationTrigger.USAGE_PATTERN,
                "action_data": {"target": "quick_actions", "action": "highlight"},
                "prerequisites": ["managed_multiple_servers"],
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
            },
            "create_custom_module": {
                "title_key": "recommendations.create_custom_module.title",
                "description_key": "recommendations.create_custom_module.description",
                "type": RecommendationType.WORKFLOW,
                "priority": RecommendationPriority.LOW,
                "trigger": RecommendationTrigger.USER_BEHAVIOR,
                "action_data": {"target": "scaffold_tool", "action": "navigate"},
                "prerequisites": ["downloaded_modules", "used_tools"],
                "user_levels": [UserLevel.ADVANCED],
            },
            
            # Troubleshooting recommendations
            "check_logs": {
                "title_key": "recommendations.check_logs.title",
                "description_key": "recommendations.check_logs.description",
                "type": RecommendationType.TROUBLESHOOTING,
                "priority": RecommendationPriority.HIGH,
                "trigger": RecommendationTrigger.ERROR_PATTERN,
                "action_data": {"target": "logs_tab", "action": "navigate"},
            },
            "update_configuration": {
                "title_key": "recommendations.update_configuration.title",
                "description_key": "recommendations.update_configuration.description",
                "type": RecommendationType.TROUBLESHOOTING,
                "priority": RecommendationPriority.MEDIUM,
                "trigger": RecommendationTrigger.SYSTEM_STATE,
                "action_data": {"target": "settings_tab", "action": "navigate"},
            },
        }
        
        self.logger.info(f"Initialized {len(self.recommendation_templates)} recommendation templates")
    
    def _load_user_patterns(self) -> None:
        """Load user behavior patterns from storage"""
        # This would load from persistent storage
        # For now, initialize with empty patterns
        self.user_behavior_patterns = {
            "session_duration": [],
            "feature_usage": {},
            "error_frequency": {},
            "workflow_patterns": [],
            "time_patterns": {},
        }
    
    def track_user_action(self, action: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Track a user action for pattern analysis"""
        timestamp = datetime.now()
        
        # Update behavior patterns
        if "actions" not in self.user_behavior_patterns:
            self.user_behavior_patterns["actions"] = []
        
        self.user_behavior_patterns["actions"].append({
            "action": action,
            "timestamp": timestamp.isoformat(),
            "context": context or {}
        })
        
        # Analyze for immediate recommendations
        self._analyze_action_patterns(action, context)
        
        self.logger.debug(f"Tracked user action: {action}")
    
    def track_system_state(self, state_data: Dict[str, Any]) -> None:
        """Track system state for analysis"""
        self.system_state_cache.update(state_data)
        self._analyze_system_state()
    
    def track_error(self, error_type: str, error_context: Dict[str, Any]) -> None:
        """Track errors for pattern analysis"""
        error_data = {
            "type": error_type,
            "timestamp": datetime.now().isoformat(),
            "context": error_context
        }
        
        self.error_patterns.append(error_data)
        
        # Analyze for error-based recommendations
        self._analyze_error_patterns(error_type, error_context)
        
        self.logger.debug(f"Tracked error: {error_type}")
    
    def _analyze_and_recommend(self) -> None:
        """Periodic analysis and recommendation generation"""
        try:
            self._analyze_usage_patterns()
            self._analyze_time_patterns()
            self._analyze_performance_patterns()
            self._cleanup_expired_recommendations()
        except Exception as e:
            self.logger.error(f"Error in periodic analysis: {e}")
    
    def _analyze_action_patterns(self, action: str, context: Optional[Dict[str, Any]]) -> None:
        """Analyze action patterns for immediate recommendations"""
        user_level = self.user_tracker.get_user_level()
        
        # Check for specific action-based recommendations
        if action == "visited_home_page" and user_level == UserLevel.BEGINNER:
            if not self._has_active_recommendation("setup_first_server"):
                self._generate_recommendation("setup_first_server")
        
        elif action == "server_error_occurred":
            if not self._has_active_recommendation("check_logs"):
                self._generate_recommendation("check_logs")
        
        elif action == "connection_failed":
            if not self._has_active_recommendation("configure_proxy"):
                self._generate_recommendation("configure_proxy")
    
    def _analyze_system_state(self) -> None:
        """Analyze system state for recommendations"""
        # Check for performance issues
        if self.system_state_cache.get("cpu_usage", 0) > 80:
            if not self._has_active_recommendation("optimize_performance"):
                self._generate_recommendation("optimize_performance")
        
        # Check for configuration issues
        if not self.system_state_cache.get("servers_configured", False):
            if not self._has_active_recommendation("setup_first_server"):
                self._generate_recommendation("setup_first_server")
    
    def _analyze_error_patterns(self, error_type: str, error_context: Dict[str, Any]) -> None:
        """Analyze error patterns for recommendations"""
        # Count recent errors of this type
        recent_errors = [
            e for e in self.error_patterns
            if e["type"] == error_type and
            datetime.now() - datetime.fromisoformat(e["timestamp"]) < timedelta(hours=1)
        ]
        
        if len(recent_errors) >= 3:  # Multiple errors of same type
            if error_type == "connection_error":
                self._generate_recommendation("configure_proxy")
            elif error_type == "configuration_error":
                self._generate_recommendation("update_configuration")
    
    def _analyze_usage_patterns(self) -> None:
        """Analyze usage patterns for recommendations"""
        actions = self.user_behavior_patterns.get("actions", [])
        if not actions:
            return
        
        # Analyze recent actions
        recent_actions = [
            a for a in actions
            if datetime.now() - datetime.fromisoformat(a["timestamp"]) < timedelta(hours=24)
        ]
        
        # Check for patterns that suggest recommendations
        action_counts = {}
        for action in recent_actions:
            action_name = action["action"]
            action_counts[action_name] = action_counts.get(action_name, 0) + 1
        
        # Recommend batch operations if user frequently manages servers individually
        if action_counts.get("server_start_individual", 0) >= 3:
            if not self._has_active_recommendation("batch_server_management"):
                self._generate_recommendation("batch_server_management")
        
        # Recommend module exploration if user has been using basic features for a while
        if len(recent_actions) >= 10 and not any("download" in a["action"] for a in recent_actions):
            if not self._has_active_recommendation("explore_modules"):
                self._generate_recommendation("explore_modules")
    
    def _analyze_time_patterns(self) -> None:
        """Analyze time-based patterns for recommendations"""
        user_level = self.user_tracker.get_user_level()
        
        # Recommend advanced features after user has been using the app for a while
        if user_level == UserLevel.BEGINNER:
            # Check if user has been active for more than a week
            first_action = self.user_behavior_patterns.get("actions", [])
            if first_action:
                first_timestamp = datetime.fromisoformat(first_action[0]["timestamp"])
                if datetime.now() - first_timestamp > timedelta(days=7):
                    if not self._has_active_recommendation("explore_modules"):
                        self._generate_recommendation("explore_modules")
    
    def _analyze_performance_patterns(self) -> None:
        """Analyze performance patterns for recommendations"""
        # This would analyze system performance metrics
        # For now, check basic indicators
        if self.system_state_cache.get("memory_usage", 0) > 85:
            if not self._has_active_recommendation("optimize_performance"):
                self._generate_recommendation("optimize_performance")
    
    def _generate_recommendation(self, template_id: str) -> Optional[Recommendation]:
        """Generate a recommendation from a template"""
        if template_id not in self.recommendation_templates:
            self.logger.error(f"Unknown recommendation template: {template_id}")
            return None
        
        template = self.recommendation_templates[template_id]
        user_level = self.user_tracker.get_user_level()
        completed_actions = set()  # Would get from user tracker
        
        # Create recommendation
        rec_id = f"{template_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        recommendation = Recommendation(
            rec_id=rec_id,
            title_key=template["title_key"],
            description_key=template["description_key"],
            rec_type=template["type"],
            priority=template["priority"],
            trigger=template["trigger"],
            action_data=template.get("action_data"),
            prerequisites=template.get("prerequisites"),
            user_levels=template.get("user_levels"),
        )
        
        # Check if recommendation is valid
        if recommendation.is_valid(user_level, completed_actions):
            self.recommendations[rec_id] = recommendation
            self.recommendation_generated.emit(rec_id)
            self.logger.info(f"Generated recommendation: {rec_id}")
            return recommendation
        
        return None
    
    def _has_active_recommendation(self, template_id: str) -> bool:
        """Check if there's an active recommendation for a template"""
        for rec in self.recommendations.values():
            if (template_id in rec.rec_id and 
                not rec.dismissed and 
                not rec.accepted and
                rec.is_valid(self.user_tracker.get_user_level(), set())):
                return True
        return False
    
    def _cleanup_expired_recommendations(self) -> None:
        """Remove expired recommendations"""
        expired_ids = []
        user_level = self.user_tracker.get_user_level()
        
        for rec_id, rec in self.recommendations.items():
            if not rec.is_valid(user_level, set()):
                expired_ids.append(rec_id)
        
        for rec_id in expired_ids:
            del self.recommendations[rec_id]
        
        if expired_ids:
            self.logger.debug(f"Cleaned up {len(expired_ids)} expired recommendations")
    
    def get_active_recommendations(self, limit: int = 5) -> List[Recommendation]:
        """Get active recommendations sorted by priority"""
        user_level = self.user_tracker.get_user_level()
        completed_actions = set()  # Would get from user tracker
        
        active_recs = [
            rec for rec in self.recommendations.values()
            if rec.is_valid(user_level, completed_actions)
        ]
        
        # Sort by priority and creation time
        active_recs.sort(key=lambda r: (r.priority.value, r.created_at), reverse=True)
        
        return active_recs[:limit]
    
    def accept_recommendation(self, rec_id: str) -> bool:
        """Mark a recommendation as accepted"""
        if rec_id in self.recommendations:
            rec = self.recommendations[rec_id]
            rec.mark_accepted()
            self.recommendation_accepted.emit(rec_id)
            self.logger.info(f"Recommendation accepted: {rec_id}")
            return True
        return False
    
    def dismiss_recommendation(self, rec_id: str) -> bool:
        """Mark a recommendation as dismissed"""
        if rec_id in self.recommendations:
            rec = self.recommendations[rec_id]
            rec.mark_dismissed()
            self.recommendation_dismissed.emit(rec_id)
            self.logger.info(f"Recommendation dismissed: {rec_id}")
            return True
        return False
    
    def show_recommendation(self, rec_id: str) -> bool:
        """Mark a recommendation as shown"""
        if rec_id in self.recommendations:
            rec = self.recommendations[rec_id]
            rec.mark_shown()
            self.recommendation_shown.emit(rec_id)
            self.logger.debug(f"Recommendation shown: {rec_id}")
            return True
        return False
    
    def get_recommendation_statistics(self) -> Dict[str, Any]:
        """Get statistics about recommendations"""
        total_recs = len(self.recommendations)
        active_recs = len(self.get_active_recommendations(100))
        accepted_recs = len([r for r in self.recommendations.values() if r.accepted])
        dismissed_recs = len([r for r in self.recommendations.values() if r.dismissed])
        
        type_counts = {}
        for rec in self.recommendations.values():
            rec_type = rec.rec_type.value
            type_counts[rec_type] = type_counts.get(rec_type, 0) + 1
        
        return {
            "total_recommendations": total_recs,
            "active_recommendations": active_recs,
            "accepted_recommendations": accepted_recs,
            "dismissed_recommendations": dismissed_recs,
            "acceptance_rate": (accepted_recs / total_recs) * 100 if total_recs > 0 else 0,
            "type_distribution": type_counts,
        }
