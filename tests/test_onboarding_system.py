"""
Test suite for the enhanced onboarding system

Tests the user onboarding, smart tips, contextual help, and progressive
feature discovery systems.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QObject

from src.heal.components.onboarding.user_state_tracker import (
    UserStateTracker, UserLevel, OnboardingStep
)
from src.heal.components.onboarding.onboarding_manager import OnboardingManager
from src.heal.components.onboarding.smart_features import (
    SmartFeaturesManager, SmartTipSystem, RecommendationEngine,
    ProgressiveFeatureDiscovery, SmartFeatureType, FeatureCategory
)
from src.heal.components.onboarding.help_system import (
    HelpSystem, ContextualHelpSystem, DocumentationIntegration,
    HelpType, HelpPriority
)


class TestUserStateTracker:
    """Test the user state tracking system"""
    
    @pytest.fixture
    def user_tracker(self):
        """Create a user state tracker for testing"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            tracker = UserStateTracker()
            return tracker
    
    def test_first_time_user_detection(self, user_tracker):
        """Test first-time user detection"""
        assert user_tracker.is_first_time_user() == True
        
        user_tracker.mark_onboarding_complete()
        assert user_tracker.is_first_time_user() == False
    
    def test_user_level_management(self, user_tracker):
        """Test user level management"""
        # Default level should be beginner
        assert user_tracker.get_user_level() == UserLevel.BEGINNER
        
        # Test level change
        user_tracker.set_user_level(UserLevel.INTERMEDIATE)
        assert user_tracker.get_user_level() == UserLevel.INTERMEDIATE
    
    def test_onboarding_step_tracking(self, user_tracker):
        """Test onboarding step tracking"""
        # Initially no steps completed
        assert len(user_tracker.get_completed_steps()) == 0
        
        # Complete a step
        user_tracker.complete_onboarding_step(OnboardingStep.WELCOME)
        completed = user_tracker.get_completed_steps()
        assert OnboardingStep.WELCOME in completed
        
        # Check if step is completed
        assert user_tracker.is_step_completed(OnboardingStep.WELCOME) == True
        assert user_tracker.is_step_completed(OnboardingStep.BASIC_SETUP) == False
    
    def test_action_tracking(self, user_tracker):
        """Test action tracking"""
        user_tracker.track_action("test_action", {"context": "test"})
        user_tracker.track_feature_usage("test_feature")
        user_tracker.track_help_request("tooltip", "home")
        
        # These should not raise exceptions
        assert True
    
    def test_help_preferences(self, user_tracker):
        """Test help preferences management"""
        # Default preferences
        prefs = user_tracker.get_help_preferences()
        assert prefs["show_tips"] == True
        assert prefs["show_tooltips"] == True
        
        # Update preferences
        user_tracker.update_help_preferences({"show_tips": False})
        assert user_tracker.should_show_tips() == False
        assert user_tracker.should_show_tooltips() == True


class TestSmartTipSystem:
    """Test the smart tip system"""
    
    @pytest.fixture
    def mock_user_tracker(self):
        """Create a mock user tracker"""
        tracker = Mock(spec=UserStateTracker)
        tracker.get_user_level.return_value = UserLevel.BEGINNER
        tracker.should_show_tips.return_value = True
        return tracker
    
    @pytest.fixture
    def tip_system(self, mock_user_tracker):
        """Create a smart tip system for testing"""
        return SmartTipSystem(mock_user_tracker)
    
    def test_tip_initialization(self, tip_system):
        """Test tip system initialization"""
        assert len(tip_system.tips) > 0
        assert TipContext.GENERAL in [tip.context for tip in tip_system.tips.values()]
    
    def test_context_switching(self, tip_system):
        """Test context switching"""
        tip_system.set_context(TipContext.HOME)
        assert tip_system.current_context == TipContext.HOME
        
        tip_system.set_context(TipContext.LAUNCHER)
        assert tip_system.current_context == TipContext.LAUNCHER
    
    def test_action_tracking(self, tip_system):
        """Test action-based tip triggering"""
        # Track an action that should trigger tips
        tip_system.track_action("connection_failed")
        
        # Should have triggered some processing
        assert "connection_failed" in tip_system.completed_actions
    
    def test_tip_rotation(self, tip_system):
        """Test tip rotation functionality"""
        tip_system.start_rotation(1000)  # 1 second interval
        assert tip_system.rotation_timer.isActive()
        
        tip_system.stop_rotation()
        assert not tip_system.rotation_timer.isActive()


