"""
Onboarding Components Package

Contains consolidated components for managing user onboarding, first-time user experience,
tutorials, and intelligent guidance systems. Components have been reorganized to reduce
granularity while maintaining clear separation of concerns.
"""

# Core onboarding system - consolidated manager
from .onboarding_manager import OnboardingManager

# User state and progress tracking
from .user_state_tracker import UserStateTracker

# Welcome and tutorial systems - consolidated
from .tutorial_system import TutorialSystem, WelcomeWizard

# Help and guidance systems - consolidated
from .help_system import HelpSystem, ContextualHelpSystem, DocumentationIntegration

# Smart features - consolidated
from .smart_features import SmartTipSystem, RecommendationEngine, ProgressiveFeatureDiscovery

__all__ = [
    # Core onboarding management
    "OnboardingManager",
    "UserStateTracker",

    # Tutorial and welcome systems
    "TutorialSystem",
    "WelcomeWizard",

    # Help and documentation systems
    "HelpSystem",
    "ContextualHelpSystem",
    "DocumentationIntegration",

    # Smart features and recommendations
    "SmartTipSystem",
    "RecommendationEngine",
    "ProgressiveFeatureDiscovery",
]
