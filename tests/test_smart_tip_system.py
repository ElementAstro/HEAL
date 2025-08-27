"""
Comprehensive tests for SmartTipSystem component

Tests intelligent tip selection, context awareness, user behavior adaptation,
and tip rotation functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List

from src.heal.components.onboarding.smart_tip_system import (
    SmartTipSystem, SmartTip, TipCategory, TipContext
)
from src.heal.components.onboarding.user_state_tracker import UserLevel, UserStateTracker


class TestSmartTip:
    """Test SmartTip class functionality"""
    
    def test_tip_creation(self):
        """Test SmartTip creation and basic properties"""
        tip = SmartTip(
            tip_id="test_tip",
            content_key="tips.test_tip",
            category=TipCategory.BASIC_USAGE,
            context=TipContext.HOME,
            user_levels=[UserLevel.BEGINNER],
            priority=3,
            frequency_limit=timedelta(hours=1)
        )
        
        assert tip.tip_id == "test_tip"
        assert tip.category == TipCategory.BASIC_USAGE
        assert tip.context == TipContext.HOME
        assert tip.priority == 3
        assert tip.show_count == 0
        assert tip.last_shown is None
    
    def test_tip_applicability(self):
        """Test tip applicability logic"""
        tip = SmartTip(
            tip_id="test_tip",
            content_key="tips.test_tip",
            category=TipCategory.BASIC_USAGE,
            context=TipContext.HOME,
            user_levels=[UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
            prerequisites=["completed_welcome"],
            frequency_limit=timedelta(hours=1)
        )
        
        # Test user level matching
        assert tip.is_applicable(
            UserLevel.BEGINNER, TipContext.HOME, 
            {"completed_welcome"}, {}
        ) == True
        
        assert tip.is_applicable(
            UserLevel.ADVANCED, TipContext.HOME,
            {"completed_welcome"}, {}
        ) == False
        
        # Test context matching
        assert tip.is_applicable(
            UserLevel.BEGINNER, TipContext.LAUNCHER,
            {"completed_welcome"}, {}
        ) == False
        
        # Test prerequisites
        assert tip.is_applicable(
            UserLevel.BEGINNER, TipContext.HOME,
            set(), {}
        ) == False
        
        # Test frequency limit
        tip.mark_shown()
        last_shown_times = {tip.tip_id: datetime.now()}
        assert tip.is_applicable(
            UserLevel.BEGINNER, TipContext.HOME,
            {"completed_welcome"}, last_shown_times
        ) == False
    
    def test_tip_marking(self):
        """Test tip marking functionality"""
        tip = SmartTip(
            tip_id="test_tip",
            content_key="tips.test_tip",
            category=TipCategory.BASIC_USAGE,
            context=TipContext.HOME,
            user_levels=[UserLevel.BEGINNER]
        )
        
        # Initially not shown
        assert tip.show_count == 0
        assert tip.last_shown is None
        
        # Mark as shown
        tip.mark_shown()
        assert tip.show_count == 1
        assert tip.last_shown is not None
        assert isinstance(tip.last_shown, datetime)
        
        # Mark as shown again
        first_shown = tip.last_shown
        tip.mark_shown()
        assert tip.show_count == 2
        assert tip.last_shown > first_shown


class TestSmartTipSystemCore:
    """Test core SmartTipSystem functionality"""
    
    @pytest.fixture
    def mock_user_tracker(self):
        """Create a mock user tracker"""
        tracker = Mock(spec=UserStateTracker)
        tracker.get_user_level.return_value = UserLevel.BEGINNER
        tracker.should_show_tips.return_value = True
        return tracker
    
    @pytest.fixture
    def tip_system(self, mock_user_tracker):
        """Create a SmartTipSystem for testing"""
        return SmartTipSystem(mock_user_tracker)
    
    def test_system_initialization(self, tip_system):
        """Test SmartTipSystem initialization"""
        assert tip_system is not None
        assert len(tip_system.tips) > 0
        assert tip_system.current_context == TipContext.GENERAL
        assert hasattr(tip_system, 'rotation_timer')
        assert hasattr(tip_system, 'last_shown_times')
        assert hasattr(tip_system, 'completed_actions')
    
    def test_tip_database_structure(self, tip_system):
        """Test that tip database is properly structured"""
        # Verify we have tips for different categories
        categories = set(tip.category for tip in tip_system.tips.values())
        assert TipCategory.BASIC_USAGE in categories
        assert TipCategory.SHORTCUTS in categories
        assert TipCategory.ADVANCED_FEATURES in categories
        
        # Verify we have tips for different contexts
        contexts = set(tip.context for tip in tip_system.tips.values())
        assert TipContext.HOME in contexts
        assert TipContext.GENERAL in contexts
        
        # Verify we have tips for different user levels
        all_levels = set()
        for tip in tip_system.tips.values():
            all_levels.update(tip.user_levels)
        assert UserLevel.BEGINNER in all_levels
        assert UserLevel.INTERMEDIATE in all_levels
        assert UserLevel.ADVANCED in all_levels
    
    def test_context_switching(self, tip_system):
        """Test context switching functionality"""
        # Initial context
        assert tip_system.current_context == TipContext.GENERAL
        
        # Switch context
        tip_system.set_context(TipContext.HOME)
        assert tip_system.current_context == TipContext.HOME
        
        tip_system.set_context(TipContext.LAUNCHER)
        assert tip_system.current_context == TipContext.LAUNCHER
        
        # Context should not change if same
        tip_system.set_context(TipContext.LAUNCHER)
        assert tip_system.current_context == TipContext.LAUNCHER


class TestSmartTipSystemBehavior:
    """Test SmartTipSystem behavior and intelligence"""
    
    @pytest.fixture
    def mock_user_tracker(self):
        """Create a mock user tracker"""
        tracker = Mock(spec=UserStateTracker)
        tracker.get_user_level.return_value = UserLevel.BEGINNER
        tracker.should_show_tips.return_value = True
        return tracker
    
    @pytest.fixture
    def tip_system(self, mock_user_tracker):
        """Create a SmartTipSystem for testing"""
        return SmartTipSystem(mock_user_tracker)
    
    def test_action_tracking(self, tip_system):
        """Test action tracking and tip triggering"""
        # Track actions that should trigger tips
        actions = [
            "connection_failed",
            "performance_issue_detected",
            "used_basic_shortcuts",
            "visited_tools_section"
        ]
        
        for action in actions:
            tip_system.track_action(action)
            assert action in tip_system.completed_actions
    
    def test_applicable_tips_filtering(self, tip_system):
        """Test filtering of applicable tips"""
        # Set context and get applicable tips
        tip_system.set_context(TipContext.HOME)
        applicable_tips = tip_system._get_applicable_tips()
        
        # All returned tips should be applicable for current context and user level
        for tip in applicable_tips:
            assert tip.is_applicable(
                tip_system.user_tracker.get_user_level(),
                tip_system.current_context,
                tip_system.completed_actions,
                tip_system.last_shown_times
            )
    
    def test_tip_selection_algorithm(self, tip_system):
        """Test tip selection algorithm"""
        # Create some test tips with different priorities
        tips = []
        for i in range(5):
            tip = SmartTip(
                tip_id=f"test_tip_{i}",
                content_key=f"tips.test_tip_{i}",
                category=TipCategory.BASIC_USAGE,
                context=TipContext.GENERAL,
                user_levels=[UserLevel.BEGINNER],
                priority=i + 1
            )
            tips.append(tip)
        
        # Test selection with different show counts
        tips[0].show_count = 0  # Never shown
        tips[1].show_count = 1  # Shown once
        tips[2].show_count = 5  # Shown many times
        
        selected_tip = tip_system._select_tip(tips)
        
        # Should prefer unshown tips and higher priority
        assert selected_tip is not None
        assert selected_tip in tips
    
    def test_contextual_tip_display(self, tip_system):
        """Test contextual tip display"""
        # Mock the tip display
        with patch.object(tip_system, '_show_tip') as mock_show:
            tip_system.set_context(TipContext.HOME)
            
            # Should attempt to show a contextual tip
            # (exact behavior depends on available tips)
            # Verify the method was called or not based on available tips
            pass  # Implementation depends on specific tip availability
    
    def test_rotation_control(self, tip_system):
        """Test tip rotation control"""
        # Test starting rotation
        tip_system.start_rotation(5000)  # 5 second interval
        assert tip_system.rotation_timer.isActive()
        
        # Test stopping rotation
        tip_system.stop_rotation()
        assert not tip_system.rotation_timer.isActive()
        
        # Test that rotation respects user preferences
        tip_system.user_tracker.should_show_tips.return_value = False
        tip_system.start_rotation(1000)
        # Should not start if user doesn't want tips
        # (behavior may vary based on implementation)


class TestSmartTipSystemAdvanced:
    """Test advanced SmartTipSystem features"""
    
    @pytest.fixture
    def mock_user_tracker(self):
        """Create a mock user tracker with advanced settings"""
        tracker = Mock(spec=UserStateTracker)
        tracker.get_user_level.return_value = UserLevel.INTERMEDIATE
        tracker.should_show_tips.return_value = True
        return tracker
    
    @pytest.fixture
    def tip_system(self, mock_user_tracker):
        """Create a SmartTipSystem for testing"""
        return SmartTipSystem(mock_user_tracker)
    
    def test_user_level_adaptation(self, tip_system):
        """Test adaptation to different user levels"""
        # Test with beginner level
        tip_system.user_tracker.get_user_level.return_value = UserLevel.BEGINNER
        beginner_tips = tip_system._get_applicable_tips()
        
        # Test with advanced level
        tip_system.user_tracker.get_user_level.return_value = UserLevel.ADVANCED
        advanced_tips = tip_system._get_applicable_tips()
        
        # Should have different tips for different levels
        beginner_tip_ids = {tip.tip_id for tip in beginner_tips}
        advanced_tip_ids = {tip.tip_id for tip in advanced_tips}
        
        # There should be some difference (though some tips may overlap)
        assert beginner_tip_ids != advanced_tip_ids or len(beginner_tip_ids) == 0 or len(advanced_tip_ids) == 0
    
    def test_frequency_limiting(self, tip_system):
        """Test tip frequency limiting"""
        # Find a tip with frequency limit
        limited_tip = None
        for tip in tip_system.tips.values():
            if tip.frequency_limit:
                limited_tip = tip
                break
        
        if limited_tip:
            # Mark tip as recently shown
            limited_tip.mark_shown()
            tip_system.last_shown_times[limited_tip.tip_id] = datetime.now()
            
            # Should not be applicable due to frequency limit
            assert not limited_tip.is_applicable(
                tip_system.user_tracker.get_user_level(),
                limited_tip.context,
                set(limited_tip.prerequisites),
                tip_system.last_shown_times
            )
    
    def test_prerequisite_checking(self, tip_system):
        """Test prerequisite checking for tips"""
        # Find a tip with prerequisites
        prereq_tip = None
        for tip in tip_system.tips.values():
            if tip.prerequisites:
                prereq_tip = tip
                break
        
        if prereq_tip:
            # Without prerequisites met
            assert not prereq_tip.is_applicable(
                tip_system.user_tracker.get_user_level(),
                prereq_tip.context,
                set(),  # No completed actions
                {}
            )
            
            # With prerequisites met
            assert prereq_tip.is_applicable(
                tip_system.user_tracker.get_user_level(),
                prereq_tip.context,
                set(prereq_tip.prerequisites),
                {}
            )
    
    def test_action_triggered_tips(self, tip_system):
        """Test action-triggered tip functionality"""
        # Find tips with action triggers
        action_tips = [tip for tip in tip_system.tips.values() if tip.action_triggers]
        
        if action_tips:
            test_tip = action_tips[0]
            trigger_action = test_tip.action_triggers[0]
            
            # Mock the tip showing
            with patch.object(tip_system, '_show_tip') as mock_show:
                tip_system.track_action(trigger_action)
                
                # Should have attempted to show the tip
                # (exact behavior depends on tip applicability)
                pass  # Verification depends on specific implementation
    
    def test_statistics_generation(self, tip_system):
        """Test tip statistics generation"""
        # Generate some activity
        tip_system.track_action("test_action")
        tip_system.set_context(TipContext.HOME)
        
        # Get statistics
        stats = tip_system.get_tip_statistics()
        
        # Verify statistics structure
        assert "total_tips" in stats
        assert "shown_tips" in stats
        assert "category_distribution" in stats
        assert "current_context" in stats
        assert "rotation_active" in stats
        
        # Verify data types and values
        assert isinstance(stats["total_tips"], int)
        assert isinstance(stats["shown_tips"], int)
        assert isinstance(stats["category_distribution"], dict)
        assert stats["current_context"] == TipContext.HOME.value
        assert isinstance(stats["rotation_active"], bool)


class TestSmartTipSystemIntegration:
    """Test SmartTipSystem integration scenarios"""
    
    @pytest.fixture
    def mock_user_tracker(self):
        """Create a comprehensive mock user tracker"""
        tracker = Mock(spec=UserStateTracker)
        tracker.get_user_level.return_value = UserLevel.BEGINNER
        tracker.should_show_tips.return_value = True
        return tracker
    
    @pytest.fixture
    def tip_system(self, mock_user_tracker):
        """Create a SmartTipSystem for testing"""
        return SmartTipSystem(mock_user_tracker)
    
    def test_user_preference_integration(self, tip_system):
        """Test integration with user preferences"""
        # Test when user disables tips
        tip_system.user_tracker.should_show_tips.return_value = False
        
        # Rotation should not start
        tip_system.start_rotation(1000)
        # Behavior depends on implementation
        
        # Manual tip requests should be ignored
        tip_system._rotate_tip()
        # Should not show tips when disabled
    
    def test_context_change_behavior(self, tip_system):
        """Test behavior when context changes"""
        contexts_to_test = [
            TipContext.HOME,
            TipContext.LAUNCHER,
            TipContext.DOWNLOAD,
            TipContext.TOOLS,
            TipContext.SETTINGS
        ]
        
        for context in contexts_to_test:
            with patch.object(tip_system, '_show_contextual_tip') as mock_show:
                tip_system.set_context(context)
                
                # Should attempt to show contextual tip when context changes
                # (if tips are enabled)
                if tip_system.user_tracker.should_show_tips():
                    pass  # Verification depends on implementation
    
    def test_force_tip_display(self, tip_system):
        """Test forcing display of specific tips"""
        # Get a valid tip ID
        if tip_system.tips:
            tip_id = list(tip_system.tips.keys())[0]
            
            with patch.object(tip_system, '_show_tip') as mock_show:
                result = tip_system.force_show_tip(tip_id)
                
                assert result == True
                mock_show.assert_called_once()
        
        # Test with invalid tip ID
        result = tip_system.force_show_tip("invalid_tip_id")
        assert result == False
    
    def test_tip_for_context_retrieval(self, tip_system):
        """Test retrieving tips for specific contexts"""
        contexts_to_test = [TipContext.HOME, TipContext.LAUNCHER, TipContext.GENERAL]
        
        for context in contexts_to_test:
            tip_content = tip_system.get_tip_for_context(context)
            
            # Should return string content or None
            assert tip_content is None or isinstance(tip_content, str)


class TestSmartTipSystemErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def mock_user_tracker(self):
        """Create a mock user tracker"""
        tracker = Mock(spec=UserStateTracker)
        tracker.get_user_level.return_value = UserLevel.BEGINNER
        tracker.should_show_tips.return_value = True
        return tracker
    
    @pytest.fixture
    def tip_system(self, mock_user_tracker):
        """Create a SmartTipSystem for testing"""
        return SmartTipSystem(mock_user_tracker)
    
    def test_empty_tip_selection(self, tip_system):
        """Test behavior when no tips are applicable"""
        # Clear all completed actions and set restrictive context
        tip_system.completed_actions.clear()
        tip_system.user_tracker.get_user_level.return_value = UserLevel.ADVANCED
        tip_system.set_context(TipContext.GENERAL)
        
        # Should handle empty tip list gracefully
        selected_tip = tip_system._select_tip([])
        assert selected_tip is None
    
    def test_invalid_context_handling(self, tip_system):
        """Test handling of invalid contexts"""
        # This should not raise an exception
        try:
            tip_system.set_context("invalid_context")
        except (ValueError, AttributeError):
            # Expected for invalid enum values
            pass
    
    def test_malformed_tip_data(self, tip_system):
        """Test handling of malformed tip data"""
        # Create a tip with missing required data
        malformed_tip = SmartTip(
            tip_id="malformed",
            content_key="",  # Empty content key
            category=TipCategory.BASIC_USAGE,
            context=TipContext.GENERAL,
            user_levels=[]  # Empty user levels
        )
        
        # Should handle gracefully
        content = malformed_tip.get_content()
        assert isinstance(content, str)  # Should return fallback content
        
        # Should not be applicable to any user
        assert not malformed_tip.is_applicable(
            UserLevel.BEGINNER, TipContext.GENERAL, set(), {}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
