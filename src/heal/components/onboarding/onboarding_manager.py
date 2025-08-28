"""
Onboarding Manager

Central manager for coordinating user onboarding experience, including
welcome wizard, tutorials, and progressive feature discovery.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QWidget

from src.heal.common.logging_config import get_logger
from .user_state_tracker import OnboardingStep, UserLevel, UserStateTracker
from .advanced_config_integration import (
    get_configuration_integrator, ConfigurationIntegrator
)
from .user_journey_tracker import (
    get_journey_tracker, UserJourneyTracker, EventType
)
from .documentation_integration import DocumentationIntegration
from .enhanced_help_system import show_help_system


class OnboardingManager(QObject):
    """Manages the overall onboarding experience"""
    
    # Signals
    onboarding_started = Signal()
    onboarding_completed = Signal()
    step_changed = Signal(str)  # OnboardingStep
    welcome_wizard_requested = Signal()
    tutorial_requested = Signal(str)  # tutorial_id
    
    def __init__(self, main_window: QWidget, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger("onboarding_manager", module="OnboardingManager")
        self.main_window = main_window

        # Initialize configuration integration
        self.config_integrator = get_configuration_integrator()
        self.config_manager = self.config_integrator.config_manager

        # Initialize journey tracking
        self.journey_tracker = get_journey_tracker()
        self.user_session_id = None

        # Initialize documentation system
        self.documentation_integration = DocumentationIntegration(self)
        self.help_system_window = None
        
        # Initialize components
        self.user_tracker = UserStateTracker(self)
        self.current_step: Optional[OnboardingStep] = None
        self.onboarding_active = False

        # Integrate user tracker with configuration system
        self.config_integrator.integrate_user_tracker(self.user_tracker)
        
        # Lazy-loaded components
        self._welcome_wizard: Optional[Any] = None
        self._contextual_help: Optional[Any] = None
        self._tutorial_system: Optional[Any] = None
        self._smart_tip_system: Optional[Any] = None
        self._recommendation_engine: Optional[Any] = None
        self._feature_discovery: Optional[Any] = None
        self._documentation_integration: Optional[Any] = None
        
        # Connect signals
        self._connect_signals()

        # Initialize onboarding state
        self._init_onboarding_state()

        # Register this manager with configuration integrator
        self.config_integrator.register_onboarding_component("onboarding_manager", self)

        # Start journey tracking session
        self._start_journey_tracking()
    
    def _connect_signals(self) -> None:
        """Connect internal signals"""
        self.user_tracker.first_time_user_detected.connect(self._handle_first_time_user)
        self.user_tracker.returning_user_detected.connect(self._handle_returning_user)
        self.user_tracker.onboarding_step_completed.connect(self._handle_step_completed)
        self.user_tracker.user_level_changed.connect(self._handle_user_level_changed)
    
    def _init_onboarding_state(self) -> None:
        """Initialize onboarding state"""
        if self.user_tracker.is_first_time_user():
            self.current_step = self.user_tracker.get_next_onboarding_step()
            self.logger.info(f"Onboarding initialized for first-time user, next step: {self.current_step}")
        else:
            # Check if there are incomplete steps for returning users
            next_step = self.user_tracker.get_next_onboarding_step()
            if next_step and next_step != OnboardingStep.COMPLETION:
                self.current_step = next_step
                self.logger.info(f"Incomplete onboarding detected, next step: {self.current_step}")
    
    def _handle_first_time_user(self) -> None:
        """Handle first-time user detection"""
        self.logger.info("First-time user detected, preparing onboarding")
        
        # Delay onboarding start to allow UI to fully load
        QTimer.singleShot(1000, self._start_onboarding)
    
    def _handle_returning_user(self) -> None:
        """Handle returning user detection"""
        self.logger.info("Returning user detected")
        
        # Check if user wants to see tips or has incomplete onboarding
        if self.current_step and self.current_step != OnboardingStep.COMPLETION:
            self._offer_continue_onboarding()
        else:
            self._setup_returning_user_experience()
    
    def _start_onboarding(self) -> None:
        """Start the onboarding process"""
        if self.onboarding_active:
            return
        
        self.onboarding_active = True
        self.onboarding_started.emit()
        
        # Track onboarding start
        self.user_tracker.track_action("onboarding_started")
        
        # Start with welcome wizard
        self.welcome_wizard_requested.emit()
        
        self.logger.info("Onboarding started")
    
    def _offer_continue_onboarding(self) -> None:
        """Offer to continue incomplete onboarding"""
        # This would show a dialog asking if user wants to continue
        # For now, we'll just log and continue
        self.logger.info("Offering to continue incomplete onboarding")
        self._start_onboarding()
    
    def _setup_returning_user_experience(self) -> None:
        """Setup experience for returning users"""
        self.logger.info("Setting up returning user experience")
        
        # Enable contextual help based on user preferences
        if self.user_tracker.should_show_contextual_help():
            self._ensure_contextual_help()
        
        # Track returning user
        self.user_tracker.track_action("returning_user_session_start")
    
    def _handle_step_completed(self, step_name: str) -> None:
        """Handle onboarding step completion"""
        try:
            completed_step = OnboardingStep(step_name)
            self.logger.info(f"Onboarding step completed: {completed_step.value}")
            
            # Move to next step
            next_step = self.user_tracker.get_next_onboarding_step()
            if next_step:
                self.current_step = next_step
                self.step_changed.emit(next_step.value)
                self._process_next_step(next_step)
            else:
                # Onboarding complete
                self._complete_onboarding()
                
        except ValueError:
            self.logger.error(f"Invalid onboarding step: {step_name}")
    
    def _process_next_step(self, step: OnboardingStep) -> None:
        """Process the next onboarding step"""
        self.logger.info(f"Processing onboarding step: {step.value}")
        
        if step == OnboardingStep.WELCOME:
            self.welcome_wizard_requested.emit()
        elif step == OnboardingStep.FEATURE_TOUR:
            self.tutorial_requested.emit("feature_tour")
        elif step == OnboardingStep.FIRST_SERVER:
            self.tutorial_requested.emit("first_server_setup")
        elif step == OnboardingStep.CUSTOMIZATION:
            self.tutorial_requested.emit("interface_customization")
        elif step == OnboardingStep.ADVANCED_FEATURES:
            self.tutorial_requested.emit("advanced_features")
    
    def _complete_onboarding(self) -> None:
        """Complete the onboarding process"""
        self.onboarding_active = False
        self.current_step = None
        
        # Mark onboarding as complete
        self.user_tracker.mark_onboarding_complete()
        
        # Track completion
        self.user_tracker.track_action("onboarding_completed")
        
        # Emit completion signal
        self.onboarding_completed.emit()
        
        self.logger.info("Onboarding completed successfully")
    
    def _handle_user_level_changed(self, new_level: str) -> None:
        """Handle user level changes"""
        self.logger.info(f"User level changed to: {new_level}")
        
        # Adjust help and guidance based on new level
        try:
            level = UserLevel(new_level)
            self._adjust_experience_for_level(level)
        except ValueError:
            self.logger.error(f"Invalid user level: {new_level}")
    
    def _adjust_experience_for_level(self, level: UserLevel) -> None:
        """Adjust user experience based on user level"""
        if level == UserLevel.BEGINNER:
            # Enable all help features
            self.user_tracker.update_help_preferences({
                "show_tips": True,
                "show_tooltips": True,
                "show_contextual_help": True,
                "tutorial_speed": "slow"
            })
        elif level == UserLevel.INTERMEDIATE:
            # Moderate help
            self.user_tracker.update_help_preferences({
                "show_tips": True,
                "show_tooltips": False,
                "show_contextual_help": True,
                "tutorial_speed": "normal"
            })
        elif level == UserLevel.ADVANCED:
            # Minimal help
            self.user_tracker.update_help_preferences({
                "show_tips": False,
                "show_tooltips": False,
                "show_contextual_help": False,
                "tutorial_speed": "fast"
            })
    
    def _ensure_welcome_wizard(self) -> Any:
        """Lazy load welcome wizard"""
        if self._welcome_wizard is None:
            from .welcome_wizard import WelcomeWizard
            self._welcome_wizard = WelcomeWizard(self.main_window, self)
        return self._welcome_wizard
    
    def _ensure_contextual_help(self) -> Any:
        """Lazy load contextual help system"""
        if self._contextual_help is None:
            from .contextual_help import ContextualHelpSystem
            self._contextual_help = ContextualHelpSystem(self.main_window, self)
        return self._contextual_help
    
    def _ensure_tutorial_system(self) -> Any:
        """Lazy load tutorial system"""
        if self._tutorial_system is None:
            from .tutorial_system import TutorialSystem
            self._tutorial_system = TutorialSystem(self.main_window, self)
        return self._tutorial_system

    def _ensure_smart_tip_system(self) -> Any:
        """Lazy load smart tip system"""
        if self._smart_tip_system is None:
            from .smart_tip_system import SmartTipSystem
            self._smart_tip_system = SmartTipSystem(self.user_tracker, self)
        return self._smart_tip_system

    def _ensure_recommendation_engine(self) -> Any:
        """Lazy load recommendation engine"""
        if self._recommendation_engine is None:
            from .recommendation_engine import RecommendationEngine
            self._recommendation_engine = RecommendationEngine(self.user_tracker, self)
        return self._recommendation_engine

    def _ensure_feature_discovery(self) -> Any:
        """Lazy load feature discovery system"""
        if self._feature_discovery is None:
            from .feature_discovery import ProgressiveFeatureDiscovery
            self._feature_discovery = ProgressiveFeatureDiscovery(self.user_tracker, self.main_window, self)
        return self._feature_discovery

    def _ensure_documentation_integration(self) -> Any:
        """Lazy load documentation integration"""
        if self._documentation_integration is None:
            from .documentation_integration import DocumentationIntegration
            self._documentation_integration = DocumentationIntegration(self.user_tracker, self.main_window, self)
        return self._documentation_integration
    
    # Public API
    
    def start_welcome_wizard(self) -> None:
        """Start the welcome wizard"""
        wizard = self._ensure_welcome_wizard()
        wizard.start()
    
    def start_tutorial(self, tutorial_id: str) -> None:
        """Start a specific tutorial"""
        tutorial_system = self._ensure_tutorial_system()
        tutorial_system.start_tutorial(tutorial_id)
    
    def complete_current_step(self) -> None:
        """Mark current onboarding step as complete"""
        if self.current_step:
            self.user_tracker.complete_onboarding_step(self.current_step)
    
    def skip_current_step(self) -> None:
        """Skip current onboarding step"""
        if self.current_step:
            self.logger.info(f"Skipping onboarding step: {self.current_step.value}")
            self.user_tracker.track_action("onboarding_step_skipped", {"step": self.current_step.value})
            self.complete_current_step()
    
    def restart_onboarding(self) -> None:
        """Restart onboarding from the beginning"""
        self.logger.info("Restarting onboarding")
        self.user_tracker.reset_onboarding()
        self._init_onboarding_state()
        self._start_onboarding()
    
    def get_onboarding_progress(self) -> Dict[str, Any]:
        """Get current onboarding progress"""
        completed_steps = self.user_tracker.get_completed_steps()
        total_steps = len(OnboardingStep)
        
        return {
            "current_step": self.current_step.value if self.current_step else None,
            "completed_steps": [step.value for step in completed_steps],
            "progress_percentage": (len(completed_steps) / total_steps) * 100,
            "is_active": self.onboarding_active,
            "user_level": self.user_tracker.get_user_level().value,
        }
    
    def track_user_action(self, action: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Track a user action for analytics"""
        self.user_tracker.track_action(action, context)
    
    def track_feature_usage(self, feature: str) -> None:
        """Track feature usage"""
        self.user_tracker.track_feature_usage(feature)
    
    def get_user_state_tracker(self) -> UserStateTracker:
        """Get the user state tracker"""
        return self.user_tracker

    def get_recommendations(self, limit: int = 5) -> List[Any]:
        """Get current recommendations for the user"""
        recommendation_engine = self._ensure_recommendation_engine()
        return recommendation_engine.get_active_recommendations(limit)

    def accept_recommendation(self, rec_id: str) -> bool:
        """Accept a recommendation"""
        recommendation_engine = self._ensure_recommendation_engine()
        return recommendation_engine.accept_recommendation(rec_id)

    def dismiss_recommendation(self, rec_id: str) -> bool:
        """Dismiss a recommendation"""
        recommendation_engine = self._ensure_recommendation_engine()
        return recommendation_engine.dismiss_recommendation(rec_id)

    def search_documentation(self, query: str) -> List[Any]:
        """Search documentation"""
        docs_integration = self._ensure_documentation_integration()
        return docs_integration.search_documentation(query)

    def get_contextual_documentation(self, context: str) -> List[Any]:
        """Get contextual documentation"""
        docs_integration = self._ensure_documentation_integration()
        return docs_integration.get_contextual_documentation(context)

    def open_documentation(self, doc_id: str, in_app: bool = True) -> bool:
        """Open documentation"""
        docs_integration = self._ensure_documentation_integration()
        return docs_integration.open_documentation(doc_id, in_app)

    def show_contextual_help(self, context: str, widget: Optional[Any] = None) -> None:
        """Show contextual help"""
        docs_integration = self._ensure_documentation_integration()
        docs_integration.show_contextual_help(context, widget)

    def force_discover_feature(self, feature_id: str) -> bool:
        """Force discovery of a specific feature"""
        feature_discovery = self._ensure_feature_discovery()
        return feature_discovery.force_discover_feature(feature_id)

    def get_discovery_progress(self) -> Dict[str, Any]:
        """Get feature discovery progress"""
        feature_discovery = self._ensure_feature_discovery()
        return feature_discovery.get_discovery_progress()

    def track_system_state(self, state_data: Dict[str, Any]) -> None:
        """Track system state for recommendations"""
        recommendation_engine = self._ensure_recommendation_engine()
        recommendation_engine.track_system_state(state_data)

    def track_error(self, error_type: str, error_context: Dict[str, Any]) -> None:
        """Track errors for analysis and recommendations"""
        recommendation_engine = self._ensure_recommendation_engine()
        recommendation_engine.track_error(error_type, error_context)

        # Also suggest documentation for the error
        docs_integration = self._ensure_documentation_integration()
        suggestions = docs_integration.suggest_documentation_for_error(error_type, str(error_context))

        if suggestions:
            self.logger.info(f"Suggested {len(suggestions)} documentation items for error: {error_type}")

    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all onboarding systems"""
        stats = {
            "user_state": self.user_tracker.get_user_summary(),
            "onboarding_progress": self.get_onboarding_progress(),
        }

        # Add statistics from other systems if they're initialized
        if self._smart_tip_system:
            stats["tips"] = self._smart_tip_system.get_tip_statistics()

        if self._recommendation_engine:
            stats["recommendations"] = self._recommendation_engine.get_recommendation_statistics()

        if self._feature_discovery:
            stats["feature_discovery"] = self._feature_discovery.get_discovery_progress()

        if self._contextual_help:
            stats["contextual_help"] = self._contextual_help.get_help_statistics()

        if self._tutorial_system:
            stats["tutorials"] = self._tutorial_system.get_tutorial_statistics()

        if self._documentation_integration:
            stats["documentation"] = self._documentation_integration.get_documentation_statistics()

        return stats

    # Configuration Management Methods

    def get_configuration_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config_manager.get(key, default)

    def set_configuration_value(self, key: str, value: Any,
                              scope: Optional[str] = None) -> bool:
        """Set configuration value"""
        from .advanced_config_integration import ConfigScope
        config_scope = ConfigScope.USER
        if scope:
            config_scope = ConfigScope(scope)
        return self.config_manager.set(key, value, scope=config_scope)

    def show_configuration_dialog(self) -> Any:
        """Show configuration dialog"""
        return self.config_integrator.show_configuration_dialog(self.main_window)

    def apply_onboarding_preset(self, preset_name: str) -> bool:
        """Apply an onboarding preset"""
        presets = self.config_integrator.get_available_presets()
        for preset in presets:
            if preset.name == preset_name:
                return self.config_integrator.apply_preset(preset)
        return False

    def get_available_presets(self) -> List[Dict[str, Any]]:
        """Get available onboarding presets"""
        presets = self.config_integrator.get_available_presets()
        return [
            {
                "name": preset.name,
                "description": preset.description,
                "user_type": preset.user_type.value,
                "features": preset.features_enabled
            }
            for preset in presets
        ]

    def export_configuration(self, file_path: str) -> bool:
        """Export configuration to file"""
        return self.config_integrator.export_user_configuration(file_path)

    def import_configuration(self, file_path: str, merge: bool = True) -> bool:
        """Import configuration from file"""
        return self.config_integrator.import_user_configuration(file_path, merge)

    def reset_configuration(self, scope: str = "user") -> None:
        """Reset configuration to defaults"""
        from .advanced_config_integration import ConfigScope
        config_scope = ConfigScope(scope)
        self.config_integrator.reset_to_defaults(config_scope)

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return self.config_integrator.get_configuration_summary()

    # Journey Tracking Methods

    def _start_journey_tracking(self):
        """Start journey tracking session"""
        try:
            # Generate user ID (could be based on system info, user profile, etc.)
            user_id = f"user_{hash(str(self.main_window))}"  # Simple user ID for demo
            self.user_session_id = self.journey_tracker.start_session(user_id)

            # Track onboarding system initialization
            self.journey_tracker.track_event(
                EventType.ONBOARDING_STARTED,
                context={
                    "system_version": "1.0.0",
                    "user_level": self.user_tracker.get_user_level().value,
                    "is_first_time": self.user_tracker.is_first_time_user()
                }
            )

            self.logger.info(f"Journey tracking started: session {self.user_session_id}")

        except Exception as e:
            self.logger.error(f"Failed to start journey tracking: {e}")

    def track_onboarding_event(self, event_type: EventType, context: Optional[Dict[str, Any]] = None):
        """Track an onboarding event"""
        try:
            self.journey_tracker.track_event(event_type, context or {})
        except Exception as e:
            self.logger.error(f"Failed to track event {event_type}: {e}")

    def track_step_completion(self, step: OnboardingStep):
        """Track onboarding step completion"""
        self.track_onboarding_event(
            EventType.ONBOARDING_STEP_COMPLETED,
            context={
                "step": step.value,
                "step_index": list(OnboardingStep).index(step),
                "completion_time": datetime.now().isoformat()
            }
        )

    def track_step_skip(self, step: OnboardingStep, reason: str = ""):
        """Track onboarding step skip"""
        self.track_onboarding_event(
            EventType.ONBOARDING_STEP_SKIPPED,
            context={
                "step": step.value,
                "step_index": list(OnboardingStep).index(step),
                "reason": reason
            }
        )

    def track_feature_discovery(self, feature_name: str, context: Optional[Dict[str, Any]] = None):
        """Track feature discovery"""
        self.track_onboarding_event(
            EventType.FEATURE_DISCOVERED,
            context={
                "feature_name": feature_name,
                **(context or {})
            }
        )

    def track_help_access(self, help_type: str, context: Optional[Dict[str, Any]] = None):
        """Track help access"""
        self.track_onboarding_event(
            EventType.HELP_ACCESSED,
            context={
                "help_type": help_type,
                **(context or {})
            }
        )

    def get_journey_insights(self, days: int = 30) -> List[Any]:
        """Get journey insights"""
        try:
            return self.journey_tracker.get_insights(days)
        except Exception as e:
            self.logger.error(f"Failed to get journey insights: {e}")
            return []

    def show_analytics_dashboard(self):
        """Show journey analytics dashboard"""
        try:
            from .journey_analytics_dashboard import show_analytics_dashboard
            return show_analytics_dashboard(self.main_window)
        except Exception as e:
            self.logger.error(f"Failed to show analytics dashboard: {e}")
            return None

    # Enhanced Documentation Methods

    def show_help_system(self):
        """Show the enhanced help system"""
        try:
            if not self.help_system_window:
                self.help_system_window = show_help_system(
                    self.documentation_integration,
                    self.user_tracker,
                    self.main_window
                )
            else:
                self.help_system_window.show()
                self.help_system_window.raise_()
                self.help_system_window.activateWindow()

            # Track help access
            self.track_help_access("help_system")

            return self.help_system_window

        except Exception as e:
            self.logger.error(f"Failed to show help system: {e}")
            return None

    def show_contextual_help(self, context: str):
        """Show contextual help for a specific context"""
        try:
            help_items = self.documentation_integration.get_contextual_help(
                context,
                self.user_tracker.get_user_level()
            )

            if help_items:
                # Show help system with contextual content
                help_system = self.show_help_system()
                if help_system and help_items:
                    help_system.display_content(help_items[0])

                # Track contextual help access
                self.track_help_access("contextual_help", {"context": context})

                return help_system
            else:
                self.logger.info(f"No contextual help found for: {context}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to show contextual help: {e}")
            return None

    def search_help(self, query: str):
        """Search help content and show results"""
        try:
            results = self.documentation_integration.search_documentation(
                query,
                user_level=self.user_tracker.get_user_level()
            )

            # Show help system with search results
            help_system = self.show_help_system()
            if help_system:
                help_system.perform_search(query, None, self.user_tracker.get_user_level())

            # Track help search
            self.track_help_access("help_search", {"query": query, "results_count": len(results)})

            return help_system

        except Exception as e:
            self.logger.error(f"Failed to search help: {e}")
            return None

    def get_help_suggestions(self, context: str = None) -> List[Any]:
        """Get help suggestions for current context"""
        try:
            if context:
                return self.documentation_integration.get_contextual_help(
                    context,
                    self.user_tracker.get_user_level()
                )
            else:
                # Get general suggestions based on user level and progress
                return self.documentation_integration.get_smart_suggestions(
                    self.user_tracker.get_user_level(),
                    self.user_tracker.get_completed_steps()
                )

        except Exception as e:
            self.logger.error(f"Failed to get help suggestions: {e}")
            return []

    def initialize_all_systems(self) -> None:
        """Initialize all onboarding systems (for testing or full setup)"""
        self.logger.info("Initializing all onboarding systems")

        self._ensure_smart_tip_system()
        self._ensure_contextual_help()
        self._ensure_tutorial_system()
        self._ensure_recommendation_engine()
        self._ensure_feature_discovery()
        self._ensure_documentation_integration()

        self.logger.info("All onboarding systems initialized")

    def shutdown_all_systems(self) -> None:
        """Shutdown all onboarding systems"""
        self.logger.info("Shutting down onboarding systems")

        if self._smart_tip_system:
            self._smart_tip_system.stop_rotation()

        # Clean up any active UI elements
        if self._contextual_help:
            self._contextual_help.dismiss_all_help()

        if self._tutorial_system and self._tutorial_system.active_tutorial:
            self._tutorial_system.cancel_tutorial()

        # Shutdown configuration system
        try:
            self.config_integrator.shutdown()
        except Exception as e:
            self.logger.error(f"Error shutting down configuration system: {e}")

        # End journey tracking session
        try:
            if self.user_session_id:
                self.journey_tracker.end_session()
                self.logger.info("Journey tracking session ended")
        except Exception as e:
            self.logger.error(f"Error ending journey tracking session: {e}")

        self.logger.info("Onboarding systems shutdown complete")
