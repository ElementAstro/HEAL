"""
Environment Components Package

Contains consolidated components for managing and configuring the development environment,
including platform detection, tool status management, and environment setup.
Components have been reorganized to reduce complexity while maintaining clear interfaces.
"""

# Core environment management - consolidated controller
from .environment_controller import EnvironmentController, EnvironmentUICoordinator

# Platform and tool detection
from .platform_detector import PlatformDetector
from .tool_status_manager import ToolStatusManager

# UI Components - unified card system
from .unified_cards import (
    UnifiedEnvironmentCard,
    EnvironmentCardFactory,
    EnvironmentCardManager,
    CardType,
    CardPriority,
    CardAction
)

# Legacy cards - for backward compatibility
from .enhanced_cards import EnvironmentStatusCard, SmartToolCard, ToolCategorySection, QuickActionPanel
from .environment_cards import HyperlinkCardEnvironment, PrimaryPushSettingCardDownload

# Legacy managers - for backward compatibility
from .config_manager import EnvironmentConfigManager
from .database_manager import EnvironmentDatabaseManager
from .navigation_manager import EnvironmentNavigationManager
from .signal_manager import EnvironmentSignalManager

__all__: list[str] = [
    # Core environment management
    "EnvironmentController",
    "EnvironmentUICoordinator",

    # Platform and tool detection
    "PlatformDetector",
    "ToolStatusManager",

    # Unified card system
    "UnifiedEnvironmentCard",
    "EnvironmentCardFactory",
    "EnvironmentCardManager",
    "CardType",
    "CardPriority",
    "CardAction",

    # Legacy UI components (backward compatibility)
    "EnvironmentStatusCard",
    "SmartToolCard",
    "ToolCategorySection",
    "QuickActionPanel",
    "HyperlinkCardEnvironment",
    "PrimaryPushSettingCardDownload",

    # Legacy managers (backward compatibility)
    "EnvironmentConfigManager",
    "EnvironmentDatabaseManager",
    "EnvironmentNavigationManager",
    "EnvironmentSignalManager",
]
