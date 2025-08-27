"""
Configuration Plugin System for HEAL Onboarding

Provides extensible configuration system with plugin support,
custom validators, dynamic configuration sources, and runtime extensions.
"""

from typing import Dict, Any, List, Optional, Callable, Type, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import importlib
import inspect
from pathlib import Path

from .config_system import AdvancedConfigurationManager, ConfigProvider, ConfigValidationRule
from src.heal.common.logging_config import get_logger

logger = get_logger(__name__)


class PluginType(Enum):
    """Configuration plugin types"""
    PROVIDER = "provider"           # Custom configuration providers
    VALIDATOR = "validator"         # Custom validation rules
    TRANSFORMER = "transformer"    # Configuration transformers
    LISTENER = "listener"          # Configuration change listeners
    UI_COMPONENT = "ui_component"  # Custom UI components
    PRESET = "preset"              # Configuration presets


@dataclass
class PluginMetadata:
    """Plugin metadata information"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str]
    config_schema: Optional[Dict[str, Any]] = None
    ui_components: List[str] = None


class ConfigurationPlugin(ABC):
    """Base class for configuration plugins"""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata"""
        pass
    
    @abstractmethod
    def initialize(self, config_manager: AdvancedConfigurationManager) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the plugin"""
        pass
    
    def get_configuration_schema(self) -> Optional[Dict[str, Any]]:
        """Get plugin-specific configuration schema"""
        return None
    
    def get_default_configuration(self) -> Optional[Dict[str, Any]]:
        """Get plugin default configuration"""
        return None


class ConfigProviderPlugin(ConfigurationPlugin):
    """Base class for configuration provider plugins"""
    
    @abstractmethod
    def create_provider(self) -> ConfigProvider:
        """Create a configuration provider instance"""
        pass


class ConfigValidatorPlugin(ConfigurationPlugin):
    """Base class for configuration validator plugins"""
    
    @abstractmethod
    def get_validation_rules(self) -> List[ConfigValidationRule]:
        """Get validation rules provided by this plugin"""
        pass


class ConfigTransformerPlugin(ConfigurationPlugin):
    """Base class for configuration transformer plugins"""
    
    @abstractmethod
    def transform_config(self, config: Dict[str, Any], 
                        context: Dict[str, Any]) -> Dict[str, Any]:
        """Transform configuration data"""
        pass


class ConfigListenerPlugin(ConfigurationPlugin):
    """Base class for configuration listener plugins"""
    
    @abstractmethod
    def on_config_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """Handle configuration changes"""
        pass


class DatabaseConfigProvider(ConfigProvider):
    """Database-based configuration provider"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    def load(self, path: str) -> Dict[str, Any]:
        """Load configuration from database"""
        # Implementation would connect to database and load config
        logger.info(f"Loading config from database: {path}")
        return {}
    
    def save(self, config: Dict[str, Any], path: str) -> bool:
        """Save configuration to database"""
        # Implementation would save config to database
        logger.info(f"Saving config to database: {path}")
        return True
    
    def exists(self, path: str) -> bool:
        """Check if configuration exists in database"""
        return True


class RemoteConfigProvider(ConfigProvider):
    """Remote configuration provider (HTTP/REST API)"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
    
    def load(self, path: str) -> Dict[str, Any]:
        """Load configuration from remote server"""
        # Implementation would make HTTP request to load config
        logger.info(f"Loading config from remote: {self.base_url}/{path}")
        return {}
    
    def save(self, config: Dict[str, Any], path: str) -> bool:
        """Save configuration to remote server"""
        # Implementation would make HTTP request to save config
        logger.info(f"Saving config to remote: {self.base_url}/{path}")
        return True
    
    def exists(self, path: str) -> bool:
        """Check if configuration exists on remote server"""
        return True


class DatabaseProviderPlugin(ConfigProviderPlugin):
    """Database configuration provider plugin"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Database Provider",
            version="1.0.0",
            description="Store configuration in database",
            author="HEAL Team",
            plugin_type=PluginType.PROVIDER,
            dependencies=[]
        )
    
    def initialize(self, config_manager: AdvancedConfigurationManager) -> bool:
        """Initialize database provider plugin"""
        try:
            # Register database provider
            from .config_system import ConfigFormat
            provider = DatabaseConfigProvider("sqlite:///config.db")
            # Would register with config manager if it supported custom providers
            logger.info("Database provider plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database provider: {e}")
            return False
    
    def shutdown(self) -> None:
        """Shutdown database provider plugin"""
        logger.info("Database provider plugin shutdown")
    
    def create_provider(self) -> ConfigProvider:
        """Create database provider instance"""
        return DatabaseConfigProvider("sqlite:///config.db")