class TestContextualHelpSystem:
    """Test the contextual help system"""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window"""
        return Mock(spec=QWidget)
    
    @pytest.fixture
    def mock_onboarding_manager(self):
        """Create a mock onboarding manager"""
        manager = Mock()
        manager.get_user_state_tracker.return_value = Mock(spec=UserStateTracker)
        manager.get_user_state_tracker.return_value.get_user_level.return_value = UserLevel.BEGINNER
        manager.get_user_state_tracker.return_value.should_show_contextual_help.return_value = True
        return manager
    
    @pytest.fixture
    def help_system(self, mock_main_window, mock_onboarding_manager):
        """Create a contextual help system for testing"""
        return ContextualHelpSystem(mock_main_window, mock_onboarding_manager)
    
    def test_help_initialization(self, help_system):
        """Test help system initialization"""
        assert len(help_system.help_items) > 0
        assert any(item.help_type == HelpType.TOOLTIP for item in help_system.help_items.values())
    
    def test_widget_help_registration(self, help_system):
        """Test widget help registration"""
        mock_widget = Mock(spec=QWidget)
        help_ids = ["test_help_1", "test_help_2"]
        
        help_system.register_widget_help(mock_widget, help_ids)
        assert mock_widget in help_system.widget_help_map
        assert help_system.widget_help_map[mock_widget] == help_ids
    
    def test_contextual_help_display(self, help_system):
        """Test contextual help display"""
        # This should not raise exceptions
        help_system.show_contextual_help("home")
        help_system.show_contextual_help("launcher")
    
    def test_error_help(self, help_system):
        """Test error-specific help"""
        help_system.show_help_for_error("connection_error", "home")
        help_system.show_help_for_error("performance_issue", "general")


class TestProgressiveFeatureDiscovery:
    """Test the progressive feature discovery system"""
    
    @pytest.fixture
    def mock_user_tracker(self):
        """Create a mock user tracker"""
        tracker = Mock(spec=UserStateTracker)
        tracker.get_user_level.return_value = UserLevel.BEGINNER
        return tracker
    
    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window"""
        return Mock(spec=QWidget)
    
    @pytest.fixture
    def discovery_system(self, mock_user_tracker, mock_main_window):
        """Create a feature discovery system for testing"""
        return ProgressiveFeatureDiscovery(mock_user_tracker, mock_main_window)
    
    def test_feature_initialization(self, discovery_system):
        """Test feature initialization"""
        assert len(discovery_system.features) > 0
        assert any(f.category == FeatureCategory.BASIC for f in discovery_system.features.values())
        assert any(f.category == FeatureCategory.ADVANCED for f in discovery_system.features.values())
    
    def test_context_switching(self, discovery_system):
        """Test context switching"""
        discovery_system.set_context("home")
        assert discovery_system.current_context == "home"
    
    def test_action_tracking(self, discovery_system):
        """Test action-based feature discovery"""
        discovery_system.track_action("server_card_clicked")
        discovery_system.track_usage_metric("servers_started", 1)
    
    def test_discovery_progress(self, discovery_system):
        """Test discovery progress tracking"""
        progress = discovery_system.get_discovery_progress()
        
        assert "total_features" in progress
        assert "discovered_features" in progress
        assert "discovery_percentage" in progress
        assert "category_progress" in progress


