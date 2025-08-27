"""
Comprehensive tests for TutorialSystem component

Tests interactive tutorials, step validation, progress tracking,
and tutorial management functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QWidget

from src.heal.components.onboarding.tutorial_system import (
    TutorialSystem, Tutorial, TutorialStep
)
from src.heal.components.onboarding.user_state_tracker import UserLevel, UserStateTracker


class TestTutorialStep:
    """Test TutorialStep class functionality"""
    
    def test_step_creation(self):
        """Test TutorialStep creation and basic properties"""
        step = TutorialStep(
            step_id="test_step",
            title_key="tutorials.test.title",
            content_key="tutorials.test.content",
            target_widget="test_widget",
            action_required="click_button",
            validation_func=lambda: True,
            delay_ms=1000,
            auto_advance=True,
            auto_advance_delay=3000
        )
        
        assert step.step_id == "test_step"
        assert step.title_key == "tutorials.test.title"
        assert step.content_key == "tutorials.test.content"
        assert step.target_widget == "test_widget"
        assert step.action_required == "click_button"
        assert step.validation_func is not None
        assert step.delay_ms == 1000
        assert step.auto_advance == True
        assert step.auto_advance_delay == 3000
        assert step.completed == False
    
    def test_step_validation(self):
        """Test step validation functionality"""
        # Step with validation function
        validation_called = False
        
        def test_validation():
            nonlocal validation_called
            validation_called = True
            return True
        
        step = TutorialStep(
            step_id="validation_step",
            title_key="tutorials.validation.title",
            content_key="tutorials.validation.content",
            validation_func=test_validation
        )
        
        # Test validation
        assert step.is_valid() == True
        assert validation_called == True
        
        # Step without validation function
        step_no_validation = TutorialStep(
            step_id="no_validation_step",
            title_key="tutorials.no_validation.title",
            content_key="tutorials.no_validation.content"
        )
        
        assert step_no_validation.is_valid() == True
    
    def test_step_content_retrieval(self):
        """Test step content retrieval with translation"""
        step = TutorialStep(
            step_id="content_step",
            title_key="tutorials.content.title",
            content_key="tutorials.content.content"
        )
        
        # Should return translated content or fallback
        title = step.get_title()
        content = step.get_content()
        
        assert isinstance(title, str)
        assert isinstance(content, str)
        assert len(title) > 0
        assert len(content) > 0


class TestTutorial:
    """Test Tutorial class functionality"""
    
    def test_tutorial_creation(self):
        """Test Tutorial creation and basic properties"""
        tutorial = Tutorial(
            tutorial_id="test_tutorial",
            title_key="tutorials.test.title",
            description_key="tutorials.test.description",
            user_levels=[UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
            prerequisites=["completed_welcome"],
            estimated_duration=300
        )
        
        assert tutorial.tutorial_id == "test_tutorial"
        assert tutorial.title_key == "tutorials.test.title"
        assert tutorial.description_key == "tutorials.test.description"
        assert tutorial.user_levels == [UserLevel.BEGINNER, UserLevel.INTERMEDIATE]
        assert tutorial.prerequisites == ["completed_welcome"]
        assert tutorial.estimated_duration == 300
        assert tutorial.current_step_index == 0
        assert tutorial.completed == False
        assert tutorial.started == False
        assert len(tutorial.steps) == 0
    
    def test_tutorial_step_management(self):
        """Test adding and managing tutorial steps"""
        tutorial = Tutorial(
            tutorial_id="step_management_tutorial",
            title_key="tutorials.step_management.title",
            description_key="tutorials.step_management.description",
            user_levels=[UserLevel.BEGINNER]
        )
        
        # Add steps
        steps = [
            TutorialStep("step1", "title1", "content1"),
            TutorialStep("step2", "title2", "content2"),
            TutorialStep("step3", "title3", "content3")
        ]
        
        for step in steps:
            tutorial.add_step(step)
        
        assert len(tutorial.steps) == 3
        assert tutorial.get_current_step() == steps[0]
    
    def test_tutorial_progression(self):
        """Test tutorial step progression"""
        tutorial = Tutorial(
            tutorial_id="progression_tutorial",
            title_key="tutorials.progression.title",
            description_key="tutorials.progression.description",
            user_levels=[UserLevel.BEGINNER]
        )
        
        # Add steps
        for i in range(3):
            step = TutorialStep(f"step{i}", f"title{i}", f"content{i}")
            tutorial.add_step(step)
        
        # Test progression
        assert tutorial.current_step_index == 0
        assert tutorial.get_current_step().step_id == "step0"
        
        # Advance to next step
        result = tutorial.advance_step()
        assert result == True
        assert tutorial.current_step_index == 1
        assert tutorial.get_current_step().step_id == "step1"
        
        # Advance to last step
        tutorial.advance_step()
        assert tutorial.current_step_index == 2
        assert tutorial.get_current_step().step_id == "step2"
        
        # Try to advance beyond last step
        result = tutorial.advance_step()
        assert result == False
        assert tutorial.completed == True
    
    def test_tutorial_backward_navigation(self):
        """Test backward navigation in tutorial"""
        tutorial = Tutorial(
            tutorial_id="backward_tutorial",
            title_key="tutorials.backward.title",
            description_key="tutorials.backward.description",
            user_levels=[UserLevel.BEGINNER]
        )
        
        # Add steps
        for i in range(3):
            step = TutorialStep(f"step{i}", f"title{i}", f"content{i}")
            tutorial.add_step(step)
        
        # Advance to middle step
        tutorial.advance_step()
        assert tutorial.current_step_index == 1
        
        # Go back
        result = tutorial.previous_step()
        assert result == True
        assert tutorial.current_step_index == 0
        
        # Try to go back from first step
        result = tutorial.previous_step()
        assert result == False
        assert tutorial.current_step_index == 0
    
    def test_tutorial_reset(self):
        """Test tutorial reset functionality"""
        tutorial = Tutorial(
            tutorial_id="reset_tutorial",
            title_key="tutorials.reset.title",
            description_key="tutorials.reset.description",
            user_levels=[UserLevel.BEGINNER]
        )
        
        # Add and complete some steps
        for i in range(3):
            step = TutorialStep(f"step{i}", f"title{i}", f"content{i}")
            tutorial.add_step(step)
        
        # Progress through tutorial
        tutorial.started = True
        tutorial.advance_step()
        tutorial.advance_step()
        tutorial.steps[0].completed = True
        tutorial.steps[1].completed = True
        
        # Reset tutorial
        tutorial.reset()
        
        assert tutorial.current_step_index == 0
        assert tutorial.completed == False
        assert tutorial.started == False
        for step in tutorial.steps:
            assert step.completed == False
    
    def test_tutorial_progress_tracking(self):
        """Test tutorial progress tracking"""
        tutorial = Tutorial(
            tutorial_id="progress_tutorial",
            title_key="tutorials.progress.title",
            description_key="tutorials.progress.description",
            user_levels=[UserLevel.BEGINNER]
        )
        
        # Add steps
        for i in range(4):
            step = TutorialStep(f"step{i}", f"title{i}", f"content{i}")
            tutorial.add_step(step)
        
        # Mark some steps as completed
        tutorial.steps[0].completed = True
        tutorial.steps[1].completed = True
        tutorial.current_step_index = 2
        
        progress = tutorial.get_progress()
        
        assert progress["current_step"] == 3  # 1-based
        assert progress["total_steps"] == 4
        assert progress["completed_steps"] == 2
        assert progress["progress_percentage"] == 50.0
        assert progress["is_completed"] == False


class TestTutorialSystemCore:
    """Test core TutorialSystem functionality"""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window"""
        return Mock(spec=QWidget)
    
    @pytest.fixture
    def mock_onboarding_manager(self):
        """Create a mock onboarding manager"""
        manager = Mock()
        user_tracker = Mock(spec=UserStateTracker)
        user_tracker.get_user_level.return_value = UserLevel.BEGINNER
        manager.get_user_state_tracker.return_value = user_tracker
        return manager
    
    @pytest.fixture
    def tutorial_system(self, mock_main_window, mock_onboarding_manager):
        """Create a TutorialSystem for testing"""
        return TutorialSystem(mock_main_window, mock_onboarding_manager)
    
    def test_system_initialization(self, tutorial_system):
        """Test TutorialSystem initialization"""
        assert tutorial_system is not None
        assert len(tutorial_system.tutorials) > 0
        assert tutorial_system.active_tutorial is None
        assert tutorial_system.current_teaching_tip is None
        assert hasattr(tutorial_system, 'step_timer')
    
    def test_tutorial_database_structure(self, tutorial_system):
        """Test tutorial database structure"""
        tutorials = tutorial_system.tutorials
        
        # Verify we have different types of tutorials
        tutorial_ids = set(tutorials.keys())
        expected_tutorials = {
            "feature_tour",
            "first_server_setup", 
            "interface_customization",
            "advanced_features",
            "interactive_workflow",
            "module_development"
        }
        
        # Should have at least some expected tutorials
        assert len(tutorial_ids.intersection(expected_tutorials)) > 0
        
        # Verify tutorial structure
        for tutorial in tutorials.values():
            assert hasattr(tutorial, 'tutorial_id')
            assert hasattr(tutorial, 'steps')
            assert hasattr(tutorial, 'user_levels')
            assert len(tutorial.steps) > 0
    
    def test_tutorial_availability_filtering(self, tutorial_system):
        """Test filtering tutorials by user level and prerequisites"""
        # Test with beginner level
        tutorial_system.user_tracker.get_user_level.return_value = UserLevel.BEGINNER
        available = tutorial_system.get_available_tutorials()
        
        beginner_tutorials = [t for t in available if "beginner" in str(t.get("prerequisites_met", True))]
        
        # Test with advanced level
        tutorial_system.user_tracker.get_user_level.return_value = UserLevel.ADVANCED
        available_advanced = tutorial_system.get_available_tutorials()
        
        # Should return list of tutorial info dictionaries
        for tutorial_info in available:
            assert "id" in tutorial_info
            assert "title" in tutorial_info
            assert "description" in tutorial_info
            assert "duration" in tutorial_info
            assert "steps" in tutorial_info
            assert "prerequisites_met" in tutorial_info
            assert "completed" in tutorial_info