class SecurityValidatorPlugin(ConfigValidatorPlugin):
    """Security-focused configuration validator plugin"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Security Validator",
            version="1.0.0",
            description="Security-focused configuration validation",
            author="HEAL Team",
            plugin_type=PluginType.VALIDATOR,
            dependencies=[]
        )
    
    def initialize(self, config_manager: AdvancedConfigurationManager) -> bool:
        """Initialize security validator plugin"""
        try:
            # Register validation rules
            rules = self.get_validation_rules()
            for rule in rules:
                # Would register with config manager's validator
                pass
            logger.info("Security validator plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize security validator: {e}")
            return False
    
    def shutdown(self) -> None:
        """Shutdown security validator plugin"""
        logger.info("Security validator plugin shutdown")
    
    def get_validation_rules(self) -> List[ConfigValidationRule]:
        """Get security validation rules"""
        return [
            ConfigValidationRule(
                field_path="security.auto_lock_timeout",
                validator=lambda x: isinstance(x, int) and 1 <= x <= 3600,
                error_message="Auto lock timeout must be between 1 and 3600 seconds"
            ),
            ConfigValidationRule(
                field_path="security.password_min_length",
                validator=lambda x: isinstance(x, int) and x >= 8,
                error_message="Password minimum length must be at least 8 characters"
            ),
            ConfigValidationRule(
                field_path="network.allowed_hosts",
                validator=self._validate_hosts,
                error_message="Invalid host format in allowed hosts list"
            )
        ]
    
    def _validate_hosts(self, hosts: Any) -> bool:
        """Validate host list format"""
        if not isinstance(hosts, list):
            return False
        
        for host in hosts:
            if not isinstance(host, str) or not host.strip():
                return False
        
        return True


class EnvironmentTransformerPlugin(ConfigTransformerPlugin):
    """Environment variable configuration transformer plugin"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Environment Transformer",
            version="1.0.0",
            description="Transform configuration using environment variables",
            author="HEAL Team",
            plugin_type=PluginType.TRANSFORMER,
            dependencies=[]
        )
    
    def initialize(self, config_manager: AdvancedConfigurationManager) -> bool:
        """Initialize environment transformer plugin"""
        logger.info("Environment transformer plugin initialized")
        return True
    
    def shutdown(self) -> None:
        """Shutdown environment transformer plugin"""
        logger.info("Environment transformer plugin shutdown")
    
    def transform_config(self, config: Dict[str, Any], 
                        context: Dict[str, Any]) -> Dict[str, Any]:
        """Transform configuration using environment variables"""
        import os
        transformed = config.copy()
        
        # Replace ${ENV_VAR} patterns with environment variable values
        def replace_env_vars(obj):
            if isinstance(obj, str):
                if obj.startswith("${") and obj.endswith("}"):
                    env_var = obj[2:-1]
                    return os.environ.get(env_var, obj)
                return obj
            elif isinstance(obj, dict):
                return {k: replace_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_env_vars(item) for item in obj]
            return obj
        
        return replace_env_vars(transformed)


class AuditListenerPlugin(ConfigListenerPlugin):
    """Configuration change audit listener plugin"""
    
    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Audit Listener",
            version="1.0.0",
            description="Audit configuration changes",
            author="HEAL Team",
            plugin_type=PluginType.LISTENER,
            dependencies=[]
        )
    
    def initialize(self, config_manager: AdvancedConfigurationManager) -> bool:
        """Initialize audit listener plugin"""
        config_manager.add_change_listener(self.on_config_changed)
        logger.info("Audit listener plugin initialized")
        return True
    
    def shutdown(self) -> None:
        """Shutdown audit listener plugin"""
        logger.info("Audit listener plugin shutdown")
    
    def on_config_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """Handle configuration changes"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "key": key,
            "old_value": old_value,
            "new_value": new_value,
            "user": "current_user"  # Would get actual user
        }
        
        self.audit_log.append(audit_entry)
        logger.info(f"Configuration change audited: {key}")
    
    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get configuration change audit log"""
        return self.audit_log.copy()


