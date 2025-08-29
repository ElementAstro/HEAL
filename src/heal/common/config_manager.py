"""
Enhanced Configuration Manager

Provides centralized configuration management with:
- Automatic path resolution for the new package structure
- Resource path validation and correction
- Configuration migration and upgrade support
- Environment-specific configuration handling
- Configuration backup and recovery
- Configuration caching for improved performance
"""

import json
import os
import shutil
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

from ..resources import resource_manager
from .config_validator import ConfigValidator, ValidationLevel, ValidationResult
from .logging_config import get_logger

logger = get_logger(__name__)


class ConfigType(Enum):
    """Configuration file types."""

    MAIN = "main"  # Main application configuration
    AUTO = "auto"  # Auto-saved settings
    VERSION = "version"  # Version information
    SERVER = "server"  # Server configurations
    USER = "user"  # User-specific settings


@dataclass
class ConfigCacheEntry:
    """Configuration cache entry."""

    data: Dict[str, Any]
    file_hash: str
    last_modified: float
    cache_time: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)


@dataclass
class ConfigPath:
    """Configuration path information."""

    config_type: ConfigType
    filename: str
    default_path: Path
    backup_path: Optional[Path] = None
    schema_path: Optional[Path] = None


class ConfigManager:
    """
    Enhanced configuration manager for HEAL application.

    Manages all configuration files with automatic path resolution,
    validation, migration support, and performance caching.
    """

    def __init__(self, config_dir: Optional[Path] = None, enable_cache: bool = True) -> None:
        """
        Initialize the configuration manager.

        Args:
            config_dir: Optional custom configuration directory
            enable_cache: Whether to enable configuration caching
        """
        self.logger = get_logger(self.__class__.__name__)

        # Set up configuration directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path("config")

        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)

        # Set up backup directory
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # Cache configuration
        self.enable_cache = enable_cache
        self.config_cache: Dict[ConfigType, ConfigCacheEntry] = {}
        self.cache_ttl = 300.0  # 5 minutes cache TTL
        self.max_cache_size = 50  # Maximum number of cached configs

        # Configuration file definitions
        self.config_paths = {
            ConfigType.MAIN: ConfigPath(
                ConfigType.MAIN,
                "config.json",
                self.config_dir / "config.json",
                self.backup_dir / "config.json.bak",
            ),
            ConfigType.AUTO: ConfigPath(
                ConfigType.AUTO,
                "auto.json",
                self.config_dir / "auto.json",
                self.backup_dir / "auto.json.bak",
            ),
            ConfigType.VERSION: ConfigPath(
                ConfigType.VERSION, "version.json", self.config_dir / "version.json"
            ),
            ConfigType.SERVER: ConfigPath(
                ConfigType.SERVER,
                "server.json",
                self.config_dir / "server.json",
                self.backup_dir / "server.json.bak",
            ),
            ConfigType.USER: ConfigPath(
                ConfigType.USER,
                "user.json",
                self.config_dir / "user.json",
                self.backup_dir / "user.json.bak",
            ),
        }

        # Initialize validator
        self.validator = ConfigValidator()

        # Initialize configurations
        self._initialize_configs()

    def _initialize_configs(self) -> None:
        """Initialize configuration files if they don't exist."""
        for config_type, config_path in self.config_paths.items():
            if not config_path.default_path.exists():
                self._create_default_config(config_type)

    def _create_default_config(self, config_type: ConfigType) -> None:
        """Create a default configuration file."""
        default_configs: Dict[ConfigType, Dict[str, Any]] = {
            ConfigType.MAIN: {
                "APP_NAME": "HEAL - Hello ElementAstro Launcher",
                "APP_VERSION": "1.0.0",
                "LANGUAGE": "en_US",
                "THEME": "auto",
                "PROXY": {"enabled": False, "host": "127.0.0.1", "port": 8080},
                "PATHS": {
                    "resources": "src/heal/resources",
                    "logs": "logs",
                    "cache": "cache",
                    "temp": "temp",
                },
                "FEATURES": {
                    "auto_copy": True,
                    "use_login": False,
                    "use_audio": True,
                    "use_remote": False,
                },
            },
            ConfigType.AUTO: {
                "window": {"geometry": None, "state": None, "theme": "auto"},
                "recent_files": [],
                "last_opened": None,
            },
            ConfigType.VERSION: {
                "APP_VERSION": "1.0.0",
                "BUILD_DATE": "2025-01-01",
                "BUILD_TYPE": "release",
                "COMMIT_HASH": None,
            },
            ConfigType.SERVER: {
                "servers": [],
                "default_server": None,
                "connection_timeout": 30,
            },
            ConfigType.USER: {
                "username": None,
                "preferences": {},
                "custom_settings": {},
                "onboarding": {
                    "is_first_time": True,
                    "completed_steps": [],
                    "last_login": None,
                    "app_launches": 0,
                    "onboarding_version": "1.0.0",
                    "user_level": "beginner",  # beginner, intermediate, advanced
                    "preferred_features": [],
                    "skipped_tutorials": [],
                    "help_preferences": {
                        "show_tips": True,
                        "show_tooltips": True,
                        "show_contextual_help": True,
                        "tutorial_speed": "normal"  # slow, normal, fast
                    }
                },
            },
        }

        if config_type in default_configs:
            config_path = self.config_paths[config_type]
            self._save_config_data(
                config_path.default_path, default_configs[config_type]
            )
            self.logger.info(
                f"Created default configuration: {config_path.filename}")

    def _save_config_data(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save configuration data to file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save configuration {file_path}: {e}")
            raise

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception:
            return ""

    def _is_cache_valid(self, config_type: ConfigType, file_path: Path) -> bool:
        """Check if cached configuration is still valid."""
        if not self.enable_cache or config_type not in self.config_cache:
            return False

        cache_entry = self.config_cache[config_type]
        current_time = time.time()

        # Check TTL
        if current_time - cache_entry.cache_time > self.cache_ttl:
            return False

        # Check file modification
        try:
            file_stat = file_path.stat()
            if file_stat.st_mtime != cache_entry.last_modified:
                return False
        except Exception:
            return False

        # Check file hash for extra safety
        current_hash = self._calculate_file_hash(file_path)
        if current_hash != cache_entry.file_hash:
            return False

        return True

    def _update_cache(self, config_type: ConfigType, file_path: Path, data: Dict[str, Any]) -> None:
        """Update configuration cache."""
        if not self.enable_cache:
            return

        try:
            file_stat = file_path.stat()
            file_hash = self._calculate_file_hash(file_path)
            current_time = time.time()

            # Clean old cache entries if cache is full
            if len(self.config_cache) >= self.max_cache_size:
                self._cleanup_cache()

            self.config_cache[config_type] = ConfigCacheEntry(
                data=data.copy(),
                file_hash=file_hash,
                last_modified=file_stat.st_mtime,
                cache_time=current_time,
                access_count=1,
                last_access=current_time
            )

            self.logger.debug(f"Updated cache for {config_type.value}")

        except Exception as e:
            self.logger.warning(f"Failed to update cache for {config_type.value}: {e}")

    def _cleanup_cache(self) -> None:
        """Clean up old cache entries."""
        if len(self.config_cache) < self.max_cache_size:
            return

        # Remove entries that haven't been accessed recently
        current_time = time.time()
        entries_to_remove = []

        for config_type, cache_entry in self.config_cache.items():
            if current_time - cache_entry.last_access > self.cache_ttl * 2:
                entries_to_remove.append(config_type)

        for config_type in entries_to_remove:
            del self.config_cache[config_type]
            self.logger.debug(f"Removed stale cache entry for {config_type.value}")

    def _load_config_data(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration data from file with caching support."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                else:
                    raise ValueError(
                        f"Configuration file {file_path} does not contain a JSON object")
        except Exception as e:
            self.logger.error(f"Failed to load configuration {file_path}: {e}")
            raise

    def get_config(self, config_type: ConfigType) -> Dict[str, Any]:
        """
        Get configuration data with caching support.

        Args:
            config_type: Type of configuration to retrieve

        Returns:
            Configuration data dictionary
        """
        config_path = self.config_paths[config_type]
        file_path = config_path.default_path

        # Check cache first
        if self._is_cache_valid(config_type, file_path):
            cache_entry = self.config_cache[config_type]
            cache_entry.access_count += 1
            cache_entry.last_access = time.time()
            self.logger.debug(f"Cache hit for {config_type.value}")
            return cache_entry.data.copy()

        # Load from file and update cache
        self.logger.debug(f"Cache miss for {config_type.value}, loading from file")
        data = self._load_config_data(file_path)
        self._update_cache(config_type, file_path, data)

        return data

    def set_config(
        self, config_type: ConfigType, data: Dict[str, Any], backup: bool = True
    ) -> None:
        """
        Set configuration data and update cache.

        Args:
            config_type: Type of configuration to set
            data: Configuration data to save
            backup: Whether to create a backup before saving
        """
        config_path = self.config_paths[config_type]

        # Create backup if requested and file exists
        if backup and config_path.default_path.exists() and config_path.backup_path:
            shutil.copy2(config_path.default_path, config_path.backup_path)

        # Save new configuration
        self._save_config_data(config_path.default_path, data)

        # Update cache with new data
        self._update_cache(config_type, config_path.default_path, data)

        self.logger.info(f"Updated configuration: {config_path.filename}")

    def get_config_value(
        self, config_type: ConfigType, key: str, default: Any | None = None
    ) -> Any:
        """
        Get a specific configuration value.

        Args:
            config_type: Type of configuration
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        try:
            config = self.get_config(config_type)

            # Handle dot notation for nested keys
            keys = key.split(".")
            value = config
            for k in keys:
                value = value[k]

            return value

        except (KeyError, TypeError):
            return default

    def set_config_value(
        self, config_type: ConfigType, key: str, value: Any, backup: bool = True
    ) -> None:
        """
        Set a specific configuration value.

        Args:
            config_type: Type of configuration
            key: Configuration key (supports dot notation for nested keys)
            value: Value to set
            backup: Whether to create a backup before saving
        """
        config = self.get_config(config_type)

        # Handle dot notation for nested keys
        keys = key.split(".")
        current = config

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the value
        current[keys[-1]] = value

        # Save the updated configuration
        self.set_config(config_type, config, backup)

    def validate_all_configs(
        self, level: ValidationLevel = ValidationLevel.NORMAL
    ) -> Dict[ConfigType, ValidationResult]:
        """
        Validate all configuration files.

        Args:
            level: Validation level

        Returns:
            Dictionary mapping config types to validation results
        """
        results = {}

        for config_type, config_path in self.config_paths.items():
            if config_path.default_path.exists():
                try:
                    config_data = self._load_config_data(
                        config_path.default_path)
                    # Convert config_data to file path for validation
                    result = self.validator.validate_file(
                        str(config_path.default_path))
                    results[config_type] = result

                    if not result.is_valid:
                        self.logger.warning(
                            f"Configuration validation failed for {config_path.filename}"
                        )
                        for error in result.errors:
                            self.logger.error(f"  {error}")

                except Exception as e:
                    self.logger.error(
                        f"Failed to validate {config_path.filename}: {e}")
                    results[config_type] = ValidationResult(
                        is_valid=False,
                        errors=[str(e)],
                        warnings=[],
                        info=[],
                        fixed_issues=[],
                    )

        return results

    def update_resource_paths(self) -> None:
        """Update configuration files to use the new resource structure."""
        try:
            # Update main configuration with correct resource paths
            main_config = self.get_config(ConfigType.MAIN)

            # Update paths section
            if "PATHS" in main_config:
                main_config["PATHS"]["resources"] = "src/heal/resources"
                main_config["PATHS"]["styles"] = "src/heal/resources/styles"
                main_config["PATHS"]["images"] = "src/heal/resources/images"
                main_config["PATHS"]["translations"] = "src/heal/resources/translations"

                self.set_config(ConfigType.MAIN, main_config)
                self.logger.info(
                    "Updated resource paths in main configuration")

        except Exception as e:
            self.logger.error(f"Failed to update resource paths: {e}")

    def clear_cache(self, config_type: Optional[ConfigType] = None) -> None:
        """
        Clear configuration cache.

        Args:
            config_type: Specific config type to clear, or None to clear all
        """
        if config_type:
            if config_type in self.config_cache:
                del self.config_cache[config_type]
                self.logger.debug(f"Cleared cache for {config_type.value}")
        else:
            self.config_cache.clear()
            self.logger.debug("Cleared all configuration cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get configuration cache statistics."""
        if not self.enable_cache:
            return {"cache_enabled": False}

        total_access_count = sum(entry.access_count for entry in self.config_cache.values())
        cache_entries = []

        for config_type, entry in self.config_cache.items():
            cache_entries.append({
                "config_type": config_type.value,
                "access_count": entry.access_count,
                "last_access": entry.last_access,
                "cache_age": time.time() - entry.cache_time,
                "file_hash": entry.file_hash[:8]  # First 8 chars for display
            })

        return {
            "cache_enabled": True,
            "total_entries": len(self.config_cache),
            "max_cache_size": self.max_cache_size,
            "cache_ttl": self.cache_ttl,
            "total_access_count": total_access_count,
            "cache_entries": cache_entries
        }

    def preload_configs(self, config_types: Optional[List[ConfigType]] = None) -> Dict[ConfigType, bool]:
        """
        Preload configurations into cache.

        Args:
            config_types: List of config types to preload, or None for all

        Returns:
            Dictionary mapping config types to success status
        """
        if not self.enable_cache:
            return {}

        if config_types is None:
            config_types = list(ConfigType)

        results = {}
        for config_type in config_types:
            try:
                self.get_config(config_type)  # This will load and cache the config
                results[config_type] = True
                self.logger.debug(f"Preloaded config {config_type.value}")
            except Exception as e:
                results[config_type] = False
                self.logger.warning(f"Failed to preload config {config_type.value}: {e}")

        return results

    # Compatibility methods for tests
    def load_config(self, config_type: ConfigType) -> Optional[Dict[str, Any]]:
        """
        Load configuration data (compatibility method).

        Args:
            config_type: Type of configuration to load

        Returns:
            Configuration data or None if not found
        """
        try:
            return self.get_config(config_type)
        except Exception as e:
            self.logger.error(f"Failed to load config {config_type.value}: {e}")
            return None

    def save_config(self, config_type: ConfigType, data: Dict[str, Any]) -> bool:
        """
        Save configuration data (compatibility method).

        Args:
            config_type: Type of configuration to save
            data: Configuration data to save

        Returns:
            True if successful, False otherwise
        """
        try:
            self.set_config(config_type, data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save config {config_type.value}: {e}")
            return False

    def get_cached_config(self, config_type: ConfigType) -> Optional[Dict[str, Any]]:
        """
        Get cached configuration data (compatibility method).

        Args:
            config_type: Type of configuration to retrieve

        Returns:
            Cached configuration data or None if not cached
        """
        if not self.enable_cache or config_type not in self.config_cache:
            return None

        cache_entry = self.config_cache[config_type]
        cache_entry.access_count += 1
        cache_entry.last_access = time.time()

        return cache_entry.data


# Global configuration manager instance with caching enabled
config_manager = ConfigManager(enable_cache=True)
