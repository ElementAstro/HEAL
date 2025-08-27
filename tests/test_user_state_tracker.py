"""
Comprehensive tests for UserStateTracker component

Tests all aspects of user state management, onboarding progress tracking,
and user behavior analytics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List

from src.heal.components.onboarding.user_state_tracker import (
    UserStateTracker, UserLevel, OnboardingStep
)


class TestUserStateTrackerCore:
    """Test core functionality of UserStateTracker"""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager"""
        with patch('src.heal.common.config_manager.ConfigManager') as mock_cm:
            mock_instance = Mock()
            mock_instance.get_config.return_value = {
                "onboarding": {
                    "is_first_time": True,
                    "completed_steps": [],
                    "last_login": None,
                    "app_launches": 0,
                    "onboarding_version": "1.0.0",
                    "user_level": "beginner",
                    "preferred_features": [],
                    "skipped_tutorials": [],
                    "help_preferences": {
                        "show_tips": True,
                        "show_tooltips": True,
                        "show_contextual_help": True,
                        "tutorial_speed": "normal"
                    }
                }
            }
            mock_cm.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def user_tracker(self, mock_config_manager):
        """Create a UserStateTracker instance for testing"""
        return UserStateTracker()
    
    def test_initialization(self, user_tracker):
        """Test proper initialization of UserStateTracker"""
        assert user_tracker is not None
        assert hasattr(user_tracker, '_user_data')
        assert hasattr(user_tracker, '_session_data')
        assert user_tracker.is_first_time_user() == True
        assert user_tracker.get_user_level() == UserLevel.BEGINNER
    
    def test_first_time_user_detection(self, user_tracker):
        """Test first-time user detection and state changes"""
        # Initially should be first-time user
        assert user_tracker.is_first_time_user() == True
        
        # Mark onboarding complete
        user_tracker.mark_onboarding_complete()
        assert user_tracker.is_first_time_user() == False
        
        # Should have completion step marked
        completed_steps = user_tracker.get_completed_steps()
        assert OnboardingStep.COMPLETION in completed_steps
    
    def test_user_level_management(self, user_tracker):
        """Test user level management and transitions"""
        # Test initial level
        assert user_tracker.get_user_level() == UserLevel.BEGINNER
        
        # Test level progression
        user_tracker.set_user_level(UserLevel.INTERMEDIATE)
        assert user_tracker.get_user_level() == UserLevel.INTERMEDIATE
        
        user_tracker.set_user_level(UserLevel.ADVANCED)
        assert user_tracker.get_user_level() == UserLevel.ADVANCED
        
        # Test invalid level handling
        user_tracker._user_data["user_level"] = "invalid_level"
        assert user_tracker.get_user_level() == UserLevel.BEGINNER  # Should fallback
    
    def test_onboarding_step_progression(self, user_tracker):
        """Test onboarding step completion and progression"""
        # Initially no steps completed
        assert len(user_tracker.get_completed_steps()) == 0
        
        # Complete steps in order
        steps_to_complete = [
            OnboardingStep.WELCOME,
            OnboardingStep.BASIC_SETUP,
            OnboardingStep.FEATURE_TOUR,
            OnboardingStep.FIRST_SERVER,
            OnboardingStep.CUSTOMIZATION
        ]
        
        for i, step in enumerate(steps_to_complete):
            user_tracker.complete_onboarding_step(step)
            completed = user_tracker.get_completed_steps()
            assert len(completed) == i + 1
            assert step in completed
            assert user_tracker.is_step_completed(step) == True
        
        # Test next step calculation
        next_step = user_tracker.get_next_onboarding_step()
        assert next_step == OnboardingStep.ADVANCED_FEATURES
    
    def test_action_tracking(self, user_tracker):
        """Test user action tracking functionality"""
        # Track various actions
        actions = [
            ("login", {"timestamp": datetime.now().isoformat()}),
            ("navigate_home", {"page": "home"}),
            ("start_server", {"server_id": "test_server"}),
            ("view_logs", {"server_id": "test_server"}),
        ]
        
        for action, context in actions:
            user_tracker.track_action(action, context)
        
        # Verify session data is updated
        assert len(user_tracker._session_data["actions_taken"]) == len(actions)
        
        # Verify action data structure
        for i, (action, context) in enumerate(actions):
            action_data = user_tracker._session_data["actions_taken"][i]
            assert action_data["action"] == action
            assert action_data["context"] == context
            assert "timestamp" in action_data
    
    def test_feature_usage_tracking(self, user_tracker):
        """Test feature usage tracking and preferred features"""
        features = ["server_management", "log_viewer", "module_downloader", "settings"]
        
        # Track feature usage
        for feature in features:
            user_tracker.track_feature_usage(feature)
        
        # Verify features are tracked
        assert len(user_tracker._session_data["features_used"]) == len(features)
        for feature in features:
            assert feature in user_tracker._session_data["features_used"]
        
        # Verify preferred features are updated
        preferred = user_tracker._user_data.get("preferred_features", [])
        for feature in features:
            assert feature in preferred
    
    def test_help_request_tracking(self, user_tracker):
        """Test help request tracking"""
        help_requests = [
            ("tooltip", "server_card"),
            ("tutorial", "first_setup"),
            ("documentation", "api_reference"),
            ("contextual_help", "error_dialog")
        ]
        
        for help_type, context in help_requests:
            user_tracker.track_help_request(help_type, context)
        
        # Verify help requests are tracked
        session_help = user_tracker._session_data["help_requests"]
        assert len(session_help) == len(help_requests)
        
        for i, (help_type, context) in enumerate(help_requests):
            request_data = session_help[i]
            assert request_data["type"] == help_type
            assert request_data["context"] == context
            assert "timestamp" in request_data


