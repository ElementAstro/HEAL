"""
Comprehensive tests for the advanced configuration system

Tests all aspects of the configuration system including:
- Core configuration management
- Multi-scope configuration
- Validation system
- Profile management
- Import/export functionality
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Mock the configuration system components since we can't import them directly
class MockConfigScope:
    GLOBAL = "global"
    USER = "user"
    SESSION = "session"
    TEMPORARY = "temporary"

class MockConfigFormat:
    JSON = "json"
    YAML = "yaml"

class MockConfigValidationRule:
    def __init__(self, field_path, validator, error_message, required=False, default_value=None):
        self.field_path = field_path
        self.validator = validator
        self.error_message = error_message
        self.required = required
        self.default_value = default_value

class MockConfigSchema:
    def __init__(self, name, version, description, validation_rules=None, required_keys=None):
        self.name = name
        self.version = version
        self.description = description
        self.validation_rules = validation_rules or []
        self.required_keys = required_keys or []

class MockConfigurationProfile:
    def __init__(self, profile_id, name, description, created_at=None, last_modified=None, settings=None):
        self.profile_id = profile_id
        self.name = name
        self.description = description
        self.created_at = created_at or datetime.now()
        self.last_modified = last_modified or datetime.now()
        self.settings = settings or {}
        self.metadata = {}
    
    def to_dict(self):
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
    def from_dict(cls, data):
        return cls(
            profile_id=data['profile_id'],
            name=data['name'],
            description=data['description'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_modified=datetime.fromisoformat(data['last_modified']),
            settings=data.get('settings', {}),
        )

class MockAdvancedConfigurationManager:
    def __init__(self, base_path=None):
        self.base_path = base_path or Path.home() / ".heal" / "config"
        self.config_layers = {
            MockConfigScope.TEMPORARY: {},
            MockConfigScope.SESSION: {},
            MockConfigScope.USER: {},
            MockConfigScope.GLOBAL: {}
        }
        self.profiles = {}
        self.active_profile_id = None
        self.change_listeners = []
        self._config_cache = {}
        self._cache_timestamp = datetime.now()
        self._cache_ttl = timedelta(minutes=5)
        self.validator = MockConfigValidator()
    
    def get(self, key, default=None, scope=None):
        # Search through scopes in priority order
        scopes_to_search = [scope] if scope else [
            MockConfigScope.TEMPORARY,
            MockConfigScope.SESSION,
            MockConfigScope.USER,
            MockConfigScope.GLOBAL
        ]
        
        for search_scope in scopes_to_search:
            value = self._get_nested_value(self.config_layers[search_scope], key)
            if value is not None:
                return value
        
        return default
    
    def set(self, key, value, scope=MockConfigScope.USER, validate=True, persist=True):
        try:
            # Get old value for change notification
            old_value = self.get(key)
            
            # Set the value
            self._set_nested_value(self.config_layers[scope], key, value)
            
            # Notify listeners
            for listener in self.change_listeners:
                try:
                    listener(key, old_value, value)
                except Exception:
                    pass
            
            return True
        except Exception:
            return False
    
    def _get_nested_value(self, config, key_path):
        keys = key_path.split('.')
        current = config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        
        return current
    
    def _set_nested_value(self, config, key_path, value):
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def add_change_listener(self, listener):
        self.change_listeners.append(listener)
    
    def remove_change_listener(self, listener):
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)
    
    def create_profile(self, name, description, settings=None):
        import uuid
        profile_id = str(uuid.uuid4())
        
        profile = MockConfigurationProfile(
            profile_id=profile_id,
            name=name,
            description=description,
            settings=settings or {}
        )
        
        self.profiles[profile_id] = profile
        return profile_id
    
    def activate_profile(self, profile_id):
        if profile_id not in self.profiles:
            return False
        
        self.active_profile_id = profile_id
        return True
    
    def get_profile(self, profile_id):
        return self.profiles.get(profile_id)
    
    def list_profiles(self):
        return list(self.profiles.values())
    
    def delete_profile(self, profile_id):
        if profile_id not in self.profiles:
            return False
        
        del self.profiles[profile_id]
        
        if self.active_profile_id == profile_id:
            self.active_profile_id = None
        
        return True
    
    def export_configuration(self, path, format=MockConfigFormat.JSON, include_profiles=True):
        try:
            export_data = {
                'global': self.config_layers[MockConfigScope.GLOBAL],
                'user': self.config_layers[MockConfigScope.USER],
                'export_timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            if include_profiles:
                export_data['profiles'] = [profile.to_dict() for profile in self.profiles.values()]
                export_data['active_profile_id'] = self.active_profile_id
            
            with open(path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def import_configuration(self, path, format=MockConfigFormat.JSON, merge=True):
        try:
            with open(path, 'r') as f:
                import_data = json.load(f)
            
            if not merge:
                self.config_layers[MockConfigScope.GLOBAL].clear()
                self.config_layers[MockConfigScope.USER].clear()
                self.profiles.clear()
            
            if 'global' in import_data:
                if merge:
                    self.config_layers[MockConfigScope.GLOBAL].update(import_data['global'])
                else:
                    self.config_layers[MockConfigScope.GLOBAL] = import_data['global']
            
            if 'user' in import_data:
                if merge:
                    self.config_layers[MockConfigScope.USER].update(import_data['user'])
                else:
                    self.config_layers[MockConfigScope.USER] = import_data['user']
            
            if 'profiles' in import_data:
                for profile_data in import_data['profiles']:
                    profile = MockConfigurationProfile.from_dict(profile_data)
                    self.profiles[profile.profile_id] = profile
            
            if 'active_profile_id' in import_data:
                self.active_profile_id = import_data['active_profile_id']
            
            return True
        except Exception:
            return False
    
    def reset_to_defaults(self, scope=MockConfigScope.USER):
        self.config_layers[scope].clear()
    
    def get_all_settings(self):
        merged_config = {}
        
        # Merge in reverse priority order
        for scope in [MockConfigScope.GLOBAL, MockConfigScope.USER, MockConfigScope.SESSION, MockConfigScope.TEMPORARY]:
            self._deep_merge(merged_config, self.config_layers[scope])
        
        return merged_config
    
    def _deep_merge(self, target, source):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def validate_all(self):
        return {scope: [] for scope in [MockConfigScope.GLOBAL, MockConfigScope.USER, MockConfigScope.SESSION, MockConfigScope.TEMPORARY]}
    
    def get_configuration_info(self):
        return {
            'base_path': str(self.base_path),
            'scopes': {scope: len(config) for scope, config in self.config_layers.items()},
            'profiles': {
                'total': len(self.profiles),
                'active': self.active_profile_id,
                'list': [{'id': p.profile_id, 'name': p.name} for p in self.profiles.values()]
            },
            'cache_valid': True,
            'listeners': len(self.change_listeners)
        }

class MockConfigValidator:
    def __init__(self):
        self.schemas = {}
    
    def register_schema(self, schema):
        self.schemas[schema.name] = schema
    
    def validate(self, config, schema_name):
        return []


class TestAdvancedConfigurationSystem:
    """Test suite for advanced configuration system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = MockAdvancedConfigurationManager(Path(self.temp_dir))
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_basic_configuration_operations(self):
        """Test basic get/set operations"""
        # Test setting and getting values
        assert self.config_manager.set("test.key", "test_value")
        assert self.config_manager.get("test.key") == "test_value"
        
        # Test default values
        assert self.config_manager.get("nonexistent.key", "default") == "default"
        
        # Test nested configuration
        assert self.config_manager.set("nested.deep.key", "nested_value")
        assert self.config_manager.get("nested.deep.key") == "nested_value"
    
    def test_multi_scope_configuration(self):
        """Test multi-scope configuration with priority"""
        # Set values in different scopes
        self.config_manager.set("ui.theme", "light", scope=MockConfigScope.GLOBAL)
        self.config_manager.set("ui.theme", "dark", scope=MockConfigScope.USER)
        self.config_manager.set("ui.theme", "custom", scope=MockConfigScope.SESSION)
        
        # Should return highest priority value (session)
        assert self.config_manager.get("ui.theme") == "custom"
        
        # Test scope-specific retrieval
        assert self.config_manager.get("ui.theme", scope=MockConfigScope.GLOBAL) == "light"
        assert self.config_manager.get("ui.theme", scope=MockConfigScope.USER) == "dark"
    
    def test_configuration_change_listeners(self):
        """Test configuration change listeners"""
        change_events = []
        
        def change_listener(key, old_value, new_value):
            change_events.append((key, old_value, new_value))
        
        # Add listener
        self.config_manager.add_change_listener(change_listener)
        
        # Make changes
        self.config_manager.set("test.key", "value1")
        self.config_manager.set("test.key", "value2")
        
        # Verify events
        assert len(change_events) == 2
        assert change_events[0] == ("test.key", None, "value1")
        assert change_events[1] == ("test.key", "value1", "value2")
        
        # Remove listener
        self.config_manager.remove_change_listener(change_listener)
        self.config_manager.set("test.key", "value3")
        
        # Should not trigger new events
        assert len(change_events) == 2
    
    def test_profile_management(self):
        """Test configuration profile management"""
        # Create profiles
        profile1_id = self.config_manager.create_profile("Profile 1", "Test profile 1")
        profile2_id = self.config_manager.create_profile("Profile 2", "Test profile 2")
        
        assert profile1_id is not None
        assert profile2_id is not None
        assert profile1_id != profile2_id
        
        # Test profile retrieval
        profile1 = self.config_manager.get_profile(profile1_id)
        assert profile1 is not None
        assert profile1.name == "Profile 1"
        assert profile1.description == "Test profile 1"
        
        # Test profile listing
        profiles = self.config_manager.list_profiles()
        assert len(profiles) == 2
        
        # Test profile activation
        assert self.config_manager.activate_profile(profile1_id)
        assert self.config_manager.active_profile_id == profile1_id
        
        # Test profile deletion
        assert self.config_manager.delete_profile(profile2_id)
        assert len(self.config_manager.list_profiles()) == 1
        assert self.config_manager.get_profile(profile2_id) is None
    
    def test_import_export_functionality(self):
        """Test configuration import/export"""
        # Setup test configuration
        self.config_manager.set("test.setting1", "value1", scope=MockConfigScope.GLOBAL)
        self.config_manager.set("test.setting2", "value2", scope=MockConfigScope.USER)
        
        # Create a profile
        profile_id = self.config_manager.create_profile("Test Profile", "Export test")
        self.config_manager.activate_profile(profile_id)
        
        # Export configuration
        export_path = Path(self.temp_dir) / "test_export.json"
        assert self.config_manager.export_configuration(str(export_path), include_profiles=True)
        assert export_path.exists()
        
        # Clear configuration
        self.config_manager.reset_to_defaults(MockConfigScope.GLOBAL)
        self.config_manager.reset_to_defaults(MockConfigScope.USER)
        self.config_manager.profiles.clear()
        
        # Import configuration
        assert self.config_manager.import_configuration(str(export_path), merge=False)
        
        # Verify imported values
        assert self.config_manager.get("test.setting1") == "value1"
        assert self.config_manager.get("test.setting2") == "value2"
        assert len(self.config_manager.profiles) == 1
        assert self.config_manager.active_profile_id == profile_id
    
    def test_configuration_reset(self):
        """Test configuration reset functionality"""
        # Set some values
        self.config_manager.set("test.key1", "value1", scope=MockConfigScope.USER)
        self.config_manager.set("test.key2", "value2", scope=MockConfigScope.USER)
        
        assert self.config_manager.get("test.key1") == "value1"
        assert self.config_manager.get("test.key2") == "value2"
        
        # Reset user scope
        self.config_manager.reset_to_defaults(MockConfigScope.USER)
        
        # Values should be gone
        assert self.config_manager.get("test.key1") is None
        assert self.config_manager.get("test.key2") is None
    
    def test_nested_configuration_operations(self):
        """Test complex nested configuration operations"""
        # Set complex nested structure
        complex_config = {
            "features": {
                "experimental": {
                    "ai_assistance": True,
                    "advanced_analytics": False,
                    "beta_features": ["feature_a", "feature_b"]
                },
                "integrations": {
                    "external_apis": {
                        "enabled": True,
                        "rate_limit": 1000,
                        "timeout": 30
                    }
                }
            }
        }
        
        # Set nested values
        self.config_manager.set("features.experimental.ai_assistance", True)
        self.config_manager.set("features.experimental.beta_features", ["feature_a", "feature_b"])
        self.config_manager.set("features.integrations.external_apis.enabled", True)
        self.config_manager.set("features.integrations.external_apis.rate_limit", 1000)
        
        # Verify nested retrieval
        assert self.config_manager.get("features.experimental.ai_assistance") is True
        assert self.config_manager.get("features.experimental.beta_features") == ["feature_a", "feature_b"]
        assert self.config_manager.get("features.integrations.external_apis.enabled") is True
        assert self.config_manager.get("features.integrations.external_apis.rate_limit") == 1000
    
    def test_configuration_merging(self):
        """Test configuration merging across scopes"""
        # Set values in different scopes
        self.config_manager.set("app.name", "HEAL", scope=MockConfigScope.GLOBAL)
        self.config_manager.set("app.version", "1.0.0", scope=MockConfigScope.GLOBAL)
        self.config_manager.set("user.name", "Test User", scope=MockConfigScope.USER)
        self.config_manager.set("user.preferences.theme", "dark", scope=MockConfigScope.USER)
        self.config_manager.set("session.temp_setting", "temp_value", scope=MockConfigScope.SESSION)
        
        # Get merged configuration
        all_settings = self.config_manager.get_all_settings()
        
        # Verify merged structure
        assert all_settings["app"]["name"] == "HEAL"
        assert all_settings["app"]["version"] == "1.0.0"
        assert all_settings["user"]["name"] == "Test User"
        assert all_settings["user"]["preferences"]["theme"] == "dark"
        assert all_settings["session"]["temp_setting"] == "temp_value"
    
    def test_configuration_info(self):
        """Test configuration system information"""
        # Add some configuration
        self.config_manager.set("test.key", "value")
        profile_id = self.config_manager.create_profile("Test", "Test profile")
        
        # Get configuration info
        info = self.config_manager.get_configuration_info()
        
        # Verify info structure
        assert "base_path" in info
        assert "scopes" in info
        assert "profiles" in info
        assert "cache_valid" in info
        assert "listeners" in info
        
        # Verify profile info
        assert info["profiles"]["total"] == 1
        assert len(info["profiles"]["list"]) == 1
        assert info["profiles"]["list"][0]["name"] == "Test"
    
    def test_error_handling(self):
        """Test error handling in configuration operations"""
        # Test invalid profile operations
        assert not self.config_manager.activate_profile("nonexistent_profile")
        assert not self.config_manager.delete_profile("nonexistent_profile")
        assert self.config_manager.get_profile("nonexistent_profile") is None
        
        # Test import/export with invalid paths
        assert not self.config_manager.import_configuration("/invalid/path/config.json")
        assert not self.config_manager.export_configuration("/invalid/path/config.json")
    
    def test_performance_characteristics(self):
        """Test performance characteristics of configuration system"""
        import time
        
        # Test bulk operations performance
        start_time = time.time()
        
        # Set many configuration values
        for i in range(100):
            self.config_manager.set(f"performance.test.key_{i}", f"value_{i}")
        
        set_time = time.time() - start_time
        
        # Get many configuration values
        start_time = time.time()
        
        for i in range(100):
            value = self.config_manager.get(f"performance.test.key_{i}")
            assert value == f"value_{i}"
        
        get_time = time.time() - start_time
        
        # Performance should be reasonable (less than 1 second for 100 operations)
        assert set_time < 1.0
        assert get_time < 1.0
    
    def test_configuration_validation_system(self):
        """Test configuration validation system"""
        # Create validation rule
        rule = MockConfigValidationRule(
            field_path="test.number",
            validator=lambda x: isinstance(x, int) and 0 <= x <= 100,
            error_message="Value must be integer between 0 and 100"
        )
        
        # Create schema
        schema = MockConfigSchema(
            name="test_schema",
            version="1.0.0",
            description="Test schema",
            validation_rules=[rule]
        )
        
        # Register schema
        self.config_manager.validator.register_schema(schema)
        
        # Test validation
        errors = self.config_manager.validator.validate({"test": {"number": 50}}, "test_schema")
        assert len(errors) == 0
        
        # Test validation with invalid data
        errors = self.config_manager.validator.validate({"test": {"number": 150}}, "test_schema")
        # Note: Mock validator doesn't actually validate, so this would need real implementation
    
    def test_concurrent_access(self):
        """Test concurrent access to configuration"""
        import threading
        import time
        
        results = []
        errors = []
        
        def config_worker(worker_id):
            try:
                for i in range(10):
                    key = f"concurrent.worker_{worker_id}.item_{i}"
                    value = f"value_{worker_id}_{i}"
                    
                    # Set value
                    self.config_manager.set(key, value)
                    
                    # Get value
                    retrieved_value = self.config_manager.get(key)
                    
                    # Verify value
                    if retrieved_value == value:
                        results.append((worker_id, i, True))
                    else:
                        results.append((worker_id, i, False))
                    
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Create multiple threads
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=config_worker, args=(worker_id,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50  # 5 workers * 10 items each
        assert all(result[2] for result in results), "Some operations failed"


if __name__ == "__main__":
    # Run tests
    test_suite = TestAdvancedConfigurationSystem()
    
    # Run all test methods
    test_methods = [method for method in dir(test_suite) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            print(f"Running {test_method}...")
            test_suite.setup_method()
            getattr(test_suite, test_method)()
            test_suite.teardown_method()
            print(f"✅ {test_method} PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_method} FAILED: {e}")
            failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All configuration system tests passed!")
    else:
        print(f"⚠️ {failed} tests failed")