class TestOnboardingManager:
    """Test the main onboarding manager"""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window"""
        return Mock(spec=QWidget)
    
    @pytest.fixture
    def onboarding_manager(self, mock_main_window):
        """Create an onboarding manager for testing"""
        with patch('src.heal.components.onboarding.user_state_tracker.UserStateTracker'):
            manager = OnboardingManager(mock_main_window)
            return manager
    
    def test_manager_initialization(self, onboarding_manager):
        """Test onboarding manager initialization"""
        assert onboarding_manager.user_tracker is not None
        assert onboarding_manager.main_window is not None
    
    def test_welcome_wizard_request(self, onboarding_manager):
        """Test welcome wizard request"""
        # Should not raise exceptions
        onboarding_manager.start_welcome_wizard()
    
    def test_tutorial_request(self, onboarding_manager):
        """Test tutorial request"""
        # Should not raise exceptions
        onboarding_manager.start_tutorial("feature_tour")
    
    def test_onboarding_progress(self, onboarding_manager):
        """Test onboarding progress tracking"""
        progress = onboarding_manager.get_onboarding_progress()
        
        assert "current_step" in progress
        assert "completed_steps" in progress
        assert "progress_percentage" in progress
        assert "is_active" in progress
        assert "user_level" in progress


class TestIntegration:
    """Integration tests for the complete onboarding system"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    def test_full_onboarding_flow(self, main_window):
        """Test the complete onboarding flow"""
        with patch('src.heal.components.onboarding.user_state_tracker.UserStateTracker') as mock_tracker_class:
            # Setup mock
            mock_tracker = Mock(spec=UserStateTracker)
            mock_tracker.is_first_time_user.return_value = True
            mock_tracker.get_user_level.return_value = UserLevel.BEGINNER
            mock_tracker.get_next_onboarding_step.return_value = OnboardingStep.WELCOME
            mock_tracker.should_show_tips.return_value = True
            mock_tracker.should_show_contextual_help.return_value = True
            mock_tracker_class.return_value = mock_tracker
            
            # Create onboarding manager
            manager = OnboardingManager(main_window)
            
            # Test first-time user flow
            assert manager.user_tracker.is_first_time_user() == True
            
            # Test step completion
            manager.complete_current_step()
            
            # Test progress tracking
            progress = manager.get_onboarding_progress()
            assert progress is not None
    
    def test_returning_user_flow(self, main_window):
        """Test the returning user flow"""
        with patch('src.heal.components.onboarding.user_state_tracker.UserStateTracker') as mock_tracker_class:
            # Setup mock for returning user
            mock_tracker = Mock(spec=UserStateTracker)
            mock_tracker.is_first_time_user.return_value = False
            mock_tracker.get_user_level.return_value = UserLevel.INTERMEDIATE
            mock_tracker.should_show_tips.return_value = True
            mock_tracker_class.return_value = mock_tracker
            
            # Create onboarding manager
            manager = OnboardingManager(main_window)
            
            # Test returning user flow
            assert manager.user_tracker.is_first_time_user() == False
    
    def test_user_level_progression(self, main_window):
        """Test user level progression"""
        with patch('src.heal.components.onboarding.user_state_tracker.UserStateTracker') as mock_tracker_class:
            mock_tracker = Mock(spec=UserStateTracker)
            mock_tracker.get_user_level.return_value = UserLevel.BEGINNER
            mock_tracker_class.return_value = mock_tracker
            
            manager = OnboardingManager(main_window)
            
            # Simulate user level change
            mock_tracker.get_user_level.return_value = UserLevel.INTERMEDIATE
            manager._handle_user_level_changed(UserLevel.INTERMEDIATE.value)
            
            # Should not raise exceptions
            assert True


class TestRecommendationEngine:
    """Test the recommendation engine"""

    @pytest.fixture
    def mock_user_tracker(self):
        """Create a mock user tracker"""
        tracker = Mock(spec=UserStateTracker)
        tracker.get_user_level.return_value = UserLevel.BEGINNER
        return tracker

    @pytest.fixture
    def recommendation_engine(self, mock_user_tracker):
        """Create a recommendation engine for testing"""
        return RecommendationEngine(mock_user_tracker)

    def test_engine_initialization(self, recommendation_engine):
        """Test recommendation engine initialization"""
        assert len(recommendation_engine.recommendation_templates) > 0
        assert recommendation_engine.analysis_timer.isActive()

    def test_action_tracking(self, recommendation_engine):
        """Test action tracking and recommendation generation"""
        recommendation_engine.track_user_action("visited_home_page")
        recommendation_engine.track_system_state({"cpu_usage": 85})
        recommendation_engine.track_error("connection_error", {"context": "test"})

        # Should not raise exceptions
        assert True

    def test_recommendation_lifecycle(self, recommendation_engine):
        """Test recommendation lifecycle"""
        # Generate a recommendation
        rec = recommendation_engine._generate_recommendation("setup_first_server")

        if rec:
            rec_id = rec.rec_id

            # Test showing recommendation
            assert recommendation_engine.show_recommendation(rec_id) == True

            # Test accepting recommendation
            assert recommendation_engine.accept_recommendation(rec_id) == True

            # Test dismissing recommendation
            assert recommendation_engine.dismiss_recommendation(rec_id) == True

    def test_recommendation_statistics(self, recommendation_engine):
        """Test recommendation statistics"""
        stats = recommendation_engine.get_recommendation_statistics()

        assert "total_recommendations" in stats
        assert "active_recommendations" in stats
        assert "acceptance_rate" in stats