class TestUserStateTrackerPreferences:
    """Test user preferences management"""
    
    @pytest.fixture
    def user_tracker(self):
        """Create a UserStateTracker instance for testing"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            return UserStateTracker()
    
    def test_help_preferences_default(self, user_tracker):
        """Test default help preferences"""
        prefs = user_tracker.get_help_preferences()
        
        assert prefs["show_tips"] == True
        assert prefs["show_tooltips"] == True
        assert prefs["show_contextual_help"] == True
        assert prefs["tutorial_speed"] == "normal"
    
    def test_help_preferences_update(self, user_tracker):
        """Test updating help preferences"""
        new_prefs = {
            "show_tips": False,
            "tutorial_speed": "fast"
        }
        
        user_tracker.update_help_preferences(new_prefs)
        
        # Verify preferences are updated
        prefs = user_tracker.get_help_preferences()
        assert prefs["show_tips"] == False
        assert prefs["tutorial_speed"] == "fast"
        # Other preferences should remain unchanged
        assert prefs["show_tooltips"] == True
        assert prefs["show_contextual_help"] == True
    
    def test_preference_convenience_methods(self, user_tracker):
        """Test convenience methods for checking preferences"""
        # Test default values
        assert user_tracker.should_show_tips() == True
        assert user_tracker.should_show_tooltips() == True
        assert user_tracker.should_show_contextual_help() == True
        assert user_tracker.get_tutorial_speed() == "normal"
        
        # Update preferences and test again
        user_tracker.update_help_preferences({
            "show_tips": False,
            "show_tooltips": False,
            "tutorial_speed": "slow"
        })
        
        assert user_tracker.should_show_tips() == False
        assert user_tracker.should_show_tooltips() == False
        assert user_tracker.should_show_contextual_help() == True  # Not changed
        assert user_tracker.get_tutorial_speed() == "slow"


class TestUserStateTrackerTutorials:
    """Test tutorial-related functionality"""
    
    @pytest.fixture
    def user_tracker(self):
        """Create a UserStateTracker instance for testing"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            return UserStateTracker()
    
    def test_tutorial_skipping(self, user_tracker):
        """Test tutorial skipping functionality"""
        tutorials = ["welcome_tutorial", "feature_tour", "advanced_setup"]
        
        # Skip tutorials
        for tutorial in tutorials:
            user_tracker.skip_tutorial(tutorial)
        
        # Verify tutorials are marked as skipped
        for tutorial in tutorials:
            assert user_tracker.is_tutorial_skipped(tutorial) == True
        
        # Verify non-skipped tutorial
        assert user_tracker.is_tutorial_skipped("non_existent_tutorial") == False
    
    def test_tutorial_skip_deduplication(self, user_tracker):
        """Test that skipping the same tutorial multiple times doesn't duplicate entries"""
        tutorial_id = "test_tutorial"
        
        # Skip the same tutorial multiple times
        for _ in range(3):
            user_tracker.skip_tutorial(tutorial_id)
        
        # Should only appear once in skipped list
        skipped = user_tracker._user_data.get("skipped_tutorials", [])
        assert skipped.count(tutorial_id) == 1


