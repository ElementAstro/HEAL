"""
Tutorial System

Interactive tutorial system that provides step-by-step guided tours
of application features and workflows.
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import TeachingTip, TeachingTipTailPosition

from ...common.i18n_ui import tr
from ...common.logging_config import get_logger
from .user_state_tracker import UserLevel, UserStateTracker


class TutorialStep:
    """Represents a single step in a tutorial"""
    
    def __init__(
        self,
        step_id: str,
        title_key: str,
        content_key: str,
        target_widget: Optional[str] = None,
        action_required: Optional[str] = None,
        validation_func: Optional[Callable] = None,
        delay_ms: int = 500,
        auto_advance: bool = False,
        auto_advance_delay: int = 3000,
    ):
        self.step_id = step_id
        self.title_key = title_key
        self.content_key = content_key
        self.target_widget = target_widget
        self.action_required = action_required
        self.validation_func = validation_func
        self.delay_ms = delay_ms
        self.auto_advance = auto_advance
        self.auto_advance_delay = auto_advance_delay
        self.completed = False
    
    def get_title(self) -> str:
        """Get the translated step title"""
        return tr(self.title_key, default=f"Step: {self.step_id}")
    
    def get_content(self) -> str:
        """Get the translated step content"""
        return tr(self.content_key, default=f"Tutorial step: {self.step_id}")
    
    def is_valid(self) -> bool:
        """Check if step requirements are met"""
        if self.validation_func:
            return self.validation_func()
        return True


class Tutorial:
    """Represents a complete tutorial with multiple steps"""
    
    def __init__(
        self,
        tutorial_id: str,
        title_key: str,
        description_key: str,
        user_levels: List[UserLevel],
        prerequisites: Optional[List[str]] = None,
        estimated_duration: int = 300,  # seconds
    ):
        self.tutorial_id = tutorial_id
        self.title_key = title_key
        self.description_key = description_key
        self.user_levels = user_levels
        self.prerequisites = prerequisites or []
        self.estimated_duration = estimated_duration
        self.steps: List[TutorialStep] = []
        self.current_step_index = 0
        self.completed = False
        self.started = False
    
    def add_step(self, step: TutorialStep) -> None:
        """Add a step to the tutorial"""
        self.steps.append(step)
    
    def get_title(self) -> str:
        """Get the translated tutorial title"""
        return tr(self.title_key, default=f"Tutorial: {self.tutorial_id}")
    
    def get_description(self) -> str:
        """Get the translated tutorial description"""
        return tr(self.description_key, default=f"Tutorial description: {self.tutorial_id}")
    
    def get_current_step(self) -> Optional[TutorialStep]:
        """Get the current step"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def advance_step(self) -> bool:
        """Advance to the next step"""
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            return True
        else:
            self.completed = True
            return False
    
    def previous_step(self) -> bool:
        """Go back to the previous step"""
        if self.current_step_index > 0:
            self.current_step_index -= 1
            return True
        return False
    
    def reset(self) -> None:
        """Reset tutorial to the beginning"""
        self.current_step_index = 0
        self.completed = False
        self.started = False
        for step in self.steps:
            step.completed = False
    
    def get_progress(self) -> Dict[str, Any]:
        """Get tutorial progress information"""
        completed_steps = sum(1 for step in self.steps if step.completed)
        return {
            "current_step": self.current_step_index + 1,
            "total_steps": len(self.steps),
            "completed_steps": completed_steps,
            "progress_percentage": (completed_steps / len(self.steps)) * 100 if self.steps else 0,
            "is_completed": self.completed,
        }


