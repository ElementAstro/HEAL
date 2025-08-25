"""Setting interface components package with performance optimizations."""

from .about_component import About, AboutBackground
from .advanced_filters import AdvancedFilter, AdvancedFilterManager, AdvancedFilterType
from .enhanced_settings_manager import EnhancedSettingsManager
from .error_handler import SettingsErrorHandler, get_error_handler
from .layout_manager import SettingsLayoutManager
from .lazy_settings import LazySettingsManager, get_lazy_manager
from .performance_manager import SettingsPerformanceManager, get_performance_manager
from .search_engine import (
    FilterType,
    SearchResult,
    SearchType,
    SettingItem,
    SettingsSearchEngine,
)
from .search_integration import SettingsSearchIntegrator, get_search_integrator
from .search_ui import SearchFilterWidget, SearchResultWidget, SettingsSearchWidget
from .setting_cards import LineEditSettingCardPort
from .settings_manager import SettingsManager

__all__: list[str] = [
    "LineEditSettingCardPort",
    "AboutBackground",
    "About",
    "SettingsManager",
    "SettingsLayoutManager",
    "SettingsPerformanceManager",
    "get_performance_manager",
    "LazySettingsManager",
    "get_lazy_manager",
    "SettingsErrorHandler",
    "get_error_handler",
    "EnhancedSettingsManager",
    "SettingsSearchEngine",
    "SettingItem",
    "SearchResult",
    "SearchType",
    "FilterType",
    "SettingsSearchWidget",
    "SearchResultWidget",
    "SearchFilterWidget",
    "SettingsSearchIntegrator",
    "get_search_integrator",
    "AdvancedFilterManager",
    "AdvancedFilter",
    "AdvancedFilterType",
]
