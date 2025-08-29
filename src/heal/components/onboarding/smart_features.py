"""
Consolidated Smart Features
Merges smart tip system, recommendation engine, and progressive feature discovery
into a unified intelligent assistance system.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer

from ...common.logging_config import get_logger

# Re-export for backward compatibility
from .smart_tip_system import SmartTipSystem
from .recommendation_engine import RecommendationEngine
from .feature_discovery import ProgressiveFeatureDiscovery

logger = get_logger(__name__)


class FeatureCategory(Enum):
    """Categories for smart features"""
    BASIC = "basic"
    ADVANCED = "advanced"
    PRODUCTIVITY = "productivity"
    CUSTOMIZATION = "customization"
    TROUBLESHOOTING = "troubleshooting"


class SmartFeatureType(Enum):
    """Types of smart features"""
    TIP = "tip"
    RECOMMENDATION = "recommendation"
    FEATURE_DISCOVERY = "feature_discovery"
    SHORTCUT = "shortcut"
    AUTOMATION = "automation"


@dataclass
class SmartFeature:
    """Unified smart feature structure"""
    feature_id: str
    title: str
    description: str
    feature_type: SmartFeatureType
    category: FeatureCategory
    priority: int = 1
    context: Optional[str] = None
    trigger_conditions: List[str] = field(default_factory=list)
    action_data: Dict[str, Any] = field(default_factory=dict)
    prerequisites: List[str] = field(default_factory=list)
    user_levels: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    last_shown: Optional[datetime] = None
    show_count: int = 0
    dismissed: bool = False
    accepted: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class SmartFeaturesManager(QObject):
    """
    Consolidated manager for all smart features including:
    - Smart tips and suggestions
    - Intelligent recommendations
    - Progressive feature discovery
    - Context-aware assistance
    """
    
    # Unified signals
    feature_suggested = Signal(str)  # feature_id
    feature_accepted = Signal(str)   # feature_id
    feature_dismissed = Signal(str)  # feature_id
    feature_discovered = Signal(str) # feature_id
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.SmartFeaturesManager")
        
        # Feature storage
        self.features: Dict[str, SmartFeature] = {}
        self.active_features: Set[str] = set()
        self.user_interactions: Dict[str, List[Dict[str, Any]]] = {}
        
        # Context tracking
        self.current_context: Optional[str] = None
        self.context_history: List[str] = []
        self.user_patterns: Dict[str, Any] = {}
        
        # Timers for intelligent suggestions
        self.suggestion_timer = QTimer()
        self.suggestion_timer.timeout.connect(self._analyze_and_suggest)
        self.suggestion_timer.start(30000)  # Check every 30 seconds
        
        # Configuration
        self.config_file = Path("config/smart_features.json")
        
        # Initialize
        self._load_features()
        self._initialize_default_features()
        
        self.logger.info("SmartFeaturesManager initialized")
    
    def register_feature(self, feature: SmartFeature) -> None:
        """Register a smart feature"""
        self.features[feature.feature_id] = feature
        self.logger.debug(f"Registered smart feature: {feature.feature_id}")
    
    def suggest_feature(self, feature_id: str, context: Optional[str] = None) -> bool:
        """Suggest a feature to the user"""
        if feature_id not in self.features:
            self.logger.warning(f"Feature not found: {feature_id}")
            return False
        
        feature = self.features[feature_id]
        
        # Check if feature should be suggested
        if not self._should_suggest_feature(feature, context):
            return False
        
        # Update feature stats
        feature.last_shown = datetime.now()
        feature.show_count += 1
        
        # Add to active features
        self.active_features.add(feature_id)
        
        # Emit signal
        self.feature_suggested.emit(feature_id)
        
        self.logger.info(f"Suggested feature: {feature_id}")
        return True
    
    def accept_feature(self, feature_id: str) -> bool:
        """Accept a suggested feature"""
        if feature_id not in self.features:
            return False
        
        feature = self.features[feature_id]
        feature.accepted = True
        feature.dismissed = False
        
        # Remove from active
        self.active_features.discard(feature_id)
        
        # Track interaction
        self._track_interaction(feature_id, "accepted")
        
        self.feature_accepted.emit(feature_id)
        self.logger.info(f"Feature accepted: {feature_id}")
        return True
    
    def dismiss_feature(self, feature_id: str) -> bool:
        """Dismiss a suggested feature"""
        if feature_id not in self.features:
            return False
        
        feature = self.features[feature_id]
        feature.dismissed = True
        feature.accepted = False
        
        # Remove from active
        self.active_features.discard(feature_id)
        
        # Track interaction
        self._track_interaction(feature_id, "dismissed")
        
        self.feature_dismissed.emit(feature_id)
        self.logger.info(f"Feature dismissed: {feature_id}")
        return True
    
    def discover_feature(self, feature_id: str, force: bool = False) -> bool:
        """Trigger feature discovery"""
        if feature_id not in self.features:
            return False
        
        feature = self.features[feature_id]
        
        # Check if discovery should happen
        if not force and not self._should_discover_feature(feature):
            return False
        
        # Trigger discovery
        self.feature_discovered.emit(feature_id)
        self._track_interaction(feature_id, "discovered")
        
        self.logger.info(f"Feature discovered: {feature_id}")
        return True
    
    def set_context(self, context: str) -> None:
        """Set current context for smart suggestions"""
        if self.current_context != context:
            self.current_context = context
            self.context_history.append(context)
            
            # Limit history size
            if len(self.context_history) > 50:
                self.context_history = self.context_history[-50:]
            
            # Trigger context-based suggestions
            self._suggest_for_context(context)
    
    def track_user_action(self, action: str, context: Optional[str] = None) -> None:
        """Track user action for pattern analysis"""
        action_data = {
            'action': action,
            'context': context or self.current_context,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in user patterns
        if action not in self.user_patterns:
            self.user_patterns[action] = []
        self.user_patterns[action].append(action_data)
        
        # Limit pattern history
        if len(self.user_patterns[action]) > 100:
            self.user_patterns[action] = self.user_patterns[action][-100:]
        
        self.logger.debug(f"Tracked user action: {action}")
    
    def get_active_features(self) -> List[SmartFeature]:
        """Get currently active features"""
        return [self.features[fid] for fid in self.active_features if fid in self.features]
    
    def get_feature_statistics(self) -> Dict[str, Any]:
        """Get smart features statistics"""
        stats = {
            'total_features': len(self.features),
            'active_features': len(self.active_features),
            'feature_types': {},
            'categories': {},
            'interactions': len(self.user_interactions)
        }
        
        # Count by type and category
        for feature in self.features.values():
            feature_type = feature.feature_type.value
            category = feature.category.value
            
            stats['feature_types'][feature_type] = stats['feature_types'].get(feature_type, 0) + 1
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
        
        return stats
    
    def _should_suggest_feature(self, feature: SmartFeature, context: Optional[str] = None) -> bool:
        """Determine if feature should be suggested"""
        # Don't suggest if already dismissed or accepted
        if feature.dismissed or feature.accepted:
            return False
        
        # Check context match
        if feature.context and context and feature.context != context:
            return False
        
        # Check if shown too recently
        if feature.last_shown:
            time_since_shown = datetime.now() - feature.last_shown
            if time_since_shown < timedelta(hours=1):  # Don't show again within 1 hour
                return False
        
        # Check show count limit
        if feature.show_count >= 3:  # Don't show more than 3 times
            return False
        
        return True
    
    def _should_discover_feature(self, feature: SmartFeature) -> bool:
        """Determine if feature should be discovered"""
        # Check if already discovered
        if feature.feature_id in self.user_interactions:
            interactions = self.user_interactions[feature.feature_id]
            if any(i.get('type') == 'discovered' for i in interactions):
                return False
        
        return True
    
    def _suggest_for_context(self, context: str) -> None:
        """Suggest features for specific context"""
        context_features = [
            f for f in self.features.values()
            if f.context == context and self._should_suggest_feature(f, context)
        ]
        
        # Sort by priority and suggest top feature
        if context_features:
            context_features.sort(key=lambda x: x.priority, reverse=True)
            self.suggest_feature(context_features[0].feature_id, context)
    
    def _track_interaction(self, feature_id: str, interaction_type: str) -> None:
        """Track user interaction with feature"""
        if feature_id not in self.user_interactions:
            self.user_interactions[feature_id] = []
        
        interaction_data = {
            'type': interaction_type,
            'timestamp': datetime.now().isoformat(),
            'context': self.current_context
        }
        
        self.user_interactions[feature_id].append(interaction_data)
    
    def _analyze_and_suggest(self) -> None:
        """Periodic analysis and suggestion generation"""
        try:
            # Analyze user patterns and suggest relevant features
            self._analyze_usage_patterns()
            self._suggest_based_on_patterns()
        except Exception as e:
            self.logger.error(f"Error in periodic analysis: {e}")
    
    def _analyze_usage_patterns(self) -> None:
        """Analyze user usage patterns"""
        # Placeholder for pattern analysis
        pass
    
    def _suggest_based_on_patterns(self) -> None:
        """Suggest features based on usage patterns"""
        # Placeholder for pattern-based suggestions
        pass
    
    def _load_features(self) -> None:
        """Load features from configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for feature_data in data.get('features', []):
                    feature = SmartFeature(
                        feature_id=feature_data['feature_id'],
                        title=feature_data['title'],
                        description=feature_data['description'],
                        feature_type=SmartFeatureType(feature_data['feature_type']),
                        category=FeatureCategory(feature_data['category']),
                        priority=feature_data.get('priority', 1),
                        context=feature_data.get('context'),
                        trigger_conditions=feature_data.get('trigger_conditions', []),
                        action_data=feature_data.get('action_data', {}),
                        prerequisites=feature_data.get('prerequisites', []),
                        user_levels=feature_data.get('user_levels', []),
                        keywords=feature_data.get('keywords', [])
                    )
                    self.register_feature(feature)
                
                self.logger.info(f"Loaded {len(self.features)} smart features")
                
        except Exception as e:
            self.logger.error(f"Failed to load features: {e}")
    
    def _initialize_default_features(self) -> None:
        """Initialize default smart features"""
        # Add some default features for common scenarios
        default_features = [
            SmartFeature(
                feature_id="keyboard_shortcuts",
                title="Keyboard Shortcuts",
                description="Learn useful keyboard shortcuts to work faster",
                feature_type=SmartFeatureType.TIP,
                category=FeatureCategory.PRODUCTIVITY,
                priority=2,
                keywords=["shortcuts", "keyboard", "productivity"]
            ),
            SmartFeature(
                feature_id="bulk_operations",
                title="Bulk Operations",
                description="Select multiple modules for batch operations",
                feature_type=SmartFeatureType.FEATURE_DISCOVERY,
                category=FeatureCategory.ADVANCED,
                priority=3,
                context="module_management",
                keywords=["bulk", "batch", "multiple", "selection"]
            ),
            SmartFeature(
                feature_id="performance_monitoring",
                title="Performance Monitoring",
                description="Monitor system performance and module metrics",
                feature_type=SmartFeatureType.RECOMMENDATION,
                category=FeatureCategory.ADVANCED,
                priority=2,
                keywords=["performance", "monitoring", "metrics"]
            )
        ]
        
        for feature in default_features:
            if feature.feature_id not in self.features:
                self.register_feature(feature)
        
        self.logger.debug("Default smart features initialized")