class TutorialSystem(QObject):
    """Manages interactive tutorials throughout the application"""
    
    # Signals
    tutorial_started = Signal(str)  # tutorial_id
    tutorial_completed = Signal(str)  # tutorial_id
    tutorial_cancelled = Signal(str)  # tutorial_id
    step_changed = Signal(str, int)  # tutorial_id, step_index
    step_completed = Signal(str, str)  # tutorial_id, step_id
    
    def __init__(self, main_window: QWidget, onboarding_manager: Any, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger("tutorial_system", module="TutorialSystem")
        self.main_window = main_window
        self.onboarding_manager = onboarding_manager
        self.user_tracker = onboarding_manager.get_user_state_tracker()
        
        # Tutorial management
        self.tutorials: Dict[str, Tutorial] = {}
        self.active_tutorial: Optional[Tutorial] = None
        self.current_teaching_tip: Optional[TeachingTip] = None
        
        # Timers
        self.step_timer = QTimer(self)
        self.step_timer.setSingleShot(True)
        self.step_timer.timeout.connect(self._advance_step_auto)
        
        self._init_tutorials()
    
    def _init_tutorials(self) -> None:
        """Initialize available tutorials"""
        # Feature tour tutorial
        feature_tour = Tutorial(
            tutorial_id="feature_tour",
            title_key="tutorials.feature_tour.title",
            description_key="tutorials.feature_tour.description",
            user_levels=[UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
            estimated_duration=180,
        )
        
        feature_tour.add_step(TutorialStep(
            step_id="welcome",
            title_key="tutorials.feature_tour.welcome.title",
            content_key="tutorials.feature_tour.welcome.content",
            auto_advance=True,
            auto_advance_delay=3000,
        ))
        
        feature_tour.add_step(TutorialStep(
            step_id="home_overview",
            title_key="tutorials.feature_tour.home.title",
            content_key="tutorials.feature_tour.home.content",
            target_widget="home_interface",
            delay_ms=1000,
        ))
        
        feature_tour.add_step(TutorialStep(
            step_id="server_cards",
            title_key="tutorials.feature_tour.servers.title",
            content_key="tutorials.feature_tour.servers.content",
            target_widget="server_cards_area",
            delay_ms=500,
        ))
        
        feature_tour.add_step(TutorialStep(
            step_id="quick_actions",
            title_key="tutorials.feature_tour.actions.title",
            content_key="tutorials.feature_tour.actions.content",
            target_widget="quick_action_bar",
            delay_ms=500,
        ))
        
        self.tutorials["feature_tour"] = feature_tour
        
        # First server setup tutorial
        server_setup = Tutorial(
            tutorial_id="first_server_setup",
            title_key="tutorials.server_setup.title",
            description_key="tutorials.server_setup.description",
            user_levels=[UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
            prerequisites=["completed_feature_tour"],
            estimated_duration=300,
        )
        
        server_setup.add_step(TutorialStep(
            step_id="navigate_launcher",
            title_key="tutorials.server_setup.navigate.title",
            content_key="tutorials.server_setup.navigate.content",
            target_widget="launcher_tab",
            action_required="click_launcher_tab",
        ))
        
        server_setup.add_step(TutorialStep(
            step_id="server_configuration",
            title_key="tutorials.server_setup.config.title",
            content_key="tutorials.server_setup.config.content",
            target_widget="server_config_area",
            delay_ms=1000,
        ))
        
        self.tutorials["first_server_setup"] = server_setup
        
        # Interface customization tutorial
        customization = Tutorial(
            tutorial_id="interface_customization",
            title_key="tutorials.customization.title",
            description_key="tutorials.customization.description",
            user_levels=[UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
            estimated_duration=240,
        )
        
        customization.add_step(TutorialStep(
            step_id="open_settings",
            title_key="tutorials.customization.settings.title",
            content_key="tutorials.customization.settings.content",
            target_widget="settings_tab",
            action_required="click_settings_tab",
        ))
        
        customization.add_step(TutorialStep(
            step_id="theme_selection",
            title_key="tutorials.customization.theme.title",
            content_key="tutorials.customization.theme.content",
            target_widget="theme_settings",
            delay_ms=1000,
        ))
        
        self.tutorials["interface_customization"] = customization
        
        # Advanced features tutorial
        advanced_features = Tutorial(
            tutorial_id="advanced_features",
            title_key="tutorials.advanced.title",
            description_key="tutorials.advanced.description",
            user_levels=[UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
            prerequisites=["completed_basic_tutorials"],
            estimated_duration=420,
        )
        
        advanced_features.add_step(TutorialStep(
            step_id="tools_overview",
            title_key="tutorials.advanced.tools.title",
            content_key="tutorials.advanced.tools.content",
            target_widget="tools_tab",
            delay_ms=1000,
        ))
        
        advanced_features.add_step(TutorialStep(
            step_id="module_development",
            title_key="tutorials.advanced.modules.title",
            content_key="tutorials.advanced.modules.content",
            target_widget="scaffold_tool",
            delay_ms=1000,
        ))
        
        self.tutorials["advanced_features"] = advanced_features

        # Interactive workflow tutorials
        workflow_tutorial = Tutorial(
            tutorial_id="interactive_workflow",
            title_key="tutorials.workflow.title",
            description_key="tutorials.workflow.description",
            user_levels=[UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
            estimated_duration=600,
        )

        workflow_tutorial.add_step(TutorialStep(
            step_id="workflow_intro",
            title_key="tutorials.workflow.intro.title",
            content_key="tutorials.workflow.intro.content",
            auto_advance=True,
            auto_advance_delay=4000,
        ))

        workflow_tutorial.add_step(TutorialStep(
            step_id="server_lifecycle",
            title_key="tutorials.workflow.lifecycle.title",
            content_key="tutorials.workflow.lifecycle.content",
            target_widget="server_cards_area",
            action_required="start_server",
            validation_func=lambda: self._validate_server_started(),
        ))

        workflow_tutorial.add_step(TutorialStep(
            step_id="monitoring_logs",
            title_key="tutorials.workflow.monitoring.title",
            content_key="tutorials.workflow.monitoring.content",
            target_widget="logs_section",
            action_required="view_logs",
            validation_func=lambda: self._validate_logs_viewed(),
        ))

        workflow_tutorial.add_step(TutorialStep(
            step_id="batch_operations",
            title_key="tutorials.workflow.batch.title",
            content_key="tutorials.workflow.batch.content",
            target_widget="quick_action_bar",
            action_required="use_batch_operation",
            validation_func=lambda: self._validate_batch_operation(),
        ))

        self.tutorials["interactive_workflow"] = workflow_tutorial

        # Module development tutorial
        module_dev_tutorial = Tutorial(
            tutorial_id="module_development",
            title_key="tutorials.module_dev.title",
            description_key="tutorials.module_dev.description",
            user_levels=[UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
            prerequisites=["used_tools_section"],
            estimated_duration=900,
        )

        module_dev_tutorial.add_step(TutorialStep(
            step_id="scaffold_intro",
            title_key="tutorials.module_dev.scaffold.title",
            content_key="tutorials.module_dev.scaffold.content",
            target_widget="scaffold_tool",
            delay_ms=1000,
        ))

        module_dev_tutorial.add_step(TutorialStep(
            step_id="create_module",
            title_key="tutorials.module_dev.create.title",
            content_key="tutorials.module_dev.create.content",
            target_widget="scaffold_form",
            action_required="create_module",
            validation_func=lambda: self._validate_module_created(),
        ))

        module_dev_tutorial.add_step(TutorialStep(
            step_id="test_module",
            title_key="tutorials.module_dev.test.title",
            content_key="tutorials.module_dev.test.content",
            target_widget="module_test_area",
            action_required="test_module",
            validation_func=lambda: self._validate_module_tested(),
        ))

        self.tutorials["module_development"] = module_dev_tutorial

        self.logger.info(f"Initialized {len(self.tutorials)} tutorials")
    
    def start_tutorial(self, tutorial_id: str) -> bool:
        """Start a specific tutorial"""
        if tutorial_id not in self.tutorials:
            self.logger.error(f"Tutorial not found: {tutorial_id}")
            return False
        
        tutorial = self.tutorials[tutorial_id]
        user_level = self.user_tracker.get_user_level()
        
        # Check if tutorial is applicable for user level
        if user_level not in tutorial.user_levels:
            self.logger.info(f"Tutorial {tutorial_id} not applicable for user level {user_level.value}")
            return False
        
        # Check prerequisites
        completed_actions = self.onboarding_manager.get_user_state_tracker().completed_actions
        for prereq in tutorial.prerequisites:
            if prereq not in completed_actions:
                self.logger.info(f"Tutorial {tutorial_id} prerequisite not met: {prereq}")
                return False
        
        # Stop any active tutorial
        if self.active_tutorial:
            self.cancel_tutorial()
        
        # Start the tutorial
        self.active_tutorial = tutorial
        tutorial.reset()
        tutorial.started = True
        
        self.tutorial_started.emit(tutorial_id)
        self.logger.info(f"Started tutorial: {tutorial_id}")
        
        # Show first step
        self._show_current_step()
        
        return True
    
    def _show_current_step(self) -> None:
        """Show the current tutorial step"""
        if not self.active_tutorial:
            return
        
        current_step = self.active_tutorial.get_current_step()
        if not current_step:
            self._complete_tutorial()
            return
        
        # Dismiss previous teaching tip
        if self.current_teaching_tip:
            self.current_teaching_tip.close()
            self.current_teaching_tip = None
        
        def show_step():
            try:
                title = current_step.get_title()
                content = current_step.get_content()
                
                # Find target widget
                target_widget = self._find_target_widget(current_step.target_widget)
                if not target_widget:
                    target_widget = self.main_window
                
                # Create teaching tip
                self.current_teaching_tip = TeachingTip.create(
                    target=target_widget,
                    icon=None,
                    title=title,
                    content=content,
                    isClosable=True,
                    tailPosition=TeachingTipTailPosition.BOTTOM,
                    parent=self.main_window
                )
                
                # Add navigation buttons if needed
                self._add_tutorial_navigation()
                
                # Emit step changed signal
                self.step_changed.emit(
                    self.active_tutorial.tutorial_id,
                    self.active_tutorial.current_step_index
                )
                
                # Setup auto-advance if enabled
                if current_step.auto_advance:
                    self.step_timer.start(current_step.auto_advance_delay)
                
                self.logger.debug(f"Showed tutorial step: {current_step.step_id}")
                
            except Exception as e:
                self.logger.error(f"Error showing tutorial step: {e}")
        
        # Show with delay if specified
        if current_step.delay_ms > 0:
            QTimer.singleShot(current_step.delay_ms, show_step)
        else:
            show_step()
    
    def _find_target_widget(self, widget_name: Optional[str]) -> Optional[QWidget]:
        """Find a target widget by name"""
        if not widget_name:
            return None
        
        # This would implement widget lookup logic
        # For now, return main window as fallback
        return self.main_window
    
    def _add_tutorial_navigation(self) -> None:
        """Add navigation buttons to the current teaching tip"""
        # This would add Previous/Next/Skip buttons to the teaching tip
        # Implementation depends on the specific UI framework capabilities
        pass
    
    def next_step(self) -> None:
        """Advance to the next tutorial step"""
        if not self.active_tutorial:
            return
        
        current_step = self.active_tutorial.get_current_step()
        if current_step:
            current_step.completed = True
            self.step_completed.emit(self.active_tutorial.tutorial_id, current_step.step_id)
        
        if self.active_tutorial.advance_step():
            self._show_current_step()
        else:
            self._complete_tutorial()
    
    def previous_step(self) -> None:
        """Go back to the previous tutorial step"""
        if not self.active_tutorial:
            return
        
        if self.active_tutorial.previous_step():
            self._show_current_step()
    
    def _advance_step_auto(self) -> None:
        """Auto-advance to next step"""
        self.next_step()
    
    def skip_step(self) -> None:
        """Skip the current tutorial step"""
        if not self.active_tutorial:
            return
        
        current_step = self.active_tutorial.get_current_step()
        if current_step:
            self.user_tracker.skip_tutorial(f"{self.active_tutorial.tutorial_id}_{current_step.step_id}")
        
        self.next_step()
    
    def cancel_tutorial(self) -> None:
        """Cancel the active tutorial"""
        if not self.active_tutorial:
            return
        
        tutorial_id = self.active_tutorial.tutorial_id
        
        # Cleanup
        if self.current_teaching_tip:
            self.current_teaching_tip.close()
            self.current_teaching_tip = None
        
        self.step_timer.stop()
        self.active_tutorial = None
        
        self.tutorial_cancelled.emit(tutorial_id)
        self.logger.info(f"Cancelled tutorial: {tutorial_id}")
    
    def _complete_tutorial(self) -> None:
        """Complete the active tutorial"""
        if not self.active_tutorial:
            return
        
        tutorial_id = self.active_tutorial.tutorial_id
        self.active_tutorial.completed = True
        
        # Track completion
        self.user_tracker.track_action(f"completed_tutorial_{tutorial_id}")
        
        # Cleanup
        if self.current_teaching_tip:
            self.current_teaching_tip.close()
            self.current_teaching_tip = None
        
        self.tutorial_completed.emit(tutorial_id)
        self.logger.info(f"Completed tutorial: {tutorial_id}")
        
        self.active_tutorial = None
    
    def get_available_tutorials(self) -> List[Dict[str, Any]]:
        """Get list of available tutorials for current user"""
        user_level = self.user_tracker.get_user_level()
        completed_actions = set()  # Would get from user tracker
        
        available = []
        for tutorial in self.tutorials.values():
            if user_level in tutorial.user_levels:
                # Check prerequisites
                prereqs_met = all(prereq in completed_actions for prereq in tutorial.prerequisites)
                
                available.append({
                    "id": tutorial.tutorial_id,
                    "title": tutorial.get_title(),
                    "description": tutorial.get_description(),
                    "duration": tutorial.estimated_duration,
                    "steps": len(tutorial.steps),
                    "prerequisites_met": prereqs_met,
                    "completed": tutorial.completed,
                })
        
        return available

    def get_tutorial_progress(self) -> Optional[Dict[str, Any]]:
        """Get progress of active tutorial"""
        if self.active_tutorial:
            return self.active_tutorial.get_progress()
        return None

    # Validation methods for interactive tutorials

    def _validate_server_started(self) -> bool:
        """Validate that a server has been started"""
        # This would check actual server state
        # For now, return True as placeholder
        return True

    def _validate_logs_viewed(self) -> bool:
        """Validate that logs have been viewed"""
        # This would check if logs interface was accessed
        return True

    def _validate_batch_operation(self) -> bool:
        """Validate that a batch operation was performed"""
        # This would check if batch operations were used
        return True

    def _validate_module_created(self) -> bool:
        """Validate that a module was created"""
        # This would check if module creation was completed
        return True

    def _validate_module_tested(self) -> bool:
        """Validate that a module was tested"""
        # This would check if module testing was performed
        return True

    def validate_step_action(self, action: str) -> bool:
        """Validate a specific step action"""
        if not self.active_tutorial:
            return False

        current_step = self.active_tutorial.get_current_step()
        if not current_step:
            return False

        # Check if this is the required action
        if current_step.action_required == action:
            # Validate the action if validation function exists
            if current_step.validation_func:
                if current_step.validation_func():
                    self.logger.info(f"Step action validated: {action}")
                    self.next_step()
                    return True
                else:
                    self.logger.warning(f"Step action validation failed: {action}")
                    return False
            else:
                # No validation function, just advance
                self.logger.info(f"Step action completed: {action}")
                self.next_step()
                return True

        return False

    def get_current_step_requirements(self) -> Optional[Dict[str, Any]]:
        """Get requirements for the current tutorial step"""
        if not self.active_tutorial:
            return None

        current_step = self.active_tutorial.get_current_step()
        if not current_step:
            return None

        return {
            "step_id": current_step.step_id,
            "title": current_step.get_title(),
            "content": current_step.get_content(),
            "target_widget": current_step.target_widget,
            "action_required": current_step.action_required,
            "has_validation": current_step.validation_func is not None,
            "auto_advance": current_step.auto_advance,
        }

    def highlight_target_widget(self, widget_name: str) -> None:
        """Highlight a target widget for tutorial guidance"""
        target_widget = self._find_target_widget(widget_name)
        if target_widget:
            # This would add visual highlighting to the widget
            # Implementation depends on the UI framework
            self.logger.debug(f"Highlighting widget: {widget_name}")

    def provide_step_hint(self) -> Optional[str]:
        """Provide a hint for the current step"""
        if not self.active_tutorial:
            return None

        current_step = self.active_tutorial.get_current_step()
        if not current_step:
            return None

        # Generate contextual hints based on step requirements
        if current_step.action_required:
            hint_key = f"tutorials.hints.{current_step.action_required}"
            return tr(hint_key, default=f"Try to {current_step.action_required.replace('_', ' ')}")

        return None

    def get_tutorial_statistics(self) -> Dict[str, Any]:
        """Get statistics about tutorial usage"""
        total_tutorials = len(self.tutorials)
        completed_tutorials = len([t for t in self.tutorials.values() if t.completed])

        step_completion_rates = {}
        for tutorial in self.tutorials.values():
            if tutorial.steps:
                completed_steps = len([s for s in tutorial.steps if s.completed])
                step_completion_rates[tutorial.tutorial_id] = {
                    "completed_steps": completed_steps,
                    "total_steps": len(tutorial.steps),
                    "completion_rate": (completed_steps / len(tutorial.steps)) * 100
                }

        return {
            "total_tutorials": total_tutorials,
            "completed_tutorials": completed_tutorials,
            "completion_rate": (completed_tutorials / total_tutorials) * 100 if total_tutorials > 0 else 0,
            "step_completion_rates": step_completion_rates,
            "active_tutorial": self.active_tutorial.tutorial_id if self.active_tutorial else None,
        }
