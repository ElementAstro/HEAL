"""
Resources Package

Contains all static resources for the HEAL application including:
- Images and icons
- Stylesheets (QSS files)
- Translation files
- Data files
- Audio files

This package provides a centralized resource management system with:
- Automatic resource discovery and validation
- Caching for improved performance
- Theme-aware resource loading
- Fallback mechanisms for missing resources
- Resource integrity checking
"""

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Resource directory paths
RESOURCES_DIR = Path(__file__).parent
IMAGES_DIR = RESOURCES_DIR / "images"
ICONS_DIR = RESOURCES_DIR / "icons"
APP_ICONS_DIR = RESOURCES_DIR / "app_icons"
STYLES_DIR = RESOURCES_DIR / "styles"
TRANSLATIONS_DIR = RESOURCES_DIR / "translations"
DATA_DIR = RESOURCES_DIR / "data"
AUDIO_DIR = RESOURCES_DIR / "audio"
PATCHES_DIR = RESOURCES_DIR / "patches"
WARP_DIR = RESOURCES_DIR / "warp"


def get_resource_path(resource_type: str, filename: str) -> Path:
    """
    Get the full path to a resource file.

    Args:
        resource_type: Type of resource ('images', 'icons', 'styles', etc.)
        filename: Name of the resource file

    Returns:
        Path to the resource file
    """
    resource_dirs = {
        "images": IMAGES_DIR,
        "icons": ICONS_DIR,
        "app_icons": APP_ICONS_DIR,
        "styles": STYLES_DIR,
        "translations": TRANSLATIONS_DIR,
        "data": DATA_DIR,
        "audio": AUDIO_DIR,
        "patches": PATCHES_DIR,
        "warp": WARP_DIR,
    }

    if resource_type not in resource_dirs:
        raise ValueError(f"Unknown resource type: {resource_type}")

    return resource_dirs[resource_type] / filename


def resource_exists(resource_type: str, filename: str) -> bool:
    """Check if a resource file exists."""
    try:
        return get_resource_path(resource_type, filename).exists()
    except ValueError:
        return False


