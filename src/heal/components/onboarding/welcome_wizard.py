"""
Welcome Wizard

Interactive welcome wizard for first-time users with step-by-step setup,
feature introduction, and personalized configuration.
"""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
    TitleLabel,
    Wizard,
    WizardPage,
)

from ...common.i18n_ui import tr
from ...common.logging_config import get_logger
from ...models.config import cfg
from .user_state_tracker import OnboardingStep, UserLevel


class WelcomePage(WizardPage):
    """Welcome page of the wizard"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(tr("onboarding.welcome.title", default="Welcome to HEAL"))
        self.setSubTitle(tr("onboarding.welcome.subtitle", 
                           default="Let's get you started with Hello ElementAstro Launcher"))
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Welcome message
        welcome_label = TitleLabel(tr("onboarding.welcome.message", 
                                    default="Welcome to HEAL!"))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        description = BodyLabel(tr("onboarding.welcome.description",
                                 default="HEAL is a powerful launcher and management system for astronomical software. "
                                        "This wizard will help you set up the application and learn about its features."))
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Features overview
        features_card = CardWidget()
        features_layout = QVBoxLayout(features_card)
        
        features_title = SubtitleLabel(tr("onboarding.welcome.features_title", 
                                        default="What you can do with HEAL:"))
        features_layout.addWidget(features_title)
        
        features = [
            tr("onboarding.welcome.feature_1", default="• Manage and launch astronomical software"),
            tr("onboarding.welcome.feature_2", default="• Monitor server status and performance"),
            tr("onboarding.welcome.feature_3", default="• Download and install modules"),
            tr("onboarding.welcome.feature_4", default="• Configure development environments"),
            tr("onboarding.welcome.feature_5", default="• Access powerful tools and utilities"),
        ]
        
        for feature in features:
            feature_label = BodyLabel(feature)
            features_layout.addWidget(feature_label)
        
        layout.addWidget(welcome_label)
        layout.addWidget(description)
        layout.addWidget(features_card)
        layout.addStretch()


class UserLevelPage(WizardPage):
    """User level selection page"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(tr("onboarding.user_level.title", default="Tell us about yourself"))
        self.setSubTitle(tr("onboarding.user_level.subtitle", 
                           default="This helps us customize your experience"))
        
        self.selected_level = UserLevel.BEGINNER
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # User level selection
        level_label = SubtitleLabel(tr("onboarding.user_level.question", 
                                     default="What's your experience level?"))
        layout.addWidget(level_label)
        
        # Level options
        self.beginner_radio = QRadioButton(tr("onboarding.user_level.beginner", 
                                            default="Beginner - New to astronomical software"))
        self.beginner_radio.setChecked(True)
        self.beginner_radio.toggled.connect(lambda: self._set_level(UserLevel.BEGINNER))
        
        self.intermediate_radio = QRadioButton(tr("onboarding.user_level.intermediate", 
                                                default="Intermediate - Some experience with similar tools"))
        self.intermediate_radio.toggled.connect(lambda: self._set_level(UserLevel.INTERMEDIATE))
        
        self.advanced_radio = QRadioButton(tr("onboarding.user_level.advanced", 
                                            default="Advanced - Experienced user, minimal guidance needed"))
        self.advanced_radio.toggled.connect(lambda: self._set_level(UserLevel.ADVANCED))
        
        layout.addWidget(self.beginner_radio)
        layout.addWidget(self.intermediate_radio)
        layout.addWidget(self.advanced_radio)
        
        # Level descriptions
        descriptions_card = CardWidget()
        desc_layout = QVBoxLayout(descriptions_card)
        
        desc_title = StrongBodyLabel(tr("onboarding.user_level.what_this_means", 
                                      default="What this means:"))
        desc_layout.addWidget(desc_title)
        
        beginner_desc = BodyLabel(tr("onboarding.user_level.beginner_desc",
                                   default="• More detailed explanations and tips\n"
                                          "• Step-by-step tutorials\n"
                                          "• Helpful tooltips and guidance"))
        
        intermediate_desc = BodyLabel(tr("onboarding.user_level.intermediate_desc",
                                       default="• Balanced guidance and freedom\n"
                                              "• Optional tutorials\n"
                                              "• Contextual help when needed"))
        
        advanced_desc = BodyLabel(tr("onboarding.user_level.advanced_desc",
                                   default="• Minimal guidance and tips\n"
                                          "• Quick access to advanced features\n"
                                          "• Streamlined interface"))
        
        desc_layout.addWidget(beginner_desc)
        desc_layout.addWidget(intermediate_desc)
        desc_layout.addWidget(advanced_desc)
        
        layout.addWidget(descriptions_card)
        layout.addStretch()
    
    def _set_level(self, level: UserLevel):
        self.selected_level = level
    
    def get_selected_level(self) -> UserLevel:
        return self.selected_level


