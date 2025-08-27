"""
Onboarding Components Package

Contains components for managing user onboarding, first-time user experience,
tutorials, and intelligent guidance systems.
"""

from .onboarding_manager import OnboardingManager
from .user_state_tracker import UserStateTracker
from .welcome_wizard import WelcomeWizard
from .contextual_help import ContextualHelpSystem
from .tutorial_system import TutorialSystem
from .smart_tip_system import SmartTipSystem
from .recommendation_engine import RecommendationEngine
from .feature_discovery import ProgressiveFeatureDiscovery
from .documentation_integration import DocumentationIntegration

__all__ = [
    "OnboardingManager",
    "UserStateTracker",
    "WelcomeWizard",
    "ContextualHelpSystem",
    "TutorialSystem",
    "SmartTipSystem",
    "RecommendationEngine",
    "ProgressiveFeatureDiscovery",
    "DocumentationIntegration",
]
