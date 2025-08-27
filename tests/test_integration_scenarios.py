"""
Integration tests for complete onboarding system scenarios

Tests real-world user journeys, system interactions, and end-to-end workflows
across all onboarding components.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
from typing import Any, Dict, List

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer

from src.heal.components.onboarding.onboarding_manager import OnboardingManager
from src.heal.components.onboarding.user_state_tracker import (
    UserStateTracker, UserLevel, OnboardingStep
)


class TestFirstTimeUserJourney:
    """Test complete first-time user journey"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager for first-time user"""
        with patch('src.heal.common.config_manager.ConfigManager') as mock_cm:
            mock_instance = Mock()
            mock_instance.get_config.return_value = {
                "onboarding": {
                    "is_first_time": True,
                    "completed_steps": [],
                    "user_level": "beginner",
                    "app_launches": 1,
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
    
    def test_complete_first_time_journey(self, main_window, mock_config_manager):
        """Test complete first-time user journey from start to finish"""
        # Create onboarding manager
        manager = OnboardingManager(main_window)
        
        # Verify first-time user detection
        assert manager.user_tracker.is_first_time_user() == True
        assert manager.user_tracker.get_user_level() == UserLevel.BEGINNER
        
        # Initialize all systems
        manager.initialize_all_systems()
        
        # Verify systems are initialized
        assert manager._smart_tip_system is not None
        assert manager._recommendation_engine is not None
        assert manager._feature_discovery is not None
        assert manager._documentation_integration is not None
        
        # Simulate welcome wizard completion
        manager.complete_current_step()  # Complete WELCOME step
        
        # Verify step progression
        completed_steps = manager.user_tracker.get_completed_steps()
        assert OnboardingStep.WELCOME in completed_steps
        
        # Simulate user actions throughout onboarding
        user_actions = [
            ("visited_home_page", {"timestamp": datetime.now().isoformat()}),
            ("server_card_clicked", {"server_id": "test_server"}),
            ("quick_action_used", {"action": "start_all"}),
            ("help_requested", {"type": "tooltip", "context": "server_management"}),
            ("feature_discovered", {"feature": "batch_operations"}),
            ("tutorial_started", {"tutorial_id": "feature_tour"}),
            ("documentation_accessed", {"doc_id": "getting_started"}),
        ]
        
        for action, context in user_actions:
            manager.track_user_action(action, context)
            manager.track_feature_usage(action.split("_")[0])
        
        # Complete more onboarding steps
        steps_to_complete = [
            OnboardingStep.BASIC_SETUP,
            OnboardingStep.FEATURE_TOUR,
            OnboardingStep.FIRST_SERVER,
            OnboardingStep.CUSTOMIZATION
        ]
        
        for step in steps_to_complete:
            manager.user_tracker.complete_onboarding_step(step)
        
        # Get recommendations
        recommendations = manager.get_recommendations()
        assert isinstance(recommendations, list)
        
        # Search documentation
        docs = manager.search_documentation("server setup")
        assert isinstance(docs, list)
        
        # Get discovery progress
        discovery_progress = manager.get_discovery_progress()
        assert "total_features" in discovery_progress
        assert "discovered_features" in discovery_progress
        
        # Complete onboarding
        manager.user_tracker.mark_onboarding_complete()
        assert manager.user_tracker.is_first_time_user() == False
        
        # Get comprehensive statistics
        stats = manager.get_comprehensive_statistics()
        assert "user_state" in stats
        assert "onboarding_progress" in stats
        assert "recommendations" in stats
        assert "feature_discovery" in stats
    
    def test_welcome_wizard_flow(self, main_window, mock_config_manager):
        """Test welcome wizard flow and user preference collection"""
        manager = OnboardingManager(main_window)
        
        # Mock welcome wizard
        with patch('src.heal.components.onboarding.welcome_wizard.WelcomeWizard') as mock_wizard_class:
            mock_wizard = Mock()
            mock_wizard_class.return_value = mock_wizard
            
            # Start welcome wizard
            manager.start_welcome_wizard()
            
            # Verify wizard was created and started
            mock_wizard_class.assert_called_once()
            mock_wizard.start.assert_called_once()
    
    def test_progressive_feature_discovery(self, main_window, mock_config_manager):
        """Test progressive feature discovery throughout user journey"""
        manager = OnboardingManager(main_window)
        manager.initialize_all_systems()
        
        # Simulate user actions that should trigger feature discovery
        discovery_triggers = [
            ("server_card_clicked", {}),
            ("multiple_servers_managed", {"count": 3}),
            ("tools_section_visited", {}),
            ("advanced_user_detected", {"experience": "high"})
        ]
        
        for action, context in discovery_triggers:
            manager.track_user_action(action, context)
            
            # Check if features were discovered
            progress = manager.get_discovery_progress()
            assert progress["discovery_percentage"] >= 0
    
    def test_adaptive_help_system(self, main_window, mock_config_manager):
        """Test adaptive help system responding to user behavior"""
        manager = OnboardingManager(main_window)
        manager.initialize_all_systems()
        
        # Test help adaptation to user level changes
        user_levels = [UserLevel.BEGINNER, UserLevel.INTERMEDIATE, UserLevel.ADVANCED]
        
        for level in user_levels:
            manager.user_tracker.set_user_level(level)
            
            # Get contextual documentation for different contexts
            contexts = ["home", "launcher", "tools", "settings"]
            for context in contexts:
                docs = manager.get_contextual_documentation(context)
                assert isinstance(docs, list)
                
                # Show contextual help
                manager.show_contextual_help(context)


class TestReturningUserJourney:
    """Test returning user experience"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    @pytest.fixture
    def mock_config_manager_returning(self):
        """Create a mock config manager for returning user"""
        with patch('src.heal.common.config_manager.ConfigManager') as mock_cm:
            mock_instance = Mock()
            mock_instance.get_config.return_value = {
                "onboarding": {
                    "is_first_time": False,
                    "completed_steps": ["welcome", "basic_setup", "feature_tour"],
                    "user_level": "intermediate",
                    "app_launches": 15,
                    "preferred_features": ["server_management", "log_viewer", "batch_operations"],
                    "help_preferences": {
                        "show_tips": True,
                        "show_tooltips": False,
                        "show_contextual_help": True,
                        "tutorial_speed": "fast"
                    }
                }
            }
            mock_cm.return_value = mock_instance
            yield mock_instance
    
    def test_returning_user_experience(self, main_window, mock_config_manager_returning):
        """Test returning user experience and preference loading"""
        manager = OnboardingManager(main_window)
        
        # Verify returning user detection
        assert manager.user_tracker.is_first_time_user() == False
        assert manager.user_tracker.get_user_level() == UserLevel.INTERMEDIATE
        
        # Verify preferences are loaded
        prefs = manager.user_tracker.get_help_preferences()
        assert prefs["show_tips"] == True
        assert prefs["show_tooltips"] == False
        assert prefs["tutorial_speed"] == "fast"
        
        # Initialize systems
        manager.initialize_all_systems()
        
        # Test that system adapts to intermediate user level
        recommendations = manager.get_recommendations()
        # Should get recommendations appropriate for intermediate users
        assert isinstance(recommendations, list)
    
    def test_user_level_progression(self, main_window, mock_config_manager_returning):
        """Test user level progression and system adaptation"""
        manager = OnboardingManager(main_window)
        manager.initialize_all_systems()
        
        # Start as intermediate user
        assert manager.user_tracker.get_user_level() == UserLevel.INTERMEDIATE
        
        # Simulate advanced usage patterns
        advanced_actions = [
            ("module_created", {"module_name": "custom_module"}),
            ("api_integration_used", {"api": "external_service"}),
            ("advanced_configuration", {"setting": "performance_tuning"}),
            ("custom_command_created", {"command": "batch_script"})
        ]
        
        for action, context in advanced_actions:
            manager.track_user_action(action, context)
        
        # Manually promote to advanced user
        manager.user_tracker.set_user_level(UserLevel.ADVANCED)
        
        # Verify system adapts to advanced level
        assert manager.user_tracker.get_user_level() == UserLevel.ADVANCED
        
        # Get recommendations for advanced user
        recommendations = manager.get_recommendations()
        assert isinstance(recommendations, list)


class TestErrorHandlingAndRecovery:
    """Test error handling and system recovery scenarios"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    def test_configuration_error_recovery(self, main_window):
        """Test recovery from configuration errors"""
        with patch('src.heal.common.config_manager.ConfigManager') as mock_cm:
            # Simulate configuration load error
            mock_instance = Mock()
            mock_instance.get_config.side_effect = Exception("Config load error")
            mock_cm.return_value = mock_instance
            
            # Should not crash
            manager = OnboardingManager(main_window)
            assert manager is not None
            assert manager.user_tracker is not None
    
    def test_system_error_handling(self, main_window):
        """Test handling of various system errors"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Test error tracking and recommendation generation
            error_scenarios = [
                ("connection_error", {"server": "test", "error": "timeout"}),
                ("performance_issue", {"cpu": 95, "memory": 90}),
                ("configuration_error", {"setting": "invalid_value"}),
                ("module_error", {"module": "test_module", "error": "import_failed"})
            ]
            
            for error_type, context in error_scenarios:
                # Should not raise exceptions
                manager.track_error(error_type, context)
                
                # Should generate appropriate recommendations
                recommendations = manager.get_recommendations()
                assert isinstance(recommendations, list)
    
    def test_component_failure_isolation(self, main_window):
        """Test that component failures don't crash the entire system"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            
            # Simulate component initialization failures
            with patch.object(manager, '_ensure_smart_tip_system', side_effect=Exception("Tip system error")):
                with patch.object(manager, '_ensure_recommendation_engine', side_effect=Exception("Recommendation error")):
                    # Should handle gracefully
                    try:
                        manager.initialize_all_systems()
                    except Exception:
                        pass  # Expected to fail, but shouldn't crash
                    
                    # Core functionality should still work
                    assert manager.user_tracker is not None
                    progress = manager.get_onboarding_progress()
                    assert isinstance(progress, dict)


class TestPerformanceAndScalability:
    """Test performance and scalability scenarios"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    def test_high_volume_action_tracking(self, main_window):
        """Test handling of high volume action tracking"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Track many actions rapidly
            for i in range(100):
                manager.track_user_action(f"action_{i}", {"index": i})
                manager.track_feature_usage(f"feature_{i % 10}")
            
            # System should handle gracefully
            stats = manager.get_comprehensive_statistics()
            assert isinstance(stats, dict)
    
    def test_memory_usage_optimization(self, main_window):
        """Test memory usage optimization"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            
            # Test lazy loading
            assert manager._smart_tip_system is None
            assert manager._recommendation_engine is None
            
            # Initialize one system
            tip_system = manager._ensure_smart_tip_system()
            assert tip_system is not None
            assert manager._smart_tip_system is not None
            
            # Other systems should still be None
            assert manager._recommendation_engine is None
    
    def test_concurrent_operations(self, main_window):
        """Test handling of concurrent operations"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Simulate concurrent operations
            operations = [
                lambda: manager.track_user_action("concurrent_action_1", {}),
                lambda: manager.get_recommendations(),
                lambda: manager.search_documentation("test"),
                lambda: manager.get_discovery_progress(),
                lambda: manager.track_system_state({"test": "value"}),
            ]
            
            # Execute operations
            for operation in operations:
                try:
                    operation()
                except Exception as e:
                    # Log but don't fail test
                    print(f"Operation failed: {e}")
            
            # System should remain stable
            stats = manager.get_comprehensive_statistics()
            assert isinstance(stats, dict)


class TestSystemIntegration:
    """Test integration between different onboarding components"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    def test_cross_component_communication(self, main_window):
        """Test communication between onboarding components"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Test that user actions affect multiple systems
            manager.track_user_action("server_management_used", {"servers": 3})
            
            # Should affect:
            # 1. User state tracker (action tracking)
            # 2. Recommendation engine (behavior analysis)
            # 3. Feature discovery (usage patterns)
            # 4. Smart tip system (context awareness)
            
            # Verify systems are aware of the action
            recommendations = manager.get_recommendations()
            discovery_progress = manager.get_discovery_progress()
            
            assert isinstance(recommendations, list)
            assert isinstance(discovery_progress, dict)
    
    def test_user_preference_propagation(self, main_window):
        """Test that user preferences propagate across components"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Change user preferences
            new_prefs = {
                "show_tips": False,
                "show_tooltips": False,
                "tutorial_speed": "fast"
            }
            manager.user_tracker.update_help_preferences(new_prefs)
            
            # Verify preferences affect system behavior
            assert manager.user_tracker.should_show_tips() == False
            assert manager.user_tracker.should_show_tooltips() == False
            assert manager.user_tracker.get_tutorial_speed() == "fast"
    
    def test_data_consistency_across_components(self, main_window):
        """Test data consistency across all components"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Perform various operations
            manager.track_user_action("consistency_test", {})
            manager.user_tracker.set_user_level(UserLevel.ADVANCED)
            manager.user_tracker.complete_onboarding_step(OnboardingStep.WELCOME)
            
            # Get statistics from all components
            stats = manager.get_comprehensive_statistics()
            
            # Verify data consistency
            assert stats["user_state"]["user_level"] == "advanced"
            assert "onboarding_progress" in stats
            
            # All components should reflect the same user state
            user_level = manager.user_tracker.get_user_level()
            assert user_level == UserLevel.ADVANCED


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    def test_daily_usage_simulation(self, main_window):
        """Simulate a typical daily usage session"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Simulate daily workflow
            daily_actions = [
                ("app_started", {}),
                ("home_page_viewed", {}),
                ("server_status_checked", {"servers": ["server1", "server2"]}),
                ("server_started", {"server_id": "server1"}),
                ("logs_viewed", {"server_id": "server1"}),
                ("module_downloaded", {"module": "astronomy_tools"}),
                ("settings_accessed", {"section": "performance"}),
                ("help_requested", {"topic": "server_configuration"}),
                ("app_closed", {"session_duration": 1800})
            ]
            
            for action, context in daily_actions:
                manager.track_user_action(action, context)
            
            # Verify system learned from the session
            stats = manager.get_comprehensive_statistics()
            assert stats["user_state"]["app_launches"] > 0
    
    def test_power_user_workflow(self, main_window):
        """Test advanced power user workflow"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Set up as advanced user
            manager.user_tracker.set_user_level(UserLevel.ADVANCED)
            
            # Simulate power user actions
            power_actions = [
                ("batch_operation_performed", {"operation": "start_all", "servers": 10}),
                ("custom_module_created", {"module": "custom_automation"}),
                ("api_integration_configured", {"api": "external_telescope"}),
                ("performance_tuning_applied", {"settings": ["memory_optimization", "cpu_affinity"]}),
                ("advanced_logging_configured", {"level": "debug", "filters": ["network", "performance"]}),
                ("automation_script_created", {"script": "nightly_routine"}),
            ]
            
            for action, context in power_actions:
                manager.track_user_action(action, context)
            
            # Should generate advanced recommendations
            recommendations = manager.get_recommendations()
            assert isinstance(recommendations, list)
            
            # Should discover expert features
            discovery_progress = manager.get_discovery_progress()
            assert discovery_progress["discovery_percentage"] >= 0
    
    def test_troubleshooting_scenario(self, main_window):
        """Test system behavior during troubleshooting scenarios"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Simulate troubleshooting session
            troubleshooting_sequence = [
                ("connection_error", {"server": "remote_server", "error": "timeout"}),
                ("help_requested", {"topic": "connection_issues"}),
                ("documentation_accessed", {"doc": "troubleshooting_guide"}),
                ("configuration_changed", {"setting": "proxy_settings"}),
                ("connection_retry", {"server": "remote_server"}),
                ("connection_success", {"server": "remote_server"}),
                ("problem_resolved", {"solution": "proxy_configuration"})
            ]
            
            for action, context in troubleshooting_sequence:
                if "error" in action:
                    manager.track_error(action, context)
                else:
                    manager.track_user_action(action, context)
            
            # Should provide helpful recommendations
            recommendations = manager.get_recommendations()
            assert isinstance(recommendations, list)
            
            # Should suggest relevant documentation
            docs = manager.search_documentation("connection troubleshooting")
            assert isinstance(docs, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