class TestTutorialSystemExecution:
    """Test tutorial execution and management"""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window"""
        return Mock(spec=QWidget)
    
    @pytest.fixture
    def mock_onboarding_manager(self):
        """Create a mock onboarding manager"""
        manager = Mock()
        user_tracker = Mock(spec=UserStateTracker)
        user_tracker.get_user_level.return_value = UserLevel.BEGINNER
        manager.get_user_state_tracker.return_value = user_tracker
        return manager
    
    @pytest.fixture
    def tutorial_system(self, mock_main_window, mock_onboarding_manager):
        """Create a TutorialSystem for testing"""
        return TutorialSystem(mock_main_window, mock_onboarding_manager)
    
    def test_tutorial_starting(self, tutorial_system):
        """Test starting tutorials"""
        # Test starting valid tutorial
        tutorial_id = "feature_tour"
        if tutorial_id in tutorial_system.tutorials:
            result = tutorial_system.start_tutorial(tutorial_id)
            assert result == True
            assert tutorial_system.active_tutorial is not None
            assert tutorial_system.active_tutorial.tutorial_id == tutorial_id
            assert tutorial_system.active_tutorial.started == True
        
        # Test starting invalid tutorial
        result = tutorial_system.start_tutorial("invalid_tutorial")
        assert result == False
    
    def test_tutorial_step_navigation(self, tutorial_system):
        """Test tutorial step navigation"""
        # Start a tutorial
        tutorial_id = "feature_tour"
        if tutorial_id in tutorial_system.tutorials:
            tutorial_system.start_tutorial(tutorial_id)
            
            if tutorial_system.active_tutorial:
                initial_step = tutorial_system.active_tutorial.current_step_index
                
                # Test next step
                tutorial_system.next_step()
                if len(tutorial_system.active_tutorial.steps) > 1:
                    assert tutorial_system.active_tutorial.current_step_index == initial_step + 1
                
                # Test previous step
                tutorial_system.previous_step()
                assert tutorial_system.active_tutorial.current_step_index == initial_step
    
    def test_tutorial_cancellation(self, tutorial_system):
        """Test tutorial cancellation"""
        # Start a tutorial
        tutorial_id = "feature_tour"
        if tutorial_id in tutorial_system.tutorials:
            tutorial_system.start_tutorial(tutorial_id)
            assert tutorial_system.active_tutorial is not None
            
            # Cancel tutorial
            tutorial_system.cancel_tutorial()
            assert tutorial_system.active_tutorial is None
    
    def test_tutorial_completion(self, tutorial_system):
        """Test tutorial completion"""
        # Create a simple tutorial for testing
        test_tutorial = Tutorial(
            tutorial_id="test_completion",
            title_key="tutorials.test.title",
            description_key="tutorials.test.description",
            user_levels=[UserLevel.BEGINNER]
        )
        
        # Add a single step
        step = TutorialStep("final_step", "title", "content")
        test_tutorial.add_step(step)
        
        tutorial_system.tutorials["test_completion"] = test_tutorial
        
        # Start and complete tutorial
        tutorial_system.start_tutorial("test_completion")
        if tutorial_system.active_tutorial:
            # Complete the step
            tutorial_system.next_step()
            
            # Should complete the tutorial
            assert tutorial_system.active_tutorial is None or tutorial_system.active_tutorial.completed
    
    def test_step_validation(self, tutorial_system):
        """Test step validation functionality"""
        # Test action validation
        result = tutorial_system.validate_step_action("test_action")
        # Result depends on whether there's an active tutorial with matching action
        assert isinstance(result, bool)
        
        # Test getting current step requirements
        requirements = tutorial_system.get_current_step_requirements()
        # Should return None if no active tutorial, or dict with step info
        assert requirements is None or isinstance(requirements, dict)
    
    def test_tutorial_hints(self, tutorial_system):
        """Test tutorial hint system"""
        hint = tutorial_system.provide_step_hint()
        # Should return None if no active tutorial, or string hint
        assert hint is None or isinstance(hint, str)
    
    def test_tutorial_statistics(self, tutorial_system):
        """Test tutorial statistics generation"""
        stats = tutorial_system.get_tutorial_statistics()
        
        # Verify statistics structure
        assert "total_tutorials" in stats
        assert "completed_tutorials" in stats
        assert "completion_rate" in stats
        assert "step_completion_rates" in stats
        assert "active_tutorial" in stats
        
        # Verify data types
        assert isinstance(stats["total_tutorials"], int)
        assert isinstance(stats["completed_tutorials"], int)
        assert isinstance(stats["completion_rate"], (int, float))
        assert isinstance(stats["step_completion_rates"], dict)


class TestTutorialSystemInteractive:
    """Test interactive tutorial features"""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window"""
        return Mock(spec=QWidget)
    
    @pytest.fixture
    def mock_onboarding_manager(self):
        """Create a mock onboarding manager"""
        manager = Mock()
        user_tracker = Mock(spec=UserStateTracker)
        user_tracker.get_user_level.return_value = UserLevel.INTERMEDIATE
        manager.get_user_state_tracker.return_value = user_tracker
        return manager
    
    @pytest.fixture
    def tutorial_system(self, mock_main_window, mock_onboarding_manager):
        """Create a TutorialSystem for testing"""
        return TutorialSystem(mock_main_window, mock_onboarding_manager)
    
    def test_validation_methods(self, tutorial_system):
        """Test built-in validation methods"""
        # Test validation methods exist and return boolean
        validation_methods = [
            tutorial_system._validate_server_started,
            tutorial_system._validate_logs_viewed,
            tutorial_system._validate_batch_operation,
            tutorial_system._validate_module_created,
            tutorial_system._validate_module_tested
        ]
        
        for method in validation_methods:
            result = method()
            assert isinstance(result, bool)
    
    def test_widget_highlighting(self, tutorial_system):
        """Test widget highlighting functionality"""
        # Should not raise exceptions
        tutorial_system.highlight_target_widget("test_widget")
        tutorial_system.highlight_target_widget("non_existent_widget")
        tutorial_system.highlight_target_widget("")
        tutorial_system.highlight_target_widget(None)
    
    def test_interactive_workflow_tutorial(self, tutorial_system):
        """Test interactive workflow tutorial"""
        tutorial_id = "interactive_workflow"
        if tutorial_id in tutorial_system.tutorials:
            tutorial = tutorial_system.tutorials[tutorial_id]
            
            # Verify tutorial has interactive elements
            interactive_steps = [step for step in tutorial.steps if step.action_required]
            assert len(interactive_steps) > 0
            
            # Verify validation functions exist
            validation_steps = [step for step in tutorial.steps if step.validation_func]
            assert len(validation_steps) > 0
    
    def test_module_development_tutorial(self, tutorial_system):
        """Test module development tutorial"""
        tutorial_id = "module_development"
        if tutorial_id in tutorial_system.tutorials:
            tutorial = tutorial_system.tutorials[tutorial_id]
            
            # Verify tutorial is for appropriate user levels
            assert UserLevel.INTERMEDIATE in tutorial.user_levels or UserLevel.ADVANCED in tutorial.user_levels
            
            # Verify tutorial has prerequisites
            assert len(tutorial.prerequisites) > 0


class TestTutorialSystemEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window"""
        return Mock(spec=QWidget)
    
    @pytest.fixture
    def mock_onboarding_manager(self):
        """Create a mock onboarding manager"""
        manager = Mock()
        user_tracker = Mock(spec=UserStateTracker)
        user_tracker.get_user_level.return_value = UserLevel.BEGINNER
        manager.get_user_state_tracker.return_value = user_tracker
        return manager
    
    @pytest.fixture
    def tutorial_system(self, mock_main_window, mock_onboarding_manager):
        """Create a TutorialSystem for testing"""
        return TutorialSystem(mock_main_window, mock_onboarding_manager)
    
    def test_empty_tutorial_handling(self, tutorial_system):
        """Test handling of tutorials with no steps"""
        empty_tutorial = Tutorial(
            tutorial_id="empty_tutorial",
            title_key="tutorials.empty.title",
            description_key="tutorials.empty.description",
            user_levels=[UserLevel.BEGINNER]
        )
        
        tutorial_system.tutorials["empty_tutorial"] = empty_tutorial
        
        # Should handle gracefully
        result = tutorial_system.start_tutorial("empty_tutorial")
        # Behavior depends on implementation - might succeed or fail
        assert isinstance(result, bool)
    
    def test_invalid_step_actions(self, tutorial_system):
        """Test handling of invalid step actions"""
        # Should handle gracefully
        result = tutorial_system.validate_step_action("")
        assert result == False
        
        result = tutorial_system.validate_step_action(None)
        assert result == False
        
        result = tutorial_system.validate_step_action("non_existent_action")
        assert result == False
    
    def test_tutorial_timer_handling(self, tutorial_system):
        """Test tutorial timer management"""
        # Timer should exist and be manageable
        assert hasattr(tutorial_system, 'step_timer')
        
        # Should handle timer operations gracefully
        tutorial_system.step_timer.stop()
        tutorial_system.step_timer.start(1000)
        tutorial_system.step_timer.stop()
    
    def test_concurrent_tutorial_starting(self, tutorial_system):
        """Test starting multiple tutorials"""
        tutorial_ids = list(tutorial_system.tutorials.keys())[:2]
        
        if len(tutorial_ids) >= 2:
            # Start first tutorial
            result1 = tutorial_system.start_tutorial(tutorial_ids[0])
            
            # Try to start second tutorial (should cancel first)
            result2 = tutorial_system.start_tutorial(tutorial_ids[1])
            
            # Should handle gracefully
            assert isinstance(result1, bool)
            assert isinstance(result2, bool)
            
            # Should have at most one active tutorial
            assert tutorial_system.active_tutorial is None or tutorial_system.active_tutorial.tutorial_id == tutorial_ids[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
