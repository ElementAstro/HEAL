"""
Advanced Configuration System for HEAL Onboarding

Provides a highly customizable configuration system that supports:
- Deep customization of all onboarding aspects
- User-specific preferences and profiles
- Dynamic configuration updates
- Validation and schema enforcement
- Configuration inheritance and overrides
- Plugin-based extensibility
"""

import json
import yaml
from typing import Any, Dict, List, Optional, Union, Callable, Type
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import copy
from abc import ABC, abstractmethod

from src.heal.common.logging_config import get_logger

logger = get_logger(__name__)


class ConfigScope(Enum):
    """Configuration scope levels"""
    GLOBAL = "global"           # System-wide defaults
    USER = "user"              # User-specific settings
    SESSION = "session"        # Current session only
    TEMPORARY = "temporary"    # Temporary overrides


class ConfigFormat(Enum):
    """Supported configuration formats"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"


@dataclass
class ConfigValidationRule:
    """Configuration validation rule"""
    field_path: str
    validator: Callable[[Any], bool]
    error_message: str
    required: bool = False
    default_value: Any = None


@dataclass
class ConfigSchema:
    """Configuration schema definition"""
    name: str
    version: str
    description: str
    validation_rules: List[ConfigValidationRule] = field(default_factory=list)
    allowed_keys: Optional[List[str]] = None
    required_keys: List[str] = field(default_factory=list)


class ConfigProvider(ABC):
    """Abstract base class for configuration providers"""
    
    @abstractmethod
    def load(self, path: str) -> Dict[str, Any]:
        """Load configuration from source"""
        pass
    
    @abstractmethod
    def save(self, config: Dict[str, Any], path: str) -> bool:
        """Save configuration to source"""
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if configuration exists"""
        pass


class JSONConfigProvider(ConfigProvider):
    """JSON configuration provider"""
    
    def load(self, path: str) -> Dict[str, Any]:
        """Load JSON configuration"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load JSON config from {path}: {e}")
            return {}
    
    def save(self, config: Dict[str, Any], path: str) -> bool:
        """Save JSON configuration"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON config to {path}: {e}")
            return False
    
    def exists(self, path: str) -> bool:
        """Check if JSON file exists"""
        return Path(path).exists()


class YAMLConfigProvider(ConfigProvider):
    """YAML configuration provider"""
    
    def load(self, path: str) -> Dict[str, Any]:
        """Load YAML configuration"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning(f"Failed to load YAML config from {path}: {e}")
            return {}
    
    def save(self, config: Dict[str, Any], path: str) -> bool:
        """Save YAML configuration"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            logger.error(f"Failed to save YAML config to {path}: {e}")
            return False
    
    def exists(self, path: str) -> bool:
        """Check if YAML file exists"""
        return Path(path).exists()


class ConfigValidator:
    """Configuration validator with schema support"""
    
    def __init__(self):
        self.schemas: Dict[str, ConfigSchema] = {}
    
    def register_schema(self, schema: ConfigSchema) -> None:
        """Register a configuration schema"""
        self.schemas[schema.name] = schema
        logger.debug(f"Registered config schema: {schema.name} v{schema.version}")
    
    def validate(self, config: Dict[str, Any], schema_name: str) -> List[str]:
        """Validate configuration against schema"""
        errors = []
        
        if schema_name not in self.schemas:
            errors.append(f"Unknown schema: {schema_name}")
            return errors
        
        schema = self.schemas[schema_name]
        
        # Check required keys
        for required_key in schema.required_keys:
            if not self._has_nested_key(config, required_key):
                errors.append(f"Missing required key: {required_key}")
        
        # Check allowed keys
        if schema.allowed_keys:
            for key in self._get_all_keys(config):
                if key not in schema.allowed_keys:
                    errors.append(f"Unknown key: {key}")
        
        # Apply validation rules
        for rule in schema.validation_rules:
            value = self._get_nested_value(config, rule.field_path)
            
            if value is None and rule.required:
                errors.append(f"Required field missing: {rule.field_path}")
            elif value is not None and not rule.validator(value):
                errors.append(f"{rule.field_path}: {rule.error_message}")
        
        return errors
    
    def _has_nested_key(self, config: Dict[str, Any], key_path: str) -> bool:
        """Check if nested key exists"""
        keys = key_path.split('.')
        current = config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        
        return True
    
    def _get_nested_value(self, config: Dict[str, Any], key_path: str) -> Any:
        """Get nested value from configuration"""
        keys = key_path.split('.')
        current = config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        
        return current
    
    def _get_all_keys(self, config: Dict[str, Any], prefix: str = "") -> List[str]:
        """Get all keys from nested configuration"""
        keys = []
        
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)
            
            if isinstance(value, dict):
                keys.extend(self._get_all_keys(value, full_key))
        
        return keys