class TestDocumentationIntegration:
    """Test the documentation integration system"""

    @pytest.fixture
    def mock_user_tracker(self):
        """Create a mock user tracker"""
        tracker = Mock(spec=UserStateTracker)
        tracker.get_user_level.return_value = UserLevel.BEGINNER
        return tracker

    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window"""
        return Mock(spec=QWidget)

    @pytest.fixture
    def docs_integration(self, mock_user_tracker, mock_main_window):
        """Create a documentation integration for testing"""
        return DocumentationIntegration(mock_user_tracker, mock_main_window)

    def test_docs_initialization(self, docs_integration):
        """Test documentation system initialization"""
        assert len(docs_integration.documentation_items) > 0
        assert len(docs_integration.search_index) > 0
        assert len(docs_integration.context_mapping) > 0

    def test_documentation_search(self, docs_integration):
        """Test documentation search"""
        results = docs_integration.search_documentation("server setup")
        assert isinstance(results, list)

        results = docs_integration.search_documentation("configuration")
        assert isinstance(results, list)

    def test_contextual_documentation(self, docs_integration):
        """Test contextual documentation"""
        docs = docs_integration.get_contextual_documentation("home")
        assert isinstance(docs, list)

        docs = docs_integration.get_contextual_documentation("launcher")
        assert isinstance(docs, list)

    def test_documentation_recommendations(self, docs_integration):
        """Test documentation recommendations"""
        recommendations = docs_integration.get_recommended_documentation()
        assert isinstance(recommendations, list)

    def test_error_documentation_suggestions(self, docs_integration):
        """Test error-specific documentation suggestions"""
        suggestions = docs_integration.suggest_documentation_for_error(
            "connection_error", "test context"
        )
        assert isinstance(suggestions, list)


class TestCompleteOnboardingSystem:
    """Integration tests for the complete enhanced onboarding system"""

    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])

    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()

    def test_complete_system_initialization(self, main_window):
        """Test complete system initialization"""
        with patch('src.heal.components.onboarding.user_state_tracker.UserStateTracker') as mock_tracker_class:
            # Setup comprehensive mock
            mock_tracker = Mock(spec=UserStateTracker)
            mock_tracker.is_first_time_user.return_value = True
            mock_tracker.get_user_level.return_value = UserLevel.BEGINNER
            mock_tracker.get_next_onboarding_step.return_value = OnboardingStep.WELCOME
            mock_tracker.should_show_tips.return_value = True
            mock_tracker.should_show_contextual_help.return_value = True
            mock_tracker.get_user_summary.return_value = {
                "is_first_time": True,
                "user_level": "beginner",
                "app_launches": 1
            }
            mock_tracker_class.return_value = mock_tracker

            # Create complete onboarding manager
            manager = OnboardingManager(main_window)

            # Initialize all systems
            manager.initialize_all_systems()

            # Test comprehensive functionality
            assert manager.user_tracker is not None
            assert manager._smart_tip_system is not None
            assert manager._recommendation_engine is not None
            assert manager._feature_discovery is not None
            assert manager._documentation_integration is not None

    def test_user_journey_simulation(self, main_window):
        """Test complete user journey simulation"""
        with patch('src.heal.components.onboarding.user_state_tracker.UserStateTracker') as mock_tracker_class:
            mock_tracker = Mock(spec=UserStateTracker)
            mock_tracker.is_first_time_user.return_value = True
            mock_tracker.get_user_level.return_value = UserLevel.BEGINNER
            mock_tracker.get_next_onboarding_step.return_value = OnboardingStep.WELCOME
            mock_tracker.should_show_tips.return_value = True
            mock_tracker.should_show_contextual_help.return_value = True
            mock_tracker_class.return_value = mock_tracker

            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()

            # Simulate user journey
            # 1. First-time user starts onboarding
            manager.start_welcome_wizard()

            # 2. User completes welcome step
            manager.complete_current_step()

            # 3. User performs actions
            manager.track_user_action("visited_home_page")
            manager.track_user_action("server_card_clicked")

            # 4. System provides recommendations
            recommendations = manager.get_recommendations()
            assert isinstance(recommendations, list)

            # 5. User searches for help
            docs = manager.search_documentation("server setup")
            assert isinstance(docs, list)

            # 6. User progresses through onboarding
            progress = manager.get_onboarding_progress()
            assert "progress_percentage" in progress

            # 7. Get comprehensive statistics
            stats = manager.get_comprehensive_statistics()
            assert "user_state" in stats
            assert "onboarding_progress" in stats

    def test_error_handling_and_recovery(self, main_window):
        """Test error handling and recovery mechanisms"""
        with patch('src.heal.components.onboarding.user_state_tracker.UserStateTracker') as mock_tracker_class:
            mock_tracker = Mock(spec=UserStateTracker)
            mock_tracker.get_user_level.return_value = UserLevel.INTERMEDIATE
            mock_tracker_class.return_value = mock_tracker

            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()

            # Simulate various error scenarios
            manager.track_error("connection_error", {"server": "test", "port": 8080})
            manager.track_error("performance_issue", {"cpu": 90, "memory": 85})
            manager.track_error("configuration_error", {"setting": "proxy"})

            # System should handle errors gracefully
            recommendations = manager.get_recommendations()
            assert isinstance(recommendations, list)

    def test_system_shutdown(self, main_window):
        """Test system shutdown and cleanup"""
        with patch('src.heal.components.onboarding.user_state_tracker.UserStateTracker') as mock_tracker_class:
            mock_tracker = Mock(spec=UserStateTracker)
            mock_tracker.get_user_level.return_value = UserLevel.ADVANCED
            mock_tracker_class.return_value = mock_tracker

            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()

            # Test shutdown
            manager.shutdown_all_systems()

            # Should complete without errors
            assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
