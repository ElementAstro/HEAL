"""
Download components package
Contains all modular components for the download interface
"""

from .card_manager import DownloadCardManager
from .category_grid import CategoryGridWidget
from .config_manager import DownloadConfigManager
from .download_handler import DownloadHandler
from .featured_downloads import FeaturedDownloadsSection
from .header_section import DownloadHeaderSection
from .navigation_manager import DownloadNavigationManager
from .search_manager import DownloadSearchManager

__all__: list[str] = [
    "DownloadSearchManager",
    "DownloadCardManager",
    "DownloadHandler",
    "DownloadConfigManager",
    "DownloadNavigationManager",
    "DownloadHeaderSection",
    "FeaturedDownloadsSection",
    "CategoryGridWidget",
]