@dataclass
class ConfigurationProfile:
    """User configuration profile"""
    profile_id: str
    name: str
    description: str
    created_at: datetime
    last_modified: datetime
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        return {
            'profile_id': self.profile_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'last_modified': self.last_modified.isoformat(),
            'settings': self.settings,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigurationProfile':
        """Create profile from dictionary"""
        return cls(
            profile_id=data['profile_id'],
            name=data['name'],
            description=data['description'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_modified=datetime.fromisoformat(data['last_modified']),
            settings=data.get('settings', {}),
            metadata=data.get('metadata', {})
        )


class AdvancedConfigurationManager:
    """Advanced configuration manager with high customization support"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.home() / ".heal" / "config"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Configuration layers (priority order: highest to lowest)
        self.config_layers: Dict[ConfigScope, Dict[str, Any]] = {
            ConfigScope.TEMPORARY: {},
            ConfigScope.SESSION: {},
            ConfigScope.USER: {},
            ConfigScope.GLOBAL: {}
        }
        
        # Configuration providers
        self.providers: Dict[ConfigFormat, ConfigProvider] = {
            ConfigFormat.JSON: JSONConfigProvider(),
            ConfigFormat.YAML: YAMLConfigProvider()
        }
        
        # Validator and schemas
        self.validator = ConfigValidator()
        
        # Configuration profiles
        self.profiles: Dict[str, ConfigurationProfile] = {}
        self.active_profile_id: Optional[str] = None
        
        # Change listeners
        self.change_listeners: List[Callable[[str, Any, Any], None]] = []
        
        # Configuration cache
        self._config_cache: Dict[str, Any] = {}
        self._cache_timestamp = datetime.now()
        self._cache_ttl = timedelta(minutes=5)
        
        # Initialize with default schemas
        self._register_default_schemas()
        self._load_initial_configuration()
    
    def _register_default_schemas(self) -> None:
        """Register default configuration schemas"""
        # Onboarding schema
        onboarding_schema = ConfigSchema(
            name="onboarding",
            version="1.0.0",
            description="Onboarding system configuration",
            validation_rules=[
                ConfigValidationRule(
                    "user_level",
                    lambda x: x in ["beginner", "intermediate", "advanced"],
                    "User level must be beginner, intermediate, or advanced"
                ),
                ConfigValidationRule(
                    "help_preferences.tutorial_speed",
                    lambda x: x in ["slow", "normal", "fast"],
                    "Tutorial speed must be slow, normal, or fast"
                )
            ],
            required_keys=["is_first_time", "user_level"]
        )
        self.validator.register_schema(onboarding_schema)
        
        # UI customization schema
        ui_schema = ConfigSchema(
            name="ui_customization",
            version="1.0.0",
            description="UI customization settings",
            validation_rules=[
                ConfigValidationRule(
                    "theme",
                    lambda x: x in ["light", "dark", "auto"],
                    "Theme must be light, dark, or auto"
                ),
                ConfigValidationRule(
                    "animation_speed",
                    lambda x: isinstance(x, (int, float)) and 0.1 <= x <= 3.0,
                    "Animation speed must be between 0.1 and 3.0"
                )
            ]
        )
        self.validator.register_schema(ui_schema)
    
    def _load_initial_configuration(self) -> None:
        """Load initial configuration from files"""
        # Load global configuration
        global_config_path = self.base_path / "global.json"
        if global_config_path.exists():
            self.config_layers[ConfigScope.GLOBAL] = self.providers[ConfigFormat.JSON].load(str(global_config_path))
        
        # Load user configuration
        user_config_path = self.base_path / "user.json"
        if user_config_path.exists():
            self.config_layers[ConfigScope.USER] = self.providers[ConfigFormat.JSON].load(str(user_config_path))
        
        # Load profiles
        self._load_profiles()
    
    def _load_profiles(self) -> None:
        """Load configuration profiles"""
        profiles_path = self.base_path / "profiles.json"
        if profiles_path.exists():
            try:
                profiles_data = self.providers[ConfigFormat.JSON].load(str(profiles_path))
                for profile_data in profiles_data.get('profiles', []):
                    profile = ConfigurationProfile.from_dict(profile_data)
                    self.profiles[profile.profile_id] = profile
                
                self.active_profile_id = profiles_data.get('active_profile_id')
                logger.info(f"Loaded {len(self.profiles)} configuration profiles")
            except Exception as e:
                logger.error(f"Failed to load profiles: {e}")
    
    def _save_profiles(self) -> None:
        """Save configuration profiles"""
        profiles_path = self.base_path / "profiles.json"
        try:
            profiles_data = {
                'active_profile_id': self.active_profile_id,
                'profiles': [profile.to_dict() for profile in self.profiles.values()]
            }
            self.providers[ConfigFormat.JSON].save(profiles_data, str(profiles_path))
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
    
    def get(self, key: str, default: Any = None, scope: Optional[ConfigScope] = None) -> Any:
        """Get configuration value with scope priority"""
        # Check cache first
        if self._is_cache_valid() and key in self._config_cache:
            return self._config_cache[key]
        
        # Search through scopes in priority order
        scopes_to_search = [scope] if scope else list(ConfigScope)
        
        for search_scope in scopes_to_search:
            value = self._get_nested_value(self.config_layers[search_scope], key)
            if value is not None:
                self._config_cache[key] = value
                return value
        
        # Check active profile
        if self.active_profile_id and self.active_profile_id in self.profiles:
            profile = self.profiles[self.active_profile_id]
            value = self._get_nested_value(profile.settings, key)
            if value is not None:
                self._config_cache[key] = value
                return value
        
        return default
    
    def set(self, key: str, value: Any, scope: ConfigScope = ConfigScope.USER, 
            validate: bool = True, persist: bool = True) -> bool:
        """Set configuration value"""
        try:
            # Validate if requested
            if validate:
                # Create temporary config for validation
                temp_config = copy.deepcopy(self.config_layers[scope])
                self._set_nested_value(temp_config, key, value)
                
                # Validate against relevant schemas
                errors = []
                for schema_name in self.validator.schemas:
                    schema_errors = self.validator.validate(temp_config, schema_name)
                    errors.extend(schema_errors)
                
                if errors:
                    logger.warning(f"Validation errors for {key}: {errors}")
                    return False
            
            # Get old value for change notification
            old_value = self.get(key)
            
            # Set the value
            self._set_nested_value(self.config_layers[scope], key, value)
            
            # Invalidate cache
            self._invalidate_cache()
            
            # Persist if requested
            if persist:
                self._persist_scope(scope)
            
            # Notify listeners
            self._notify_change_listeners(key, old_value, value)
            
            logger.debug(f"Set config {key} = {value} in scope {scope.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set config {key}: {e}")
            return False
    
    def _get_nested_value(self, config: Dict[str, Any], key_path: str) -> Any:
        """Get nested value from configuration"""
        keys = key_path.split('.')
        current = config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        
        return current
    
    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any) -> None:
        """Set nested value in configuration"""
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _persist_scope(self, scope: ConfigScope) -> None:
        """Persist configuration scope to file"""
        if scope == ConfigScope.GLOBAL:
            path = self.base_path / "global.json"
        elif scope == ConfigScope.USER:
            path = self.base_path / "user.json"
        else:
            return  # Session and temporary scopes are not persisted
        
        self.providers[ConfigFormat.JSON].save(self.config_layers[scope], str(path))
    
    def _is_cache_valid(self) -> bool:
        """Check if configuration cache is valid"""
        return datetime.now() - self._cache_timestamp < self._cache_ttl
    
    def _invalidate_cache(self) -> None:
        """Invalidate configuration cache"""
        self._config_cache.clear()
        self._cache_timestamp = datetime.now()
    
    def _notify_change_listeners(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify configuration change listeners"""
        for listener in self.change_listeners:
            try:
                listener(key, old_value, new_value)
            except Exception as e:
                logger.error(f"Error in config change listener: {e}")
    
    def add_change_listener(self, listener: Callable[[str, Any, Any], None]) -> None:
        """Add configuration change listener"""
        self.change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[str, Any, Any], None]) -> None:
        """Remove configuration change listener"""
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)
    
    def create_profile(self, name: str, description: str, 
                      settings: Optional[Dict[str, Any]] = None) -> str:
        """Create a new configuration profile"""
        import uuid
        profile_id = str(uuid.uuid4())
        
        profile = ConfigurationProfile(
            profile_id=profile_id,
            name=name,
            description=description,
            created_at=datetime.now(),
            last_modified=datetime.now(),
            settings=settings or {}
        )
        
        self.profiles[profile_id] = profile
        self._save_profiles()
        
        logger.info(f"Created configuration profile: {name} ({profile_id})")
        return profile_id
    
    def activate_profile(self, profile_id: str) -> bool:
        """Activate a configuration profile"""
        if profile_id not in self.profiles:
            logger.error(f"Profile not found: {profile_id}")
            return False
        
        self.active_profile_id = profile_id
        self._invalidate_cache()
        self._save_profiles()
        
        logger.info(f"Activated configuration profile: {profile_id}")
        return True
    
    def get_profile(self, profile_id: str) -> Optional[ConfigurationProfile]:
        """Get configuration profile"""
        return self.profiles.get(profile_id)
    
    def list_profiles(self) -> List[ConfigurationProfile]:
        """List all configuration profiles"""
        return list(self.profiles.values())
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a configuration profile"""
        if profile_id not in self.profiles:
            return False
        
        del self.profiles[profile_id]
        
        if self.active_profile_id == profile_id:
            self.active_profile_id = None
        
        self._save_profiles()
        logger.info(f"Deleted configuration profile: {profile_id}")
        return True
    
    def export_configuration(self, path: str, format: ConfigFormat = ConfigFormat.JSON,
                           include_profiles: bool = True) -> bool:
        """Export configuration to file"""
        try:
            export_data = {
                'global': self.config_layers[ConfigScope.GLOBAL],
                'user': self.config_layers[ConfigScope.USER],
                'export_timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            if include_profiles:
                export_data['profiles'] = [profile.to_dict() for profile in self.profiles.values()]
                export_data['active_profile_id'] = self.active_profile_id
            
            return self.providers[format].save(export_data, path)
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_configuration(self, path: str, format: ConfigFormat = ConfigFormat.JSON,
                           merge: bool = True) -> bool:
        """Import configuration from file"""
        try:
            import_data = self.providers[format].load(path)
            
            if not merge:
                # Clear existing configuration
                self.config_layers[ConfigScope.GLOBAL].clear()
                self.config_layers[ConfigScope.USER].clear()
                self.profiles.clear()
            
            # Import configuration layers
            if 'global' in import_data:
                if merge:
                    self.config_layers[ConfigScope.GLOBAL].update(import_data['global'])
                else:
                    self.config_layers[ConfigScope.GLOBAL] = import_data['global']
            
            if 'user' in import_data:
                if merge:
                    self.config_layers[ConfigScope.USER].update(import_data['user'])
                else:
                    self.config_layers[ConfigScope.USER] = import_data['user']
            
            # Import profiles
            if 'profiles' in import_data:
                for profile_data in import_data['profiles']:
                    profile = ConfigurationProfile.from_dict(profile_data)
                    self.profiles[profile.profile_id] = profile
            
            if 'active_profile_id' in import_data:
                self.active_profile_id = import_data['active_profile_id']
            
            # Persist changes
            self._persist_scope(ConfigScope.GLOBAL)
            self._persist_scope(ConfigScope.USER)
            self._save_profiles()
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info(f"Successfully imported configuration from {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
    
    def reset_to_defaults(self, scope: ConfigScope = ConfigScope.USER) -> None:
        """Reset configuration scope to defaults"""
        self.config_layers[scope].clear()
        self._persist_scope(scope)
        self._invalidate_cache()
        logger.info(f"Reset {scope.value} configuration to defaults")
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all configuration settings merged across scopes"""
        merged_config = {}
        
        # Merge in reverse priority order
        for scope in reversed(list(ConfigScope)):
            self._deep_merge(merged_config, self.config_layers[scope])
        
        # Merge active profile settings
        if self.active_profile_id and self.active_profile_id in self.profiles:
            profile = self.profiles[self.active_profile_id]
            self._deep_merge(merged_config, profile.settings)
        
        return merged_config
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source dictionary into target"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = copy.deepcopy(value)
    
    def validate_all(self) -> Dict[str, List[str]]:
        """Validate all configuration scopes against all schemas"""
        validation_results = {}
        
        for scope in ConfigScope:
            scope_errors = []
            for schema_name in self.validator.schemas:
                errors = self.validator.validate(self.config_layers[scope], schema_name)
                scope_errors.extend(errors)
            validation_results[scope.value] = scope_errors
        
        return validation_results
    
    def get_configuration_info(self) -> Dict[str, Any]:
        """Get comprehensive configuration system information"""
        return {
            'base_path': str(self.base_path),
            'scopes': {scope.value: len(config) for scope, config in self.config_layers.items()},
            'profiles': {
                'total': len(self.profiles),
                'active': self.active_profile_id,
                'list': [{'id': p.profile_id, 'name': p.name} for p in self.profiles.values()]
            },
            'schemas': list(self.validator.schemas.keys()),
            'providers': list(self.providers.keys()),
            'cache_valid': self._is_cache_valid(),
            'listeners': len(self.change_listeners)
        }


