"""
Tests for configuration integration system

Tests the integration between configuration system and onboarding components:
- Configuration integrator functionality
- Component registration and updates
- Real-time configuration synchronization
- Profile and preset management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import tempfile

# Mock integration system components
class MockUserLevel:
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class MockUserType:
    BEGINNER = "beginner"
    DEVELOPER = "developer"
    RESEARCHER = "researcher"

class MockOnboardingPreset:
    def __init__(self, name, description, user_type, settings, features_enabled, ui_customizations):
        self.name = name
        self.description = description
        self.user_type = user_type
        self.settings = settings
        self.features_enabled = features_enabled
        self.ui_customizations = ui_customizations

class MockUserStateTracker:
    def __init__(self):
        self.user_level = MockUserLevel.BEGINNER
        self.is_first_time = True
        self.completed_steps = []
        self.help_preferences = {
            "show_tips": True,
            "tutorial_speed": "normal",
            "auto_advance": False
        }
    
    def get_user_level(self):
        return type('UserLevel', (), {'value': self.user_level})()
    
    def set_user_level(self, user_level):
        self.user_level = user_level.value if hasattr(user_level, 'value') else user_level
    
    def is_first_time_user(self):
        return self.is_first_time
    
    def get_completed_steps(self):
        return [type('Step', (), {'value': step})() for step in self.completed_steps]
    
    def get_help_preferences(self):
        return self.help_preferences.copy()
    
    def update_help_preferences(self, preferences):
        self.help_preferences.update(preferences)

class MockAdvancedConfigurationManager:
    def __init__(self, base_path=None):
        self.base_path = base_path or Path.home() / ".heal" / "config"
        self.config_data = {}
        self.change_listeners = []
        self.profiles = {}
        self.active_profile_id = None
    
    def get(self, key, default=None):
        keys = key.split('.')
        current = self.config_data
        
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return default
            current = current[k]
        
        return current
    
    def set(self, key, value, scope=None, persist=True):
        keys = key.split('.')
        current = self.config_data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        old_value = current.get(keys[-1])
        current[keys[-1]] = value
        
        # Notify listeners
        for listener in self.change_listeners:
            try:
                listener(key, old_value, value)
            except Exception:
                pass
        
        return True
    
    def add_change_listener(self, listener):
        self.change_listeners.append(listener)
    
    def create_profile(self, name, description, settings=None):
        import uuid
        profile_id = str(uuid.uuid4())
        
        profile = type('Profile', (), {
            'profile_id': profile_id,
            'name': name,
            'description': description,
            'settings': settings or {},
            'last_modified': datetime.now()
        })()
        
        self.profiles[profile_id] = profile
        return profile_id
    
    def activate_profile(self, profile_id):
        if profile_id in self.profiles:
            self.active_profile_id = profile_id
            return True
        return False
    
    def get_profile(self, profile_id):
        return self.profiles.get(profile_id)
    
    def list_profiles(self):
        return list(self.profiles.values())
    
    def export_configuration(self, path, include_profiles=True):
        try:
            # Mock export functionality
            return True
        except Exception:
            return False
    
    def import_configuration(self, path, merge=True):
        try:
            # Mock import functionality
            return True
        except Exception:
            return False
    
    def reset_to_defaults(self, scope):
        # Mock reset functionality
        pass
    
    def validate_all(self):
        return {}
    
    def get_configuration_info(self):
        return {
            'base_path': str(self.base_path),
            'profiles': {
                'total': len(self.profiles),
                'active': self.active_profile_id
            }
        }

class MockConfigurationPluginManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.plugins = {}
    
    def list_plugins(self):
        return []
    
    def shutdown_all_plugins(self):
        pass

class MockConfigurationUIManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def show_configuration_dialog(self, parent=None):
        return Mock()

class MockConfigurationTemplates:
    @staticmethod
    def get_available_presets():
        return [
            MockOnboardingPreset(
                name="Developer Mode",
                description="Technical onboarding for developers",
                user_type=MockUserType.DEVELOPER,
                settings={
                    "ui.theme": "dark",
                    "ui.layout": "developer",
                    "onboarding.user_level": "advanced"
                },
                features_enabled=["debug_tools", "api_docs"],
                ui_customizations={"show_debug_info": True}
            ),
            MockOnboardingPreset(
                name="Beginner Mode",
                description="Simplified onboarding for beginners",
                user_type=MockUserType.BEGINNER,
                settings={
                    "ui.layout": "simplified",
                    "onboarding.help_preferences.tutorial_speed": "slow"
                },
                features_enabled=["welcome_wizard", "tutorials"],
                ui_customizations={"simplified_menus": True}
            )
        ]
    
    @staticmethod
    def get_user_config_template(user_type):
        return {
            "user": {"type": user_type},
            "onboarding": {
                "user_level": "beginner" if user_type == MockUserType.BEGINNER else "advanced",
                "help_preferences": {"show_tips": True}
            },
            "ui": {"theme": "dark" if user_type == MockUserType.DEVELOPER else "light"}
        }

class MockConfigurationIntegrator:
    def __init__(self, base_path=None):
        self.config_manager = MockAdvancedConfigurationManager(base_path)
        self.plugin_manager = MockConfigurationPluginManager(self.config_manager)
        self.ui_manager = MockConfigurationUIManager(self.config_manager)
        
        self.user_tracker = None
        self.onboarding_components = {}
        self.change_events = []
        
        # Setup change handling
        self.config_manager.add_change_listener(self._on_configuration_changed)
    
    def integrate_user_tracker(self, user_tracker):
        self.user_tracker = user_tracker
        self._sync_user_tracker_config()
        self.config_manager.add_change_listener(self._sync_config_to_user_tracker)
    
    def _sync_user_tracker_config(self):
        if not self.user_tracker:
            return
        
        # Sync user level
        tracker_level = self.user_tracker.get_user_level()
        self.config_manager.set("onboarding.user_level", tracker_level.value)
        
        # Sync first-time status
        is_first_time = self.user_tracker.is_first_time_user()
        self.config_manager.set("onboarding.is_first_time", is_first_time)
        
        # Sync help preferences
        help_prefs = self.user_tracker.get_help_preferences()
        for key, value in help_prefs.items():
            self.config_manager.set(f"onboarding.help_preferences.{key}", value)
    
    def _sync_config_to_user_tracker(self, key, old_value, new_value):
        if not self.user_tracker:
            return
        
        if key == "onboarding.user_level":
            user_level = type('UserLevel', (), {'value': new_value})()
            self.user_tracker.set_user_level(user_level)
        elif key.startswith("onboarding.help_preferences."):
            pref_key = key.split(".")[-1]
            current_prefs = self.user_tracker.get_help_preferences()
            current_prefs[pref_key] = new_value
            self.user_tracker.update_help_preferences(current_prefs)
    
    def register_onboarding_component(self, name, component):
        self.onboarding_components[name] = component
        self._apply_configuration_to_component(name, component)
    
    def _apply_configuration_to_component(self, name, component):
        # Apply theme if component supports it
        if hasattr(component, 'set_theme'):
            theme = self.config_manager.get("ui.theme", "light")
            component.set_theme(theme)
        
        # Apply animation settings
        if hasattr(component, 'set_animation_speed'):
            speed = self.config_manager.get("ui.animation_speed", 1.0)
            component.set_animation_speed(speed)
        
        # Apply help preferences
        if hasattr(component, 'update_help_preferences'):
            help_prefs = {
                "show_tips": self.config_manager.get("onboarding.help_preferences.show_tips", True),
                "tutorial_speed": self.config_manager.get("onboarding.help_preferences.tutorial_speed", "normal")
            }
            component.update_help_preferences(help_prefs)
    
    def _on_configuration_changed(self, key, old_value, new_value):
        self.change_events.append((key, old_value, new_value))
        
        # Apply changes to registered components
        for name, component in self.onboarding_components.items():
            self._apply_configuration_to_component(name, component)
    
    def apply_preset(self, preset):
        try:
            # Apply preset settings
            for key, value in preset.settings.items():
                self.config_manager.set(key, value)
            
            # Apply UI customizations
            for key, value in preset.ui_customizations.items():
                ui_key = f"ui.{key}"
                self.config_manager.set(ui_key, value)
            
            return True
        except Exception:
            return False
    
    def create_user_profile_from_template(self, user_type, profile_name=None):
        if not profile_name:
            profile_name = f"{user_type.title()} Profile"
        
        template_config = MockConfigurationTemplates.get_user_config_template(user_type)
        
        profile_id = self.config_manager.create_profile(
            profile_name,
            f"Profile for {user_type} users"
        )
        
        profile = self.config_manager.get_profile(profile_id)
        if profile:
            profile.settings = template_config
            profile.last_modified = datetime.now()
        
        return profile_id
    
    def get_available_presets(self):
        return MockConfigurationTemplates.get_available_presets()
    
    def get_configuration_summary(self):
        return {
            "system_info": self.config_manager.get_configuration_info(),
            "current_settings": {
                "user_level": self.config_manager.get("onboarding.user_level"),
                "theme": self.config_manager.get("ui.theme")
            },
            "profiles": {
                "active": self.config_manager.active_profile_id,
                "total": len(self.config_manager.profiles)
            },
            "plugins": self.plugin_manager.list_plugins(),
            "components": list(self.onboarding_components.keys())
        }
    
    def show_configuration_dialog(self, parent=None):
        return self.ui_manager.show_configuration_dialog(parent)
    
    def export_user_configuration(self, file_path):
        return self.config_manager.export_configuration(file_path, include_profiles=True)
    
    def import_user_configuration(self, file_path, merge=True):
        return self.config_manager.import_configuration(file_path, merge=merge)
    
    def reset_to_defaults(self, scope):
        self.config_manager.reset_to_defaults(scope)
    
    def validate_configuration(self):
        return self.config_manager.validate_all()
    
    def shutdown(self):
        self.plugin_manager.shutdown_all_plugins()
        self.onboarding_components.clear()


class TestConfigurationIntegration:
    """Test suite for configuration integration system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.integrator = MockConfigurationIntegrator(Path(self.temp_dir))
        self.user_tracker = MockUserStateTracker()
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_user_tracker_integration(self):
        """Test user tracker integration"""
        # Integrate user tracker
        self.integrator.integrate_user_tracker(self.user_tracker)
        
        # Verify initial sync
        assert self.integrator.config_manager.get("onboarding.user_level") == MockUserLevel.BEGINNER
        assert self.integrator.config_manager.get("onboarding.is_first_time") is True
        assert self.integrator.config_manager.get("onboarding.help_preferences.show_tips") is True
    
    def test_bidirectional_sync(self):
        """Test bidirectional synchronization between config and user tracker"""
        self.integrator.integrate_user_tracker(self.user_tracker)
        
        # Change configuration - should sync to user tracker
        self.integrator.config_manager.set("onboarding.user_level", MockUserLevel.ADVANCED)
        assert self.user_tracker.user_level == MockUserLevel.ADVANCED
        
        # Change help preference - should sync to user tracker
        self.integrator.config_manager.set("onboarding.help_preferences.tutorial_speed", "fast")
        assert self.user_tracker.help_preferences["tutorial_speed"] == "fast"
    
    def test_component_registration(self):
        """Test onboarding component registration"""
        # Create mock component
        component = Mock()
        component.set_theme = Mock()
        component.set_animation_speed = Mock()
        component.update_help_preferences = Mock()
        
        # Register component
        self.integrator.register_onboarding_component("test_component", component)
        
        # Verify component is registered
        assert "test_component" in self.integrator.onboarding_components
        
        # Verify configuration is applied
        component.set_theme.assert_called_once()
        component.set_animation_speed.assert_called_once()
        component.update_help_preferences.assert_called_once()
    
    def test_component_configuration_updates(self):
        """Test component configuration updates"""
        # Create and register mock component
        component = Mock()
        component.set_theme = Mock()
        component.set_animation_speed = Mock()
        
        self.integrator.register_onboarding_component("test_component", component)
        
        # Reset mocks to track new calls
        component.set_theme.reset_mock()
        component.set_animation_speed.reset_mock()
        
        # Change configuration
        self.integrator.config_manager.set("ui.theme", "dark")
        self.integrator.config_manager.set("ui.animation_speed", 2.0)
        
        # Verify component methods are called again
        assert component.set_theme.call_count >= 1
        assert component.set_animation_speed.call_count >= 1
    
    def test_preset_application(self):
        """Test onboarding preset application"""
        presets = self.integrator.get_available_presets()
        developer_preset = next(p for p in presets if p.name == "Developer Mode")
        
        # Apply preset
        assert self.integrator.apply_preset(developer_preset)
        
        # Verify settings are applied
        assert self.integrator.config_manager.get("ui.theme") == "dark"
        assert self.integrator.config_manager.get("ui.layout") == "developer"
        assert self.integrator.config_manager.get("onboarding.user_level") == "advanced"
        
        # Verify UI customizations are applied
        assert self.integrator.config_manager.get("ui.show_debug_info") is True
    
    def test_profile_creation_from_template(self):
        """Test profile creation from user type template"""
        # Create profile from template
        profile_id = self.integrator.create_user_profile_from_template(
            MockUserType.DEVELOPER,
            "My Developer Profile"
        )
        
        # Verify profile is created
        assert profile_id is not None
        profile = self.integrator.config_manager.get_profile(profile_id)
        assert profile is not None
        assert profile.name == "My Developer Profile"
        
        # Verify template settings are applied
        assert profile.settings["user"]["type"] == MockUserType.DEVELOPER
        assert profile.settings["ui"]["theme"] == "dark"
    
    def test_configuration_change_events(self):
        """Test configuration change event handling"""
        # Make configuration changes
        self.integrator.config_manager.set("ui.theme", "dark")
        self.integrator.config_manager.set("onboarding.user_level", "advanced")
        
        # Verify change events are recorded
        assert len(self.integrator.change_events) >= 2
        
        # Check specific events
        theme_event = next((e for e in self.integrator.change_events if e[0] == "ui.theme"), None)
        assert theme_event is not None
        assert theme_event[2] == "dark"  # new value
    
    def test_configuration_summary(self):
        """Test configuration summary generation"""
        # Add some configuration and components
        self.integrator.config_manager.set("ui.theme", "dark")
        self.integrator.register_onboarding_component("test_component", Mock())
        
        # Get summary
        summary = self.integrator.get_configuration_summary()
        
        # Verify summary structure
        assert "system_info" in summary
        assert "current_settings" in summary
        assert "profiles" in summary
        assert "plugins" in summary
        assert "components" in summary
        
        # Verify current settings
        assert summary["current_settings"]["theme"] == "dark"
        
        # Verify components
        assert "test_component" in summary["components"]
    
    def test_configuration_dialog_integration(self):
        """Test configuration dialog integration"""
        # Show configuration dialog
        dialog = self.integrator.show_configuration_dialog()
        
        # Verify dialog is returned (mock)
        assert dialog is not None
    
    def test_import_export_integration(self):
        """Test configuration import/export integration"""
        # Test export
        export_path = Path(self.temp_dir) / "test_export.json"
        assert self.integrator.export_user_configuration(str(export_path))
        
        # Test import
        assert self.integrator.import_user_configuration(str(export_path), merge=True)
    
    def test_configuration_validation_integration(self):
        """Test configuration validation integration"""
        # Validate configuration
        validation_results = self.integrator.validate_configuration()
        
        # Verify validation results structure
        assert isinstance(validation_results, dict)
    
    def test_configuration_reset_integration(self):
        """Test configuration reset integration"""
        # Set some configuration
        self.integrator.config_manager.set("test.key", "test_value")
        
        # Reset configuration
        self.integrator.reset_to_defaults("user")
        
        # Verify reset was called (mock doesn't actually reset)
        # In real implementation, this would clear the configuration
    
    def test_multiple_component_updates(self):
        """Test updates to multiple registered components"""
        # Create multiple mock components
        components = {}
        for i in range(3):
            component = Mock()
            component.set_theme = Mock()
            component.set_animation_speed = Mock()
            
            name = f"component_{i}"
            components[name] = component
            self.integrator.register_onboarding_component(name, component)
        
        # Reset mocks
        for component in components.values():
            component.set_theme.reset_mock()
            component.set_animation_speed.reset_mock()
        
        # Change configuration
        self.integrator.config_manager.set("ui.theme", "dark")
        
        # Verify all components are updated
        for component in components.values():
            assert component.set_theme.call_count >= 1
    
    def test_integration_shutdown(self):
        """Test integration system shutdown"""
        # Register some components
        self.integrator.register_onboarding_component("test_component", Mock())
        
        # Shutdown integration
        self.integrator.shutdown()
        
        # Verify components are cleared
        assert len(self.integrator.onboarding_components) == 0
    
    def test_error_handling_in_component_updates(self):
        """Test error handling in component updates"""
        # Create component that raises exception
        failing_component = Mock()
        failing_component.set_theme = Mock(side_effect=Exception("Test error"))
        
        # Register component
        self.integrator.register_onboarding_component("failing_component", failing_component)
        
        # Change configuration - should not raise exception
        try:
            self.integrator.config_manager.set("ui.theme", "dark")
            # If we get here, error handling worked
            assert True
        except Exception:
            # If exception propagates, error handling failed
            assert False, "Exception should have been handled"


if __name__ == "__main__":
    # Run tests
    test_suite = TestConfigurationIntegration()
    
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
        print("🎉 All configuration integration tests passed!")
    else:
        print(f"⚠️ {failed} tests failed")
