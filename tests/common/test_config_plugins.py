"""
Tests for configuration plugin system

Tests the plugin architecture including:
- Plugin registration and management
- Plugin types and functionality
- Plugin dependencies
- Built-in plugins
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Mock plugin system components
class MockPluginType:
    PROVIDER = "provider"
    VALIDATOR = "validator"
    TRANSFORMER = "transformer"
    LISTENER = "listener"
    UI_COMPONENT = "ui_component"
    PRESET = "preset"

class MockPluginMetadata:
    def __init__(self, name, version, description, author, plugin_type, dependencies=None):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.plugin_type = plugin_type
        self.dependencies = dependencies or []

class MockConfigurationPlugin:
    def __init__(self, metadata):
        self._metadata = metadata
        self.initialized = False
        self.shutdown_called = False
    
    @property
    def metadata(self):
        return self._metadata
    
    def initialize(self, config_manager):
        self.initialized = True
        return True
    
    def shutdown(self):
        self.shutdown_called = True
    
    def get_configuration_schema(self):
        return None
    
    def get_default_configuration(self):
        return None

class MockConfigValidationRule:
    def __init__(self, field_path, validator, error_message):
        self.field_path = field_path
        self.validator = validator
        self.error_message = error_message

class MockConfigProvider:
    def load(self, path):
        return {}
    
    def save(self, config, path):
        return True
    
    def exists(self, path):
        return True

class MockConfigProviderPlugin(MockConfigurationPlugin):
    def __init__(self):
        metadata = MockPluginMetadata(
            name="Test Provider",
            version="1.0.0",
            description="Test provider plugin",
            author="Test Author",
            plugin_type=MockPluginType.PROVIDER
        )
        super().__init__(metadata)
    
    def create_provider(self):
        return MockConfigProvider()

class MockConfigValidatorPlugin(MockConfigurationPlugin):
    def __init__(self):
        metadata = MockPluginMetadata(
            name="Test Validator",
            version="1.0.0",
            description="Test validator plugin",
            author="Test Author",
            plugin_type=MockPluginType.VALIDATOR
        )
        super().__init__(metadata)
    
    def get_validation_rules(self):
        return [
            MockConfigValidationRule(
                field_path="test.field",
                validator=lambda x: isinstance(x, str),
                error_message="Field must be a string"
            )
        ]

class MockConfigTransformerPlugin(MockConfigurationPlugin):
    def __init__(self):
        metadata = MockPluginMetadata(
            name="Test Transformer",
            version="1.0.0",
            description="Test transformer plugin",
            author="Test Author",
            plugin_type=MockPluginType.TRANSFORMER
        )
        super().__init__(metadata)
    
    def transform_config(self, config, context):
        # Simple transformation: add a test field
        transformed = config.copy()
        transformed["transformed"] = True
        return transformed

class MockConfigListenerPlugin(MockConfigurationPlugin):
    def __init__(self):
        metadata = MockPluginMetadata(
            name="Test Listener",
            version="1.0.0",
            description="Test listener plugin",
            author="Test Author",
            plugin_type=MockPluginType.LISTENER
        )
        super().__init__(metadata)
        self.change_events = []
    
    def on_config_changed(self, key, old_value, new_value):
        self.change_events.append((key, old_value, new_value))

class MockSecurityValidatorPlugin(MockConfigurationPlugin):
    def __init__(self):
        metadata = MockPluginMetadata(
            name="Security Validator",
            version="1.0.0",
            description="Security validation plugin",
            author="HEAL Team",
            plugin_type=MockPluginType.VALIDATOR
        )
        super().__init__(metadata)
    
    def get_validation_rules(self):
        return [
            MockConfigValidationRule(
                field_path="security.auto_lock_timeout",
                validator=lambda x: isinstance(x, int) and 1 <= x <= 3600,
                error_message="Auto lock timeout must be between 1 and 3600 seconds"
            ),
            MockConfigValidationRule(
                field_path="security.password_min_length",
                validator=lambda x: isinstance(x, int) and x >= 8,
                error_message="Password minimum length must be at least 8 characters"
            )
        ]

class MockEnvironmentTransformerPlugin(MockConfigurationPlugin):
    def __init__(self):
        metadata = MockPluginMetadata(
            name="Environment Transformer",
            version="1.0.0",
            description="Environment variable transformer",
            author="HEAL Team",
            plugin_type=MockPluginType.TRANSFORMER
        )
        super().__init__(metadata)
    
    def transform_config(self, config, context):
        # Mock environment variable substitution
        transformed = config.copy()
        
        def replace_env_vars(obj):
            if isinstance(obj, str):
                if obj.startswith("${") and obj.endswith("}"):
                    env_var = obj[2:-1]
                    # Mock environment variable lookup
                    return f"mock_env_value_{env_var}"
                return obj
            elif isinstance(obj, dict):
                return {k: replace_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_env_vars(item) for item in obj]
            return obj
        
        return replace_env_vars(transformed)

class MockAuditListenerPlugin(MockConfigurationPlugin):
    def __init__(self):
        metadata = MockPluginMetadata(
            name="Audit Listener",
            version="1.0.0",
            description="Configuration audit plugin",
            author="HEAL Team",
            plugin_type=MockPluginType.LISTENER
        )
        super().__init__(metadata)
        self.audit_log = []
    
    def on_config_changed(self, key, old_value, new_value):
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "key": key,
            "old_value": old_value,
            "new_value": new_value,
            "user": "test_user"
        }
        self.audit_log.append(audit_entry)
    
    def get_audit_log(self):
        return self.audit_log.copy()

class MockConfigurationPluginManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.plugins = {}
        self.plugin_registry = {
            plugin_type: [] for plugin_type in [
                MockPluginType.PROVIDER,
                MockPluginType.VALIDATOR,
                MockPluginType.TRANSFORMER,
                MockPluginType.LISTENER,
                MockPluginType.UI_COMPONENT,
                MockPluginType.PRESET
            ]
        }
    
    def register_plugin(self, plugin):
        try:
            metadata = plugin.metadata
            
            # Check dependencies
            if not self._check_dependencies(metadata.dependencies):
                return False
            
            # Initialize plugin
            if not plugin.initialize(self.config_manager):
                return False
            
            # Register plugin
            self.plugins[metadata.name] = plugin
            self.plugin_registry[metadata.plugin_type].append(metadata.name)
            
            return True
        except Exception:
            return False
    
    def unregister_plugin(self, plugin_name):
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
            return True
        except Exception:
            return False
    
    def get_plugin(self, plugin_name):
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type):
        plugin_names = self.plugin_registry.get(plugin_type, [])
        return [self.plugins[name] for name in plugin_names if name in self.plugins]
    
    def list_plugins(self):
        return [
            {
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "description": plugin.metadata.description,
                "type": plugin.metadata.plugin_type,
                "author": plugin.metadata.author
            }
            for plugin in self.plugins.values()
        ]
    
    def _check_dependencies(self, dependencies):
        for dependency in dependencies:
            if dependency not in self.plugins:
                return False
        return True
    
    def shutdown_all_plugins(self):
        for plugin_name in list(self.plugins.keys()):
            self.unregister_plugin(plugin_name)


class TestConfigurationPlugins:
    """Test suite for configuration plugin system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config_manager = Mock()
        self.plugin_manager = MockConfigurationPluginManager(self.config_manager)
    
    def test_plugin_registration(self):
        """Test plugin registration"""
        plugin = MockConfigProviderPlugin()
        
        # Register plugin
        assert self.plugin_manager.register_plugin(plugin)
        
        # Verify plugin is registered
        assert plugin.metadata.name in self.plugin_manager.plugins
        assert plugin.initialized
        
        # Verify plugin is in registry
        provider_plugins = self.plugin_manager.get_plugins_by_type(MockPluginType.PROVIDER)
        assert len(provider_plugins) == 1
        assert provider_plugins[0] == plugin
    
    def test_plugin_unregistration(self):
        """Test plugin unregistration"""
        plugin = MockConfigProviderPlugin()
        
        # Register and then unregister
        self.plugin_manager.register_plugin(plugin)
        assert self.plugin_manager.unregister_plugin(plugin.metadata.name)
        
        # Verify plugin is removed
        assert plugin.metadata.name not in self.plugin_manager.plugins
        assert plugin.shutdown_called
        
        # Verify plugin is removed from registry
        provider_plugins = self.plugin_manager.get_plugins_by_type(MockPluginType.PROVIDER)
        assert len(provider_plugins) == 0
    
    def test_multiple_plugin_types(self):
        """Test registration of multiple plugin types"""
        plugins = [
            MockConfigProviderPlugin(),
            MockConfigValidatorPlugin(),
            MockConfigTransformerPlugin(),
            MockConfigListenerPlugin()
        ]
        
        # Register all plugins
        for plugin in plugins:
            assert self.plugin_manager.register_plugin(plugin)
        
        # Verify all plugins are registered
        assert len(self.plugin_manager.plugins) == 4
        
        # Verify plugins are in correct registries
        assert len(self.plugin_manager.get_plugins_by_type(MockPluginType.PROVIDER)) == 1
        assert len(self.plugin_manager.get_plugins_by_type(MockPluginType.VALIDATOR)) == 1
        assert len(self.plugin_manager.get_plugins_by_type(MockPluginType.TRANSFORMER)) == 1
        assert len(self.plugin_manager.get_plugins_by_type(MockPluginType.LISTENER)) == 1
    
    def test_plugin_dependencies(self):
        """Test plugin dependency checking"""
        # Create plugin with dependency
        dependent_plugin = MockConfigurationPlugin(
            MockPluginMetadata(
                name="Dependent Plugin",
                version="1.0.0",
                description="Plugin with dependency",
                author="Test",
                plugin_type=MockPluginType.VALIDATOR,
                dependencies=["Base Plugin"]
            )
        )
        
        # Try to register without dependency - should fail
        assert not self.plugin_manager.register_plugin(dependent_plugin)
        
        # Register base plugin first
        base_plugin = MockConfigurationPlugin(
            MockPluginMetadata(
                name="Base Plugin",
                version="1.0.0",
                description="Base plugin",
                author="Test",
                plugin_type=MockPluginType.PROVIDER
            )
        )
        assert self.plugin_manager.register_plugin(base_plugin)
        
        # Now dependent plugin should register successfully
        assert self.plugin_manager.register_plugin(dependent_plugin)
    
    def test_plugin_listing(self):
        """Test plugin listing functionality"""
        plugins = [
            MockConfigProviderPlugin(),
            MockConfigValidatorPlugin(),
            MockConfigTransformerPlugin()
        ]
        
        # Register plugins
        for plugin in plugins:
            self.plugin_manager.register_plugin(plugin)
        
        # Get plugin list
        plugin_list = self.plugin_manager.list_plugins()
        
        # Verify list structure
        assert len(plugin_list) == 3
        
        for plugin_info in plugin_list:
            assert "name" in plugin_info
            assert "version" in plugin_info
            assert "description" in plugin_info
            assert "type" in plugin_info
            assert "author" in plugin_info
    
    def test_plugin_retrieval(self):
        """Test plugin retrieval by name"""
        plugin = MockConfigProviderPlugin()
        self.plugin_manager.register_plugin(plugin)
        
        # Retrieve plugin by name
        retrieved_plugin = self.plugin_manager.get_plugin(plugin.metadata.name)
        assert retrieved_plugin == plugin
        
        # Try to retrieve non-existent plugin
        assert self.plugin_manager.get_plugin("Non-existent Plugin") is None
    
    def test_provider_plugin_functionality(self):
        """Test provider plugin functionality"""
        plugin = MockConfigProviderPlugin()
        self.plugin_manager.register_plugin(plugin)
        
        # Test provider creation
        provider = plugin.create_provider()
        assert provider is not None
        
        # Test provider methods
        assert provider.load("test_path") == {}
        assert provider.save({}, "test_path") is True
        assert provider.exists("test_path") is True
    
    def test_validator_plugin_functionality(self):
        """Test validator plugin functionality"""
        plugin = MockConfigValidatorPlugin()
        self.plugin_manager.register_plugin(plugin)
        
        # Test validation rules
        rules = plugin.get_validation_rules()
        assert len(rules) == 1
        assert rules[0].field_path == "test.field"
        assert rules[0].validator("test_string") is True
        assert rules[0].validator(123) is False
    
    def test_transformer_plugin_functionality(self):
        """Test transformer plugin functionality"""
        plugin = MockConfigTransformerPlugin()
        self.plugin_manager.register_plugin(plugin)
        
        # Test configuration transformation
        original_config = {"test": "value"}
        transformed_config = plugin.transform_config(original_config, {})
        
        assert "transformed" in transformed_config
        assert transformed_config["transformed"] is True
        assert transformed_config["test"] == "value"
    
    def test_listener_plugin_functionality(self):
        """Test listener plugin functionality"""
        plugin = MockConfigListenerPlugin()
        self.plugin_manager.register_plugin(plugin)
        
        # Test change listening
        plugin.on_config_changed("test.key", "old_value", "new_value")
        
        assert len(plugin.change_events) == 1
        assert plugin.change_events[0] == ("test.key", "old_value", "new_value")
    
    def test_security_validator_plugin(self):
        """Test security validator plugin"""
        plugin = MockSecurityValidatorPlugin()
        self.plugin_manager.register_plugin(plugin)
        
        # Test security validation rules
        rules = plugin.get_validation_rules()
        assert len(rules) == 2
        
        # Test timeout validation
        timeout_rule = next(r for r in rules if "auto_lock_timeout" in r.field_path)
        assert timeout_rule.validator(300) is True  # Valid timeout
        assert timeout_rule.validator(5000) is False  # Too high
        assert timeout_rule.validator(0) is False  # Too low
        
        # Test password length validation
        password_rule = next(r for r in rules if "password_min_length" in r.field_path)
        assert password_rule.validator(8) is True  # Valid length
        assert password_rule.validator(12) is True  # Valid length
        assert password_rule.validator(4) is False  # Too short
    
    def test_environment_transformer_plugin(self):
        """Test environment transformer plugin"""
        plugin = MockEnvironmentTransformerPlugin()
        self.plugin_manager.register_plugin(plugin)
        
        # Test environment variable transformation
        config_with_env_vars = {
            "database_url": "${DATABASE_URL}",
            "api_key": "${API_KEY}",
            "static_value": "no_change"
        }
        
        transformed = plugin.transform_config(config_with_env_vars, {})
        
        assert transformed["database_url"] == "mock_env_value_DATABASE_URL"
        assert transformed["api_key"] == "mock_env_value_API_KEY"
        assert transformed["static_value"] == "no_change"
    
    def test_audit_listener_plugin(self):
        """Test audit listener plugin"""
        plugin = MockAuditListenerPlugin()
        self.plugin_manager.register_plugin(plugin)
        
        # Test audit logging
        plugin.on_config_changed("ui.theme", "light", "dark")
        plugin.on_config_changed("user.level", "beginner", "intermediate")
        
        audit_log = plugin.get_audit_log()
        assert len(audit_log) == 2
        
        # Verify first entry
        first_entry = audit_log[0]
        assert first_entry["key"] == "ui.theme"
        assert first_entry["old_value"] == "light"
        assert first_entry["new_value"] == "dark"
        assert first_entry["user"] == "test_user"
        assert "timestamp" in first_entry
        
        # Verify second entry
        second_entry = audit_log[1]
        assert second_entry["key"] == "user.level"
        assert second_entry["old_value"] == "beginner"
        assert second_entry["new_value"] == "intermediate"
    
    def test_plugin_shutdown(self):
        """Test plugin shutdown functionality"""
        plugins = [
            MockConfigProviderPlugin(),
            MockConfigValidatorPlugin(),
            MockConfigTransformerPlugin()
        ]
        
        # Register all plugins
        for plugin in plugins:
            self.plugin_manager.register_plugin(plugin)
        
        # Shutdown all plugins
        self.plugin_manager.shutdown_all_plugins()
        
        # Verify all plugins are shutdown
        assert len(self.plugin_manager.plugins) == 0
        for plugin in plugins:
            assert plugin.shutdown_called
    
    def test_plugin_error_handling(self):
        """Test plugin error handling"""
        # Create plugin that fails initialization
        failing_plugin = MockConfigurationPlugin(
            MockPluginMetadata(
                name="Failing Plugin",
                version="1.0.0",
                description="Plugin that fails",
                author="Test",
                plugin_type=MockPluginType.VALIDATOR
            )
        )
        
        # Override initialize to fail
        failing_plugin.initialize = lambda config_manager: False
        
        # Registration should fail
        assert not self.plugin_manager.register_plugin(failing_plugin)
        assert failing_plugin.metadata.name not in self.plugin_manager.plugins
    
    def test_plugin_metadata_validation(self):
        """Test plugin metadata validation"""
        plugin = MockConfigProviderPlugin()
        metadata = plugin.metadata
        
        # Verify metadata structure
        assert hasattr(metadata, 'name')
        assert hasattr(metadata, 'version')
        assert hasattr(metadata, 'description')
        assert hasattr(metadata, 'author')
        assert hasattr(metadata, 'plugin_type')
        assert hasattr(metadata, 'dependencies')
        
        # Verify metadata values
        assert metadata.name == "Test Provider"
        assert metadata.version == "1.0.0"
        assert metadata.plugin_type == MockPluginType.PROVIDER
        assert isinstance(metadata.dependencies, list)


if __name__ == "__main__":
    # Run tests
    test_suite = TestConfigurationPlugins()
    
    # Run all test methods
    test_methods = [method for method in dir(test_suite) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            print(f"Running {test_method}...")
            test_suite.setup_method()
            getattr(test_suite, test_method)()
            print(f"✅ {test_method} PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_method} FAILED: {e}")
            failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All configuration plugin tests passed!")
    else:
        print(f"⚠️ {failed} tests failed")