class ConfigurationPluginManager:
    """Manager for configuration plugins"""
    
    def __init__(self, config_manager: AdvancedConfigurationManager):
        self.config_manager = config_manager
        self.plugins: Dict[str, ConfigurationPlugin] = {}
        self.plugin_registry: Dict[PluginType, List[str]] = {
            plugin_type: [] for plugin_type in PluginType
        }
    
    def register_plugin(self, plugin: ConfigurationPlugin) -> bool:
        """Register a configuration plugin"""
        try:
            metadata = plugin.metadata
            
            # Check dependencies
            if not self._check_dependencies(metadata.dependencies):
                logger.error(f"Plugin {metadata.name} has unmet dependencies")
                return False
            
            # Initialize plugin
            if not plugin.initialize(self.config_manager):
                logger.error(f"Failed to initialize plugin {metadata.name}")
                return False
            
            # Register plugin
            self.plugins[metadata.name] = plugin
            self.plugin_registry[metadata.plugin_type].append(metadata.name)
            
            logger.info(f"Registered plugin: {metadata.name} v{metadata.version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin: {e}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """Unregister a configuration plugin"""
        if plugin_name not in self.plugins:
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            plugin.shutdown()
            
            # Remove from registry
            plugin_type = plugin.metadata.plugin_type
            if plugin_name in self.plugin_registry[plugin_type]:
                self.plugin_registry[plugin_type].remove(plugin_name)
            
            del self.plugins[plugin_name]
            
            logger.info(f"Unregistered plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister plugin {plugin_name}: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[ConfigurationPlugin]:
        """Get a registered plugin"""
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[ConfigurationPlugin]:
        """Get all plugins of a specific type"""
        plugin_names = self.plugin_registry.get(plugin_type, [])
        return [self.plugins[name] for name in plugin_names if name in self.plugins]
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all registered plugins"""
        return [
            {
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "description": plugin.metadata.description,
                "type": plugin.metadata.plugin_type.value,
                "author": plugin.metadata.author
            }
            for plugin in self.plugins.values()
        ]
    
    def load_plugins_from_directory(self, plugin_dir: Path) -> int:
        """Load plugins from a directory"""
        loaded_count = 0
        
        if not plugin_dir.exists():
            logger.warning(f"Plugin directory does not exist: {plugin_dir}")
            return 0
        
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
            
            try:
                # Import plugin module
                spec = importlib.util.spec_from_file_location(
                    plugin_file.stem, plugin_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find plugin classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, ConfigurationPlugin) and 
                        obj != ConfigurationPlugin):
                        
                        # Create and register plugin instance
                        plugin_instance = obj()
                        if self.register_plugin(plugin_instance):
                            loaded_count += 1
                
            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {e}")
        
        logger.info(f"Loaded {loaded_count} plugins from {plugin_dir}")
        return loaded_count
    
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if plugin dependencies are met"""
        for dependency in dependencies:
            if dependency not in self.plugins:
                return False
        return True
    
    def shutdown_all_plugins(self) -> None:
        """Shutdown all registered plugins"""
        for plugin_name in list(self.plugins.keys()):
            self.unregister_plugin(plugin_name)
        
        logger.info("All plugins shutdown")


# Example usage and built-in plugins
def create_default_plugin_manager(config_manager: AdvancedConfigurationManager) -> ConfigurationPluginManager:
    """Create plugin manager with default plugins"""
    plugin_manager = ConfigurationPluginManager(config_manager)
    
    # Register built-in plugins
    plugin_manager.register_plugin(SecurityValidatorPlugin())
    plugin_manager.register_plugin(EnvironmentTransformerPlugin())
    plugin_manager.register_plugin(AuditListenerPlugin())
    
    return plugin_manager