class PreferencesPage(WizardPage):
    """User preferences configuration page"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(tr("onboarding.preferences.title", default="Customize your experience"))
        self.setSubTitle(tr("onboarding.preferences.subtitle", 
                           default="Configure how HEAL behaves"))
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Help preferences
        help_card = CardWidget()
        help_layout = QVBoxLayout(help_card)
        
        help_title = SubtitleLabel(tr("onboarding.preferences.help_title", 
                                    default="Help & Guidance"))
        help_layout.addWidget(help_title)
        
        self.show_tips_cb = QCheckBox(tr("onboarding.preferences.show_tips", 
                                       default="Show helpful tips"))
        self.show_tips_cb.setChecked(True)
        
        self.show_tooltips_cb = QCheckBox(tr("onboarding.preferences.show_tooltips", 
                                           default="Show tooltips on hover"))
        self.show_tooltips_cb.setChecked(True)
        
        self.contextual_help_cb = QCheckBox(tr("onboarding.preferences.contextual_help", 
                                             default="Show contextual help"))
        self.contextual_help_cb.setChecked(True)
        
        help_layout.addWidget(self.show_tips_cb)
        help_layout.addWidget(self.show_tooltips_cb)
        help_layout.addWidget(self.contextual_help_cb)
        
        # Tutorial speed
        speed_card = CardWidget()
        speed_layout = QVBoxLayout(speed_card)
        
        speed_title = SubtitleLabel(tr("onboarding.preferences.tutorial_speed", 
                                     default="Tutorial Speed"))
        speed_layout.addWidget(speed_title)
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems([
            tr("onboarding.preferences.speed_slow", default="Slow - Take your time"),
            tr("onboarding.preferences.speed_normal", default="Normal - Balanced pace"),
            tr("onboarding.preferences.speed_fast", default="Fast - Quick overview"),
        ])
        self.speed_combo.setCurrentIndex(1)  # Normal by default
        
        speed_layout.addWidget(self.speed_combo)
        
        layout.addWidget(help_card)
        layout.addWidget(speed_card)
        layout.addStretch()
    
    def get_preferences(self) -> Dict[str, Any]:
        speed_map = {0: "slow", 1: "normal", 2: "fast"}
        
        return {
            "show_tips": self.show_tips_cb.isChecked(),
            "show_tooltips": self.show_tooltips_cb.isChecked(),
            "show_contextual_help": self.contextual_help_cb.isChecked(),
            "tutorial_speed": speed_map.get(self.speed_combo.currentIndex(), "normal")
        }


class CompletionPage(WizardPage):
    """Completion page of the wizard"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(tr("onboarding.completion.title", default="You're all set!"))
        self.setSubTitle(tr("onboarding.completion.subtitle", 
                           default="HEAL is ready to use"))
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Completion message
        completion_label = TitleLabel(tr("onboarding.completion.message", 
                                       default="Welcome to HEAL!"))
        completion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        description = BodyLabel(tr("onboarding.completion.description",
                                 default="Your setup is complete. You can now start using HEAL to manage "
                                        "your astronomical software and servers."))
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Next steps
        next_steps_card = CardWidget()
        steps_layout = QVBoxLayout(next_steps_card)
        
        steps_title = SubtitleLabel(tr("onboarding.completion.next_steps", 
                                     default="What's next?"))
        steps_layout.addWidget(steps_title)
        
        steps = [
            tr("onboarding.completion.step_1", default="• Explore the home dashboard"),
            tr("onboarding.completion.step_2", default="• Configure your first server"),
            tr("onboarding.completion.step_3", default="• Download modules from the store"),
            tr("onboarding.completion.step_4", default="• Check out the tools section"),
        ]
        
        for step in steps:
            step_label = BodyLabel(step)
            steps_layout.addWidget(step_label)
        
        layout.addWidget(completion_label)
        layout.addWidget(description)
        layout.addWidget(next_steps_card)
        layout.addStretch()