class ResourceManager:
    """
    Advanced resource management system for HEAL application.

    Provides centralized resource loading with caching, validation,
    and theme support.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, Any] = {}
        self._theme = "light"  # Default theme

        # Resource directories mapping
        self.resource_dirs = {
            "images": IMAGES_DIR,
            "icons": ICONS_DIR,
            "app_icons": APP_ICONS_DIR,
            "styles": STYLES_DIR,
            "translations": TRANSLATIONS_DIR,
            "data": DATA_DIR,
            "audio": AUDIO_DIR,
            "patches": PATCHES_DIR,
            "warp": WARP_DIR,
        }

    @lru_cache(maxsize=128)
    def get_resource_path(
        self, resource_type: str, filename: str, theme: Optional[str] = None
    ) -> Path:
        """
        Get the full path to a resource file with theme support.

        Args:
            resource_type: Type of resource ('images', 'icons', 'styles', etc.)
            filename: Name of the resource file
            theme: Optional theme name (for theme-aware resources)

        Returns:
            Path to the resource file

        Raises:
            ValueError: If resource type is unknown
            FileNotFoundError: If resource file doesn't exist
        """
        if resource_type not in self.resource_dirs:
            raise ValueError(f"Unknown resource type: {resource_type}")

        base_path = self.resource_dirs[resource_type]

        # Handle theme-aware resources (mainly styles)
        if theme and resource_type == "styles":
            resource_path = base_path / theme / filename
            if not resource_path.exists():
                # Fallback to default theme
                resource_path = base_path / self._theme / filename
        else:
            resource_path = base_path / filename

        if not resource_path.exists():
            self.logger.warning(f"Resource not found: {resource_path}")
            raise FileNotFoundError(f"Resource not found: {resource_path}")

        return resource_path

    def load_text_resource(
        self, resource_type: str, filename: str, encoding: str = "utf-8"
    ) -> str:
        """
        Load a text resource file.

        Args:
            resource_type: Type of resource
            filename: Name of the file
            encoding: Text encoding (default: utf-8)

        Returns:
            Content of the text file
        """
        cache_key = f"{resource_type}:{filename}:text"

        if cache_key in self._cache:
            return str(self._cache[cache_key])

        try:
            resource_path = self.get_resource_path(resource_type, filename)
            with open(resource_path, "r", encoding=encoding) as f:
                content = f.read()

            self._cache[cache_key] = content
            return content

        except Exception as e:
            self.logger.error(f"Failed to load text resource {filename}: {e}")
            raise

    def load_json_resource(self, resource_type: str, filename: str) -> Dict[str, Any]:
        """
        Load a JSON resource file.

        Args:
            resource_type: Type of resource
            filename: Name of the JSON file

        Returns:
            Parsed JSON data
        """
        cache_key = f"{resource_type}:{filename}:json"

        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if isinstance(cached_data, dict):
                return cached_data
            return {}

        try:
            content = self.load_text_resource(resource_type, filename)
            data = json.loads(content)

            if not isinstance(data, dict):
                raise ValueError(f"Expected dict from JSON file {filename}, got {type(data)}")

            self._cache[cache_key] = data
            return data

        except Exception as e:
            self.logger.error(f"Failed to load JSON resource {filename}: {e}")
            raise

    def load_stylesheet(self, filename: str, theme: Optional[str] = None) -> str:
        """
        Load a QSS stylesheet with theme support.

        Args:
            filename: Name of the stylesheet file
            theme: Optional theme name

        Returns:
            Stylesheet content
        """
        try:
            return self.load_text_resource("styles", filename, theme or self._theme)
        except FileNotFoundError:
            # Try without theme
            return self.load_text_resource("styles", filename)

    def set_theme(self, theme: str) -> None:
        """
        Set the current theme for resource loading.

        Args:
            theme: Theme name (e.g., 'light', 'dark')
        """
        self._theme = theme
        # Clear cache to reload theme-dependent resources
        self._cache.clear()

    def get_theme(self) -> str:
        """Get the current theme."""
        return self._theme

    def clear_cache(self) -> None:
        """Clear the resource cache."""
        self._cache.clear()
        self.get_resource_path.cache_clear()

    def validate_resources(self) -> Dict[str, bool]:
        """
        Validate that all critical resources exist.

        Returns:
            Dictionary mapping resource paths to existence status
        """
        critical_resources = {
            "styles/light": ["home_interface.qss", "setting_interface.qss"],
            "styles/dark": ["home_interface.qss", "setting_interface.qss"],
            "images": ["icon.ico", "atom.png"],
            "translations": ["en_US.qm", "zh_TW.qm"],
        }

        results = {}

        for resource_type, filenames in critical_resources.items():
            for filename in filenames:
                try:
                    if "/" in resource_type:
                        # Handle theme-specific resources
                        base_type, theme = resource_type.split("/")
                        path = self.get_resource_path(base_type, filename, theme)
                    else:
                        path = self.get_resource_path(resource_type, filename)

                    results[str(path)] = path.exists()

                except Exception as e:
                    self.logger.error(
                        f"Error validating resource {resource_type}/{filename}: {e}"
                    )
                    results[f"{resource_type}/{filename}"] = False

        return results


# Global resource manager instance
resource_manager = ResourceManager()

__all__: list[str] = [
    "RESOURCES_DIR",
    "IMAGES_DIR",
    "ICONS_DIR",
    "APP_ICONS_DIR",
    "STYLES_DIR",
    "TRANSLATIONS_DIR",
    "DATA_DIR",
    "AUDIO_DIR",
    "PATCHES_DIR",
    "WARP_DIR",
    "get_resource_path",
    "resource_exists",
    "ResourceManager",
    "resource_manager",
]