class TestUserStateTrackerAnalytics:
    """Test analytics and summary functionality"""
    
    @pytest.fixture
    def user_tracker(self):
        """Create a UserStateTracker instance for testing"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            return UserStateTracker()
    
    def test_user_summary(self, user_tracker):
        """Test user summary generation"""
        # Complete some steps and track some activity
        user_tracker.complete_onboarding_step(OnboardingStep.WELCOME)
        user_tracker.complete_onboarding_step(OnboardingStep.BASIC_SETUP)
        user_tracker.track_feature_usage("server_management")
        user_tracker.track_feature_usage("log_viewer")
        
        summary = user_tracker.get_user_summary()
        
        # Verify summary structure and content
        assert "is_first_time" in summary
        assert "user_level" in summary
        assert "app_launches" in summary
        assert "completed_steps" in summary
        assert "total_steps" in summary
        assert "preferred_features" in summary
        assert "last_login" in summary
        
        # Verify specific values
        assert summary["is_first_time"] == True
        assert summary["user_level"] == "beginner"
        assert summary["completed_steps"] == 2
        assert summary["total_steps"] == len(OnboardingStep)
        assert summary["preferred_features"] == 2
    
    def test_onboarding_reset(self, user_tracker):
        """Test onboarding state reset functionality"""
        # Set up some state
        user_tracker.complete_onboarding_step(OnboardingStep.WELCOME)
        user_tracker.set_user_level(UserLevel.INTERMEDIATE)
        user_tracker.track_feature_usage("test_feature")
        user_tracker.skip_tutorial("test_tutorial")
        
        # Verify state is set
        assert len(user_tracker.get_completed_steps()) > 0
        assert user_tracker.get_user_level() == UserLevel.INTERMEDIATE
        assert len(user_tracker._user_data.get("preferred_features", [])) > 0
        assert len(user_tracker._user_data.get("skipped_tutorials", [])) > 0
        
        # Reset onboarding
        user_tracker.reset_onboarding()
        
        # Verify state is reset
        assert user_tracker.is_first_time_user() == True
        assert len(user_tracker.get_completed_steps()) == 0
        assert user_tracker.get_user_level() == UserLevel.BEGINNER
        assert len(user_tracker._user_data.get("preferred_features", [])) == 0
        assert len(user_tracker._user_data.get("skipped_tutorials", [])) == 0


class TestUserStateTrackerPersistence:
    """Test data persistence and configuration management"""
    
    def test_configuration_save_calls(self):
        """Test that configuration is saved when state changes"""
        with patch('src.heal.common.config_manager.ConfigManager') as mock_cm:
            mock_instance = Mock()
            mock_instance.get_config.return_value = {"onboarding": {}}
            mock_cm.return_value = mock_instance
            
            user_tracker = UserStateTracker()
            
            # Perform operations that should trigger saves
            user_tracker.set_user_level(UserLevel.INTERMEDIATE)
            user_tracker.complete_onboarding_step(OnboardingStep.WELCOME)
            user_tracker.update_help_preferences({"show_tips": False})
            
            # Verify save_config was called
            assert mock_instance.save_config.call_count >= 3
    
    def test_configuration_load_error_handling(self):
        """Test handling of configuration load errors"""
        with patch('src.heal.common.config_manager.ConfigManager') as mock_cm:
            mock_instance = Mock()
            mock_instance.get_config.side_effect = Exception("Config load error")
            mock_cm.return_value = mock_instance
            
            # Should not raise exception
            user_tracker = UserStateTracker()
            
            # Should have empty user data
            assert user_tracker._user_data == {}
    
    def test_configuration_save_error_handling(self):
        """Test handling of configuration save errors"""
        with patch('src.heal.common.config_manager.ConfigManager') as mock_cm:
            mock_instance = Mock()
            mock_instance.get_config.return_value = {"onboarding": {}}
            mock_instance.save_config.side_effect = Exception("Save error")
            mock_cm.return_value = mock_instance
            
            user_tracker = UserStateTracker()
            
            # Should not raise exception when save fails
            user_tracker.set_user_level(UserLevel.INTERMEDIATE)


class TestUserStateTrackerEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.fixture
    def user_tracker(self):
        """Create a UserStateTracker instance for testing"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            return UserStateTracker()
    
    def test_invalid_onboarding_step(self, user_tracker):
        """Test handling of invalid onboarding steps"""
        # This should not raise an exception
        user_tracker.complete_onboarding_step("invalid_step")
        
        # Should not affect completed steps
        completed = user_tracker.get_completed_steps()
        assert len(completed) == 0
    
    def test_duplicate_step_completion(self, user_tracker):
        """Test completing the same step multiple times"""
        step = OnboardingStep.WELCOME
        
        # Complete the same step multiple times
        for _ in range(3):
            user_tracker.complete_onboarding_step(step)
        
        # Should only appear once in completed steps
        completed = user_tracker.get_completed_steps()
        assert completed.count(step) == 1
    
    def test_empty_action_tracking(self, user_tracker):
        """Test tracking actions with empty or None values"""
        # These should not raise exceptions
        user_tracker.track_action("", None)
        user_tracker.track_action(None, {})
        user_tracker.track_feature_usage("")
        user_tracker.track_help_request("", "")
    
    def test_session_data_initialization(self, user_tracker):
        """Test session data is properly initialized"""
        session_data = user_tracker._session_data
        
        assert "session_start" in session_data
        assert "actions_taken" in session_data
        assert "features_used" in session_data
        assert "help_requests" in session_data
        assert "errors_encountered" in session_data
        
        # Verify data types
        assert isinstance(session_data["actions_taken"], list)
        assert isinstance(session_data["features_used"], set)
        assert isinstance(session_data["help_requests"], list)
        assert isinstance(session_data["errors_encountered"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
