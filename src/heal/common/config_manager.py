"""
Enhanced Configuration Manager

Provides centralized configuration management with:
- Automatic path resolution for the new package structure
- Resource path validation and correction
- Configuration migration and upgrade support
- Environment-specific configuration handling
- Configuration backup and recovery
"""

import json
import os
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
    validation, and migration support.
    """

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """
        Initialize the configuration manager.

        Args:
            config_dir: Optional custom configuration directory
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
            },
        }

        if config_type in default_configs:
            config_path = self.config_paths[config_type]
            self._save_config_data(
                config_path.default_path, default_configs[config_type]
            )
            self.logger.info(f"Created default configuration: {config_path.filename}")

    def _save_config_data(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save configuration data to file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save configuration {file_path}: {e}")
            raise

    def _load_config_data(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration data from file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                else:
                    raise ValueError(f"Configuration file {file_path} does not contain a JSON object")
        except Exception as e:
            self.logger.error(f"Failed to load configuration {file_path}: {e}")
            raise

    def get_config(self, config_type: ConfigType) -> Dict[str, Any]:
        """
        Get configuration data.

        Args:
            config_type: Type of configuration to retrieve

        Returns:
            Configuration data dictionary
        """
        config_path = self.config_paths[config_type]
        return self._load_config_data(config_path.default_path)

    def set_config(
        self, config_type: ConfigType, data: Dict[str, Any], backup: bool = True
    ) -> None:
        """
        Set configuration data.

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
                    config_data = self._load_config_data(config_path.default_path)
                    # Convert config_data to file path for validation
                    result = self.validator.validate_file(str(config_path.default_path))
                    results[config_type] = result

                    if not result.is_valid:
                        self.logger.warning(
                            f"Configuration validation failed for {config_path.filename}"
                        )
                        for error in result.errors:
                            self.logger.error(f"  {error}")

                except Exception as e:
                    self.logger.error(f"Failed to validate {config_path.filename}: {e}")
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
                self.logger.info("Updated resource paths in main configuration")

        except Exception as e:
            self.logger.error(f"Failed to update resource paths: {e}")


# Global configuration manager instance
config_manager = ConfigManager()