class WelcomeWizard(Wizard):
    """Main welcome wizard for first-time users"""
    
    # Signals
    wizard_completed = Signal(dict)  # user_preferences
    wizard_cancelled = Signal()
    
    def __init__(self, parent: QWidget, onboarding_manager: Any):
        super().__init__(parent)
        self.onboarding_manager = onboarding_manager
        self.logger = get_logger("welcome_wizard", module="WelcomeWizard")
        
        self._init_wizard()
        self._connect_signals()
    
    def _init_wizard(self):
        """Initialize the wizard"""
        self.setWindowTitle(tr("onboarding.wizard.title", default="Welcome to HEAL"))
        self.setFixedSize(800, 600)
        
        # Add pages
        self.welcome_page = WelcomePage()
        self.user_level_page = UserLevelPage()
        self.preferences_page = PreferencesPage()
        self.completion_page = CompletionPage()
        
        self.addPage(self.welcome_page)
        self.addPage(self.user_level_page)
        self.addPage(self.preferences_page)
        self.addPage(self.completion_page)
        
        # Customize buttons
        self.setButtonText(Wizard.WizardButton.NextButton, 
                          tr("onboarding.wizard.next", default="Next"))
        self.setButtonText(Wizard.WizardButton.BackButton, 
                          tr("onboarding.wizard.back", default="Back"))
        self.setButtonText(Wizard.WizardButton.FinishButton, 
                          tr("onboarding.wizard.finish", default="Get Started"))
        self.setButtonText(Wizard.WizardButton.CancelButton, 
                          tr("onboarding.wizard.cancel", default="Skip"))
    
    def _connect_signals(self):
        """Connect wizard signals"""
        self.accepted.connect(self._handle_completion)
        self.rejected.connect(self._handle_cancellation)
    
    def _handle_completion(self):
        """Handle wizard completion"""
        try:
            # Collect user preferences
            user_level = self.user_level_page.get_selected_level()
            preferences = self.preferences_page.get_preferences()
            
            user_data = {
                "user_level": user_level,
                "preferences": preferences
            }
            
            # Apply user preferences
            self._apply_user_preferences(user_level, preferences)
            
            # Mark welcome step as complete
            self.onboarding_manager.get_user_state_tracker().complete_onboarding_step(
                OnboardingStep.WELCOME
            )
            
            # Track completion
            self.onboarding_manager.track_user_action("welcome_wizard_completed", user_data)
            
            self.wizard_completed.emit(user_data)
            self.logger.info("Welcome wizard completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error completing welcome wizard: {e}")
    
    def _handle_cancellation(self):
        """Handle wizard cancellation"""
        self.onboarding_manager.track_user_action("welcome_wizard_cancelled")
        self.wizard_cancelled.emit()
        self.logger.info("Welcome wizard cancelled")
    
    def _apply_user_preferences(self, user_level: UserLevel, preferences: Dict[str, Any]):
        """Apply user preferences to the system"""
        try:
            # Set user level
            self.onboarding_manager.get_user_state_tracker().set_user_level(user_level)
            
            # Update help preferences
            self.onboarding_manager.get_user_state_tracker().update_help_preferences(preferences)
            
            self.logger.info(f"Applied user preferences: level={user_level.value}, prefs={preferences}")
            
        except Exception as e:
            self.logger.error(f"Error applying user preferences: {e}")
    
    def start(self):
        """Start the welcome wizard"""
        self.logger.info("Starting welcome wizard")
        self.show()
        self.raise_()
        self.activateWindow()
