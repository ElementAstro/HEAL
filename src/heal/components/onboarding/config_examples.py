"""
Configuration Examples and Usage Patterns for HEAL Onboarding System

Provides comprehensive examples of how to use the advanced configuration system,
including common patterns, best practices, and real-world scenarios.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

from .config_system import (
    AdvancedConfigurationManager, ConfigScope, ConfigurationProfile,
    ConfigValidationRule, ConfigSchema
)
from .config_templates import ConfigurationTemplates, UserType
from .config_plugins import ConfigurationPluginManager, create_default_plugin_manager
from .config_ui_manager import ConfigurationUIManager


class ConfigurationExamples:
    """Examples and patterns for configuration usage"""
    
    @staticmethod
    def basic_usage_example():
        """Basic configuration usage example"""
        print("=== Basic Configuration Usage ===")
        
        # Create configuration manager
        config_manager = AdvancedConfigurationManager()
        
        # Set basic configuration values
        config_manager.set("onboarding.user_level", "intermediate")
        config_manager.set("ui.theme", "dark")
        config_manager.set("ui.animation_speed", 1.5)
        
        # Get configuration values
        user_level = config_manager.get("onboarding.user_level")
        theme = config_manager.get("ui.theme")
        animation_speed = config_manager.get("ui.animation_speed", 1.0)
        
        print(f"User Level: {user_level}")
        print(f"Theme: {theme}")
        print(f"Animation Speed: {animation_speed}")
        
        # Get all settings
        all_settings = config_manager.get_all_settings()
        print(f"Total settings: {len(all_settings)}")
    
    @staticmethod
    def profile_management_example():
        """Configuration profile management example"""
        print("\n=== Profile Management ===")
        
        config_manager = AdvancedConfigurationManager()
        
        # Create profiles for different user types
        profiles = [
            ("Developer Profile", UserType.DEVELOPER, {
                "ui.theme": "dark",
                "ui.layout": "developer",
                "onboarding.user_level": "advanced",
                "system.debug_mode": True
            }),
            ("Researcher Profile", UserType.RESEARCHER, {
                "ui.layout": "research",
                "workflow.auto_save_interval": 120,
                "onboarding.recommendations.types": ["analysis", "data"]
            }),
            ("Beginner Profile", UserType.BEGINNER, {
                "ui.layout": "simplified",
                "onboarding.help_preferences.tutorial_speed": "slow",
                "onboarding.feature_discovery.discovery_pace": "slow"
            })
        ]
        
        created_profiles = []
        for name, user_type, settings in profiles:
            profile_id = config_manager.create_profile(name, f"Profile for {user_type.value}")
            
            # Apply settings to profile
            profile = config_manager.get_profile(profile_id)
            if profile:
                for key, value in settings.items():
                    profile.settings[key] = value
                profile.last_modified = datetime.now()
            
            created_profiles.append(profile_id)
            print(f"Created profile: {name} ({profile_id})")
        
        # Activate developer profile
        if created_profiles:
            config_manager.activate_profile(created_profiles[0])
            print(f"Activated profile: {created_profiles[0]}")
        
        # List all profiles
        all_profiles = config_manager.list_profiles()
        print(f"Total profiles: {len(all_profiles)}")
        for profile in all_profiles:
            print(f"  - {profile.name}: {profile.description}")
    
    @staticmethod
    def validation_example():
        """Configuration validation example"""
        print("\n=== Configuration Validation ===")
        
        config_manager = AdvancedConfigurationManager()
        
        # Try to set invalid values
        invalid_settings = [
            ("onboarding.user_level", "invalid_level"),
            ("onboarding.help_preferences.tutorial_speed", "super_fast"),
            ("ui.animation_speed", -1.0)
        ]
        
        for key, value in invalid_settings:
            success = config_manager.set(key, value, validate=True)
            print(f"Setting {key} = {value}: {'✓' if success else '✗'}")
        
        # Validate all configurations
        validation_results = config_manager.validate_all()
        for scope, errors in validation_results.items():
            if errors:
                print(f"Validation errors in {scope}: {errors}")
            else:
                print(f"No validation errors in {scope}")
    
    @staticmethod
    def change_listener_example():
        """Configuration change listener example"""
        print("\n=== Change Listeners ===")
        
        config_manager = AdvancedConfigurationManager()
        
        # Define change listener
        def on_theme_changed(key: str, old_value: Any, new_value: Any):
            if "theme" in key:
                print(f"Theme changed: {old_value} → {new_value}")
        
        def on_any_change(key: str, old_value: Any, new_value: Any):
            print(f"Configuration changed: {key}")
        
        # Add listeners
        config_manager.add_change_listener(on_theme_changed)
        config_manager.add_change_listener(on_any_change)
        
        # Make changes to trigger listeners
        config_manager.set("ui.theme", "light")
        config_manager.set("ui.theme", "dark")
        config_manager.set("onboarding.user_level", "advanced")
    
    @staticmethod
    def scope_management_example():
        """Configuration scope management example"""
        print("\n=== Scope Management ===")
        
        config_manager = AdvancedConfigurationManager()
        
        # Set values in different scopes
        config_manager.set("ui.theme", "light", scope=ConfigScope.GLOBAL)
        config_manager.set("ui.theme", "dark", scope=ConfigScope.USER)
        config_manager.set("ui.theme", "high_contrast", scope=ConfigScope.SESSION)
        config_manager.set("ui.theme", "custom", scope=ConfigScope.TEMPORARY)
        
        # Get value (should return highest priority scope value)
        theme = config_manager.get("ui.theme")
        print(f"Current theme (highest priority): {theme}")
        
        # Get value from specific scope
        global_theme = config_manager.get("ui.theme", scope=ConfigScope.GLOBAL)
        user_theme = config_manager.get("ui.theme", scope=ConfigScope.USER)
        
        print(f"Global theme: {global_theme}")
        print(f"User theme: {user_theme}")
        
        # Reset scope
        config_manager.reset_to_defaults(ConfigScope.TEMPORARY)
        theme_after_reset = config_manager.get("ui.theme")
        print(f"Theme after temporary reset: {theme_after_reset}")
    
    @staticmethod
    def import_export_example():
        """Configuration import/export example"""
        print("\n=== Import/Export ===")
        
        config_manager = AdvancedConfigurationManager()
        
        # Set up some configuration
        config_manager.set("onboarding.user_level", "advanced")
        config_manager.set("ui.theme", "dark")
        config_manager.set("ui.layout", "developer")
        
        # Create a profile
        profile_id = config_manager.create_profile("Export Test", "Test profile for export")
        
        # Export configuration
        export_path = "config_export_example.json"
        success = config_manager.export_configuration(export_path, include_profiles=True)
        print(f"Export to {export_path}: {'✓' if success else '✗'}")
        
        # Reset configuration
        config_manager.reset_to_defaults(ConfigScope.USER)
        
        # Import configuration
        success = config_manager.import_configuration(export_path, merge=False)
        print(f"Import from {export_path}: {'✓' if success else '✗'}")
        
        # Verify imported values
        user_level = config_manager.get("onboarding.user_level")
        theme = config_manager.get("ui.theme")
        print(f"Imported user level: {user_level}")
        print(f"Imported theme: {theme}")
        
        # Clean up
        try:
            Path(export_path).unlink()
        except:
            pass
    
    @staticmethod
    def plugin_system_example():
        """Plugin system usage example"""
        print("\n=== Plugin System ===")
        
        config_manager = AdvancedConfigurationManager()
        plugin_manager = create_default_plugin_manager(config_manager)
        
        # List loaded plugins
        plugins = plugin_manager.list_plugins()
        print(f"Loaded plugins: {len(plugins)}")
        for plugin in plugins:
            print(f"  - {plugin['name']} v{plugin['version']}: {plugin['description']}")
        
        # Make a configuration change to trigger audit plugin
        config_manager.set("security.auto_lock_timeout", 300)
        
        # Get audit log from audit plugin
        audit_plugin = plugin_manager.get_plugin("Audit Listener")
        if audit_plugin:
            audit_log = audit_plugin.get_audit_log()
            print(f"Audit log entries: {len(audit_log)}")
            for entry in audit_log[-3:]:  # Show last 3 entries
                print(f"  {entry['timestamp']}: {entry['key']} changed")
    
    @staticmethod
    def template_usage_example():
        """Configuration template usage example"""
        print("\n=== Configuration Templates ===")
        
        # Get predefined templates
        beginner_config = ConfigurationTemplates.get_user_config_template(UserType.BEGINNER)
        developer_config = ConfigurationTemplates.get_user_config_template(UserType.DEVELOPER)
        
        print("Beginner vs Developer Configuration Differences:")
        
        # Compare specific settings
        comparisons = [
            ("onboarding.user_level", "User Level"),
            ("onboarding.help_preferences.tutorial_speed", "Tutorial Speed"),
            ("ui.layout", "UI Layout"),
            ("ui.theme", "Theme")
        ]
        
        for key, label in comparisons:
            beginner_val = ConfigurationTemplates._get_nested_value(beginner_config, key)
            developer_val = ConfigurationTemplates._get_nested_value(developer_config, key)
            print(f"  {label}: Beginner={beginner_val}, Developer={developer_val}")
        
        # Show available presets
        presets = ConfigurationTemplates.get_onboarding_presets()
        print(f"\nAvailable presets: {len(presets)}")
        for preset in presets:
            print(f"  - {preset.name}: {preset.description}")
    
    @staticmethod
    def advanced_customization_example():
        """Advanced customization example"""
        print("\n=== Advanced Customization ===")
        
        config_manager = AdvancedConfigurationManager()
        
        # Create custom validation rule
        def validate_custom_timeout(value):
            return isinstance(value, int) and 10 <= value <= 7200
        
        custom_rule = ConfigValidationRule(
            field_path="custom.timeout_seconds",
            validator=validate_custom_timeout,
            error_message="Timeout must be between 10 and 7200 seconds",
            required=True,
            default_value=300
        )
        
        # Create custom schema
        custom_schema = ConfigSchema(
            name="custom_app",
            version="1.0.0",
            description="Custom application settings",
            validation_rules=[custom_rule],
            required_keys=["custom.timeout_seconds"]
        )
        
        # Register schema
        config_manager.validator.register_schema(custom_schema)
        
        # Test custom validation
        config_manager.set("custom.timeout_seconds", 150)  # Valid
        success1 = config_manager.set("custom.timeout_seconds", 5, validate=True)  # Invalid
        
        print(f"Set valid timeout: ✓")
        print(f"Set invalid timeout: {'✓' if success1 else '✗'}")
        
        # Complex nested configuration
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
        
        # Set complex configuration
        for key, value in complex_config.items():
            config_manager.set(key, value)
        
        # Retrieve and display
        features = config_manager.get("features")
        print(f"Complex configuration set successfully: {features is not None}")
    
    @staticmethod
    def run_all_examples():
        """Run all configuration examples"""
        print("HEAL Onboarding Configuration System Examples")
        print("=" * 50)
        
        ConfigurationExamples.basic_usage_example()
        ConfigurationExamples.profile_management_example()
        ConfigurationExamples.validation_example()
        ConfigurationExamples.change_listener_example()
        ConfigurationExamples.scope_management_example()
        ConfigurationExamples.import_export_example()
        ConfigurationExamples.plugin_system_example()
        ConfigurationExamples.template_usage_example()
        ConfigurationExamples.advanced_customization_example()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")


class ConfigurationBestPractices:
    """Best practices and guidelines for configuration usage"""
    
    @staticmethod
    def get_best_practices() -> List[Dict[str, str]]:
        """Get configuration best practices"""
        return [
            {
                "title": "Use Appropriate Scopes",
                "description": "Use GLOBAL for system-wide defaults, USER for personal preferences, SESSION for temporary settings, and TEMPORARY for short-lived overrides.",
                "example": "config_manager.set('ui.theme', 'dark', scope=ConfigScope.USER)"
            },
            {
                "title": "Always Validate Critical Settings",
                "description": "Enable validation for security-sensitive or system-critical configuration values.",
                "example": "config_manager.set('security.timeout', 300, validate=True)"
            },
            {
                "title": "Use Profiles for Different Workflows",
                "description": "Create profiles for different user types or workflows to provide optimized experiences.",
                "example": "profile_id = config_manager.create_profile('Developer', 'Settings for developers')"
            },
            {
                "title": "Implement Change Listeners Carefully",
                "description": "Use change listeners for reactive updates but avoid heavy operations that could block the UI.",
                "example": "config_manager.add_change_listener(lightweight_update_function)"
            },
            {
                "title": "Regular Configuration Backups",
                "description": "Create regular backups of configuration, especially before major changes.",
                "example": "backup_manager.create_backup('before_major_update')"
            },
            {
                "title": "Use Templates for Consistency",
                "description": "Use configuration templates to ensure consistent setups across different user types.",
                "example": "config = ConfigurationTemplates.get_user_config_template(UserType.BEGINNER)"
            },
            {
                "title": "Leverage Plugin System",
                "description": "Use plugins to extend configuration capabilities without modifying core code.",
                "example": "plugin_manager.register_plugin(CustomValidatorPlugin())"
            },
            {
                "title": "Document Custom Configurations",
                "description": "Document any custom configuration keys and their expected values.",
                "example": "# custom.feature_flags.experimental_ui: boolean - Enable experimental UI features"
            }
        ]
    
    @staticmethod
    def get_common_patterns() -> List[Dict[str, str]]:
        """Get common configuration patterns"""
        return [
            {
                "pattern": "Feature Flags",
                "description": "Use configuration to enable/disable features dynamically",
                "code": """
config_manager.set('features.experimental_ui', True)
if config_manager.get('features.experimental_ui', False):
    enable_experimental_features()
"""
            },
            {
                "pattern": "Environment-Specific Settings",
                "description": "Different settings for development, testing, and production",
                "code": """
env = config_manager.get('system.environment', 'production')
if env == 'development':
    config_manager.set('system.debug_mode', True)
"""
            },
            {
                "pattern": "User Preference Inheritance",
                "description": "Layer user preferences over system defaults",
                "code": """
# System default
config_manager.set('ui.theme', 'light', scope=ConfigScope.GLOBAL)
# User preference
config_manager.set('ui.theme', 'dark', scope=ConfigScope.USER)
# Result: user gets dark theme
"""
            },
            {
                "pattern": "Configuration Migration",
                "description": "Handle configuration format changes between versions",
                "code": """
migrator = ConfigurationMigrator(config_manager)
migrated_config = migrator.migrate_configuration(
    old_config, '1.0.0', '1.1.0'
)
"""
            }
        ]


if __name__ == "__main__":
    # Run examples when script is executed directly
    ConfigurationExamples.run_all_examples()