class ConfigurationMigrator:
    """Configuration migration system for version updates"""

    def __init__(self, config_manager: AdvancedConfigurationManager):
        self.config_manager = config_manager
        self.migrations: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self._register_default_migrations()

    def _register_default_migrations(self):
        """Register default configuration migrations"""
        self.register_migration("1.0.0", "1.1.0", self._migrate_1_0_to_1_1)
        self.register_migration("1.1.0", "1.2.0", self._migrate_1_1_to_1_2)

    def register_migration(self, from_version: str, to_version: str,
                          migration_func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """Register a configuration migration"""
        migration_key = f"{from_version}->{to_version}"
        self.migrations[migration_key] = migration_func
        logger.info(f"Registered migration: {migration_key}")

    def migrate_configuration(self, config: Dict[str, Any],
                            from_version: str, to_version: str) -> Dict[str, Any]:
        """Migrate configuration from one version to another"""
        current_version = from_version
        migrated_config = copy.deepcopy(config)

        # Apply migrations in sequence
        while current_version != to_version:
            next_version = self._get_next_version(current_version, to_version)
            if not next_version:
                raise ValueError(f"No migration path from {current_version} to {to_version}")

            migration_key = f"{current_version}->{next_version}"
            if migration_key not in self.migrations:
                raise ValueError(f"Migration not found: {migration_key}")

            logger.info(f"Applying migration: {migration_key}")
            migrated_config = self.migrations[migration_key](migrated_config)
            current_version = next_version

        return migrated_config

    def _get_next_version(self, current: str, target: str) -> Optional[str]:
        """Get the next version in the migration path"""
        # Simple version progression logic
        version_map = {
            "1.0.0": "1.1.0",
            "1.1.0": "1.2.0"
        }
        return version_map.get(current)

    def _migrate_1_0_to_1_1(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 1.0.0 to 1.1.0"""
        migrated = copy.deepcopy(config)

        # Add new feature discovery settings
        if "onboarding" in migrated:
            if "feature_discovery" not in migrated["onboarding"]:
                migrated["onboarding"]["feature_discovery"] = {
                    "auto_highlight": True,
                    "discovery_pace": "normal",
                    "show_advanced_features": False,
                    "feature_categories_enabled": ["basic", "intermediate"]
                }

        # Update version
        if "system" in migrated:
            migrated["system"]["version"] = "1.1.0"

        return migrated

    def _migrate_1_1_to_1_2(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 1.1.0 to 1.2.0"""
        migrated = copy.deepcopy(config)

        # Add accessibility settings
        if "accessibility" not in migrated:
            migrated["accessibility"] = {
                "high_contrast": False,
                "large_fonts": False,
                "screen_reader_support": False,
                "keyboard_navigation": True,
                "reduced_motion": False
            }

        # Update version
        if "system" in migrated:
            migrated["system"]["version"] = "1.2.0"

        return migrated


class ConfigurationBackup:
    """Configuration backup and restore system"""

    def __init__(self, config_manager: AdvancedConfigurationManager):
        self.config_manager = config_manager
        self.backup_path = config_manager.base_path / "backups"
        self.backup_path.mkdir(exist_ok=True)

    def create_backup(self, name: Optional[str] = None) -> str:
        """Create a configuration backup"""
        if not name:
            name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_file = self.backup_path / f"{name}.json"

        backup_data = {
            "backup_name": name,
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "global_config": self.config_manager.config_layers[ConfigScope.GLOBAL],
            "user_config": self.config_manager.config_layers[ConfigScope.USER],
            "profiles": [profile.to_dict() for profile in self.config_manager.profiles.values()],
            "active_profile_id": self.config_manager.active_profile_id
        }

        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Created configuration backup: {backup_file}")
            return str(backup_file)

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def restore_backup(self, backup_file: str) -> bool:
        """Restore configuration from backup"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # Restore configuration layers
            if "global_config" in backup_data:
                self.config_manager.config_layers[ConfigScope.GLOBAL] = backup_data["global_config"]
                self.config_manager._persist_scope(ConfigScope.GLOBAL)

            if "user_config" in backup_data:
                self.config_manager.config_layers[ConfigScope.USER] = backup_data["user_config"]
                self.config_manager._persist_scope(ConfigScope.USER)

            # Restore profiles
            if "profiles" in backup_data:
                self.config_manager.profiles.clear()
                for profile_data in backup_data["profiles"]:
                    profile = ConfigurationProfile.from_dict(profile_data)
                    self.config_manager.profiles[profile.profile_id] = profile

                self.config_manager.active_profile_id = backup_data.get("active_profile_id")
                self.config_manager._save_profiles()

            # Invalidate cache
            self.config_manager._invalidate_cache()

            logger.info(f"Restored configuration from backup: {backup_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []

        for backup_file in self.backup_path.glob("*.json"):
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)

                backups.append({
                    "file": str(backup_file),
                    "name": backup_data.get("backup_name", backup_file.stem),
                    "created_at": backup_data.get("created_at"),
                    "version": backup_data.get("version"),
                    "size": backup_file.stat().st_size
                })

            except Exception as e:
                logger.warning(f"Failed to read backup {backup_file}: {e}")

        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    def delete_backup(self, backup_file: str) -> bool:
        """Delete a backup file"""
        try:
            Path(backup_file).unlink()
            logger.info(f"Deleted backup: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False
