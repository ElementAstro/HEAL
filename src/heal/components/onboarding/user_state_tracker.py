"""
User State Tracker

Tracks user behavior, preferences, and onboarding progress to provide
intelligent and adaptive user experience.
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import QObject, Signal

from src.heal.common.config_manager import ConfigManager, ConfigType
from src.heal.common.logging_config import get_logger


class UserLevel(Enum):
    """User experience levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class OnboardingStep(Enum):
    """Onboarding steps"""
    WELCOME = "welcome"
    BASIC_SETUP = "basic_setup"
    FEATURE_TOUR = "feature_tour"
    FIRST_SERVER = "first_server"
    CUSTOMIZATION = "customization"
    ADVANCED_FEATURES = "advanced_features"
    COMPLETION = "completion"


class UserStateTracker(QObject):
    """Tracks and manages user state and onboarding progress"""
    
    # Signals
    user_level_changed = Signal(str)  # UserLevel
    onboarding_step_completed = Signal(str)  # OnboardingStep
    first_time_user_detected = Signal()
    returning_user_detected = Signal()
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger("user_state_tracker", module="UserStateTracker")
        self.config_manager = ConfigManager()
        self._user_data: Dict[str, Any] = {}
        self._session_data: Dict[str, Any] = {}
        
        self._load_user_state()
        self._init_session()
    
    def _load_user_state(self) -> None:
        """Load user state from configuration"""
        try:
            user_config = self.config_manager.get_config(ConfigType.USER)
            self._user_data = user_config.get("onboarding", {})
            
            # Ensure all required fields exist
            defaults = {
                "is_first_time": True,
                "completed_steps": [],
                "last_login": None,
                "app_launches": 0,
                "onboarding_version": "1.0.0",
                "user_level": UserLevel.BEGINNER.value,
                "preferred_features": [],
                "skipped_tutorials": [],
                "help_preferences": {
                    "show_tips": True,
                    "show_tooltips": True,
                    "show_contextual_help": True,
                    "tutorial_speed": "normal"
                }
            }
            
            for key, default_value in defaults.items():
                if key not in self._user_data:
                    self._user_data[key] = default_value
            
            self.logger.info(f"User state loaded: {self.get_user_summary()}")
            
        except Exception as e:
            self.logger.error(f"Failed to load user state: {e}")
            self._user_data = {}
    
    def _init_session(self) -> None:
        """Initialize session data"""
        self._session_data = {
            "session_start": datetime.now().isoformat(),
            "actions_taken": [],
            "features_used": set(),
            "help_requests": [],
            "errors_encountered": [],
        }
        
        # Update app launches and last login
        self._user_data["app_launches"] = self._user_data.get("app_launches", 0) + 1
        self._user_data["last_login"] = datetime.now().isoformat()
        
        # Detect first-time vs returning user
        if self._user_data.get("is_first_time", True):
            self.first_time_user_detected.emit()
            self.logger.info("First-time user detected")
        else:
            self.returning_user_detected.emit()
            self.logger.info("Returning user detected")
        
        self._save_user_state()
    
    def _save_user_state(self) -> None:
        """Save user state to configuration"""
        try:
            user_config = self.config_manager.get_config(ConfigType.USER)
            user_config["onboarding"] = self._user_data
            self.config_manager.save_config(ConfigType.USER, user_config)
            self.logger.debug("User state saved")
        except Exception as e:
            self.logger.error(f"Failed to save user state: {e}")
    
    def is_first_time_user(self) -> bool:
        """Check if this is a first-time user"""
        return self._user_data.get("is_first_time", True)
    
    def mark_onboarding_complete(self) -> None:
        """Mark onboarding as complete"""
        self._user_data["is_first_time"] = False
        self.complete_onboarding_step(OnboardingStep.COMPLETION)
        self.logger.info("Onboarding marked as complete")
    
    def get_user_level(self) -> UserLevel:
        """Get current user level"""
        level_str = self._user_data.get("user_level", UserLevel.BEGINNER.value)
        try:
            return UserLevel(level_str)
        except ValueError:
            return UserLevel.BEGINNER
    
    def set_user_level(self, level: UserLevel) -> None:
        """Set user level"""
        old_level = self.get_user_level()
        self._user_data["user_level"] = level.value
        self._save_user_state()
        
        if old_level != level:
            self.user_level_changed.emit(level.value)
            self.logger.info(f"User level changed from {old_level.value} to {level.value}")
    
    def complete_onboarding_step(self, step: OnboardingStep) -> None:
        """Mark an onboarding step as completed"""
        completed_steps = self._user_data.get("completed_steps", [])
        if step.value not in completed_steps:
            completed_steps.append(step.value)
            self._user_data["completed_steps"] = completed_steps
            self._save_user_state()
            self.onboarding_step_completed.emit(step.value)
            self.logger.info(f"Onboarding step completed: {step.value}")
    
    def is_step_completed(self, step: OnboardingStep) -> bool:
        """Check if an onboarding step is completed"""
        completed_steps = self._user_data.get("completed_steps", [])
        return step.value in completed_steps
    
    def get_completed_steps(self) -> List[OnboardingStep]:
        """Get list of completed onboarding steps"""
        completed_steps = self._user_data.get("completed_steps", [])
        return [OnboardingStep(step) for step in completed_steps if step in [s.value for s in OnboardingStep]]
    
    def get_next_onboarding_step(self) -> Optional[OnboardingStep]:
        """Get the next onboarding step to complete"""
        completed_steps = set(self._user_data.get("completed_steps", []))
        
        for step in OnboardingStep:
            if step.value not in completed_steps:
                return step
        
        return None
    
    def track_action(self, action: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Track a user action"""
        action_data = {
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        self._session_data["actions_taken"].append(action_data)
        self.logger.debug(f"Action tracked: {action}")
    
    def track_feature_usage(self, feature: str) -> None:
        """Track feature usage"""
        self._session_data["features_used"].add(feature)
        
        # Update preferred features based on usage
        preferred = self._user_data.get("preferred_features", [])
        if feature not in preferred:
            preferred.append(feature)
            self._user_data["preferred_features"] = preferred
            self._save_user_state()
        
        self.logger.debug(f"Feature usage tracked: {feature}")
    
    def track_help_request(self, help_type: str, context: str) -> None:
        """Track help requests"""
        help_data = {
            "type": help_type,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        self._session_data["help_requests"].append(help_data)
        self.logger.debug(f"Help request tracked: {help_type} in {context}")
    
    def get_help_preferences(self) -> Dict[str, Any]:
        """Get user help preferences"""
        return self._user_data.get("help_preferences", {
            "show_tips": True,
            "show_tooltips": True,
            "show_contextual_help": True,
            "tutorial_speed": "normal"
        })
    
    def update_help_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update help preferences"""
        current_prefs = self.get_help_preferences()
        current_prefs.update(preferences)
        self._user_data["help_preferences"] = current_prefs
        self._save_user_state()
        self.logger.info(f"Help preferences updated: {preferences}")
    
    def should_show_tips(self) -> bool:
        """Check if tips should be shown"""
        return self.get_help_preferences().get("show_tips", True)
    
    def should_show_tooltips(self) -> bool:
        """Check if tooltips should be shown"""
        return self.get_help_preferences().get("show_tooltips", True)
    
    def should_show_contextual_help(self) -> bool:
        """Check if contextual help should be shown"""
        return self.get_help_preferences().get("show_contextual_help", True)
    
    def get_tutorial_speed(self) -> str:
        """Get preferred tutorial speed"""
        return self.get_help_preferences().get("tutorial_speed", "normal")
    
    def skip_tutorial(self, tutorial_id: str) -> None:
        """Mark a tutorial as skipped"""
        skipped = self._user_data.get("skipped_tutorials", [])
        if tutorial_id not in skipped:
            skipped.append(tutorial_id)
            self._user_data["skipped_tutorials"] = skipped
            self._save_user_state()
            self.logger.info(f"Tutorial skipped: {tutorial_id}")
    
    def is_tutorial_skipped(self, tutorial_id: str) -> bool:
        """Check if a tutorial was skipped"""
        skipped = self._user_data.get("skipped_tutorials", [])
        return tutorial_id in skipped
    
    def get_user_summary(self) -> Dict[str, Any]:
        """Get a summary of user state"""
        return {
            "is_first_time": self.is_first_time_user(),
            "user_level": self.get_user_level().value,
            "app_launches": self._user_data.get("app_launches", 0),
            "completed_steps": len(self.get_completed_steps()),
            "total_steps": len(OnboardingStep),
            "preferred_features": len(self._user_data.get("preferred_features", [])),
            "last_login": self._user_data.get("last_login"),
        }
    
    def reset_onboarding(self) -> None:
        """Reset onboarding state (for testing or re-onboarding)"""
        self._user_data.update({
            "is_first_time": True,
            "completed_steps": [],
            "user_level": UserLevel.BEGINNER.value,
            "preferred_features": [],
            "skipped_tutorials": [],
        })
        self._save_user_state()
        self.logger.info("Onboarding state reset")
