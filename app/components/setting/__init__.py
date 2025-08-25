"""Setting interface components package with performance optimizations."""

from .setting_cards import LineEditSettingCardPort
from .about_component import AboutBackground, About
from .settings_manager import SettingsManager
from .layout_manager import SettingsLayoutManager
from .performance_manager import SettingsPerformanceManager, get_performance_manager
from .lazy_settings import LazySettingsManager, get_lazy_manager
from .error_handler import SettingsErrorHandler, get_error_handler
from .enhanced_settings_manager import EnhancedSettingsManager
from .search_engine import SettingsSearchEngine, SettingItem, SearchResult, SearchType, FilterType
from .search_ui import SettingsSearchWidget, SearchResultWidget, SearchFilterWidget
from .search_integration import SettingsSearchIntegrator, get_search_integrator
from .advanced_filters import AdvancedFilterManager, AdvancedFilter, AdvancedFilterType

__all__ = [
    'LineEditSettingCardPort',
    'AboutBackground',
    'About',
    'SettingsManager',
    'SettingsLayoutManager',
    'SettingsPerformanceManager',
    'get_performance_manager',
    'LazySettingsManager',
    'get_lazy_manager',
    'SettingsErrorHandler',
    'get_error_handler',
    'EnhancedSettingsManager',
    'SettingsSearchEngine',
    'SettingItem',
    'SearchResult',
    'SearchType',
    'FilterType',
    'SettingsSearchWidget',
    'SearchResultWidget',
    'SearchFilterWidget',
    'SettingsSearchIntegrator',
    'get_search_integrator',
    'AdvancedFilterManager',
    'AdvancedFilter',
    'AdvancedFilterType'
]
