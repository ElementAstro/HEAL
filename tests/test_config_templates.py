"""
Tests for configuration templates and presets

Tests the configuration template system including:
- User type templates
- Onboarding presets
- UI themes and layouts
- Template validation and consistency
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

# Mock the template system components
class MockUserType:
    BEGINNER = "beginner"
    POWER_USER = "power_user"
    DEVELOPER = "developer"
    ADMINISTRATOR = "administrator"
    RESEARCHER = "researcher"
    EDUCATOR = "educator"

class MockOnboardingPreset:
    def __init__(self, name, description, user_type, settings, features_enabled, ui_customizations):
        self.name = name
        self.description = description
        self.user_type = user_type
        self.settings = settings
        self.features_enabled = features_enabled
        self.ui_customizations = ui_customizations

class MockConfigurationTemplates:
    """Mock configuration templates class"""
    
    @staticmethod
    def get_default_global_config():
        return {
            "system": {
                "version": "1.0.0",
                "locale": "en_US",
                "timezone": "UTC",
                "debug_mode": False,
                "telemetry_enabled": True,
                "auto_update": True,
                "crash_reporting": True
            },
            "performance": {
                "cache_size_mb": 100,
                "max_concurrent_operations": 5,
                "animation_quality": "high",
                "lazy_loading": True,
                "preload_content": True
            },
            "security": {
                "auto_lock_timeout": 30,
                "require_confirmation": True,
                "secure_storage": True,
                "audit_logging": True
            },
            "accessibility": {
                "high_contrast": False,
                "large_fonts": False,
                "screen_reader_support": False,
                "keyboard_navigation": True,
                "reduced_motion": False
            },
            "onboarding": {
                "default_user_level": "beginner",
                "skip_welcome_for_returning": False,
                "auto_detect_experience": True,
                "progressive_disclosure": True,
                "contextual_help_enabled": True,
                "smart_recommendations": True
            }
        }
    
    @staticmethod
    def get_user_config_template(user_type):
        base_config = {
            "user": {
                "type": user_type,
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "login_count": 0,
                "preferred_language": "en",
                "timezone": "auto"
            },
            "onboarding": {
                "is_first_time": True,
                "completed_steps": [],
                "skipped_steps": [],
                "user_level": "beginner",
                "onboarding_version": "1.0.0",
                "completion_percentage": 0,
                "estimated_completion_time": 0,
                "last_step_completed": None,
                "help_preferences": {
                    "show_tips": True,
                    "show_tooltips": True,
                    "show_contextual_help": True,
                    "tutorial_speed": "normal",
                    "auto_advance": False,
                    "sound_enabled": True,
                    "animation_enabled": True
                },
                "feature_discovery": {
                    "auto_highlight": True,
                    "discovery_pace": "normal",
                    "show_advanced_features": False,
                    "feature_categories_enabled": ["basic", "intermediate"]
                },
                "recommendations": {
                    "enabled": True,
                    "frequency": "normal",
                    "types": ["workflow", "optimization", "learning"],
                    "auto_apply_safe": False,
                    "notification_style": "subtle"
                }
            },
            "ui": {
                "theme": "auto",
                "color_scheme": "default",
                "font_size": "medium",
                "layout": "standard",
                "sidebar_position": "left",
                "toolbar_style": "icons_and_text",
                "animation_speed": 1.0,
                "transition_effects": True
            },
            "workflow": {
                "auto_save_interval": 300,
                "backup_frequency": "daily",
                "default_workspace": "default",
                "recent_items_count": 10,
                "quick_actions": [],
                "custom_shortcuts": {}
            },
            "privacy": {
                "analytics_opt_in": True,
                "usage_tracking": True,
                "error_reporting": True,
                "feature_suggestions": True,
                "personalization": True
            }
        }
        
        # Customize based on user type
        if user_type == MockUserType.BEGINNER:
            base_config["onboarding"]["help_preferences"]["tutorial_speed"] = "slow"
            base_config["onboarding"]["feature_discovery"]["discovery_pace"] = "slow"
            base_config["onboarding"]["recommendations"]["frequency"] = "high"
            base_config["ui"]["layout"] = "simplified"
            
        elif user_type == MockUserType.POWER_USER:
            base_config["onboarding"]["user_level"] = "intermediate"
            base_config["onboarding"]["help_preferences"]["tutorial_speed"] = "fast"
            base_config["onboarding"]["feature_discovery"]["show_advanced_features"] = True
            base_config["onboarding"]["feature_discovery"]["feature_categories_enabled"].append("advanced")
            base_config["ui"]["layout"] = "compact"
            
        elif user_type == MockUserType.DEVELOPER:
            base_config["onboarding"]["user_level"] = "advanced"
            base_config["onboarding"]["help_preferences"]["show_tips"] = False
            base_config["onboarding"]["feature_discovery"]["discovery_pace"] = "fast"
            base_config["onboarding"]["feature_discovery"]["feature_categories_enabled"].extend(["advanced", "expert"])
            base_config["ui"]["theme"] = "dark"
            base_config["ui"]["layout"] = "developer"
            base_config["system"]["debug_mode"] = True
            
        elif user_type == MockUserType.ADMINISTRATOR:
            base_config["onboarding"]["user_level"] = "advanced"
            base_config["onboarding"]["recommendations"]["types"].append("security")
            base_config["onboarding"]["feature_discovery"]["feature_categories_enabled"].extend(["advanced", "admin"])
            base_config["security"]["audit_logging"] = True
            base_config["ui"]["layout"] = "admin"
            
        elif user_type == MockUserType.RESEARCHER:
            base_config["onboarding"]["user_level"] = "intermediate"
            base_config["onboarding"]["recommendations"]["types"].extend(["analysis", "data"])
            base_config["workflow"]["auto_save_interval"] = 120
            base_config["workflow"]["backup_frequency"] = "hourly"
            base_config["ui"]["layout"] = "research"
            
        elif user_type == MockUserType.EDUCATOR:
            base_config["onboarding"]["help_preferences"]["tutorial_speed"] = "normal"
            base_config["onboarding"]["recommendations"]["types"].append("teaching")
            base_config["ui"]["layout"] = "presentation"
            base_config["accessibility"]["large_fonts"] = True
        
        return base_config
    
    @staticmethod
    def get_onboarding_presets():
        return [
            MockOnboardingPreset(
                name="First-Time User",
                description="Comprehensive onboarding for new users",
                user_type=MockUserType.BEGINNER,
                settings={
                    "onboarding.help_preferences.show_tips": True,
                    "onboarding.help_preferences.tutorial_speed": "slow",
                    "onboarding.feature_discovery.discovery_pace": "slow",
                    "onboarding.recommendations.frequency": "high",
                    "ui.layout": "simplified"
                },
                features_enabled=[
                    "welcome_wizard",
                    "interactive_tutorials",
                    "contextual_help",
                    "smart_tips",
                    "feature_discovery",
                    "progress_tracking"
                ],
                ui_customizations={
                    "show_welcome_banner": True,
                    "highlight_important_features": True,
                    "simplified_menus": True,
                    "extra_spacing": True
                }
            ),
            MockOnboardingPreset(
                name="Quick Start",
                description="Minimal onboarding for experienced users",
                user_type=MockUserType.POWER_USER,
                settings={
                    "onboarding.help_preferences.show_tips": False,
                    "onboarding.help_preferences.tutorial_speed": "fast",
                    "onboarding.feature_discovery.discovery_pace": "fast",
                    "onboarding.recommendations.frequency": "low",
                    "ui.layout": "compact"
                },
                features_enabled=[
                    "quick_setup",
                    "keyboard_shortcuts",
                    "advanced_features"
                ],
                ui_customizations={
                    "show_welcome_banner": False,
                    "compact_interface": True,
                    "advanced_controls": True
                }
            ),
            MockOnboardingPreset(
                name="Developer Mode",
                description="Technical onboarding for developers",
                user_type=MockUserType.DEVELOPER,
                settings={
                    "onboarding.user_level": "advanced",
                    "onboarding.help_preferences.show_tips": False,
                    "onboarding.feature_discovery.feature_categories_enabled": ["advanced", "expert"],
                    "ui.theme": "dark",
                    "ui.layout": "developer",
                    "system.debug_mode": True
                },
                features_enabled=[
                    "api_documentation",
                    "debug_tools",
                    "advanced_configuration",
                    "scripting_support"
                ],
                ui_customizations={
                    "show_debug_info": True,
                    "technical_tooltips": True,
                    "code_highlighting": True
                }
            ),
            MockOnboardingPreset(
                name="Accessibility Focus",
                description="Optimized for accessibility needs",
                user_type=MockUserType.BEGINNER,
                settings={
                    "accessibility.high_contrast": True,
                    "accessibility.large_fonts": True,
                    "accessibility.screen_reader_support": True,
                    "accessibility.reduced_motion": True,
                    "onboarding.help_preferences.sound_enabled": True,
                    "onboarding.help_preferences.tutorial_speed": "slow"
                },
                features_enabled=[
                    "screen_reader_support",
                    "keyboard_navigation",
                    "high_contrast_mode",
                    "audio_cues",
                    "simplified_interface"
                ],
                ui_customizations={
                    "high_contrast": True,
                    "large_buttons": True,
                    "clear_focus_indicators": True,
                    "reduced_animations": True
                }
            ),
            MockOnboardingPreset(
                name="Research Workflow",
                description="Optimized for research and analysis",
                user_type=MockUserType.RESEARCHER,
                settings={
                    "onboarding.user_level": "intermediate",
                    "onboarding.recommendations.types": ["analysis", "data", "workflow"],
                    "workflow.auto_save_interval": 120,
                    "workflow.backup_frequency": "hourly",
                    "ui.layout": "research"
                },
                features_enabled=[
                    "data_analysis_tools",
                    "advanced_search",
                    "export_options",
                    "collaboration_features",
                    "version_control"
                ],
                ui_customizations={
                    "data_focused_layout": True,
                    "analysis_shortcuts": True,
                    "research_templates": True
                }
            )
        ]
    
    @staticmethod
    def get_ui_themes():
        return {
            "light": {
                "name": "Light Theme",
                "colors": {
                    "primary": "#0078d4",
                    "secondary": "#6c757d",
                    "background": "#ffffff",
                    "surface": "#f8f9fa",
                    "text": "#212529",
                    "accent": "#0066cc"
                },
                "fonts": {
                    "primary": "Segoe UI",
                    "monospace": "Consolas"
                }
            },
            "dark": {
                "name": "Dark Theme",
                "colors": {
                    "primary": "#0078d4",
                    "secondary": "#6c757d",
                    "background": "#1e1e1e",
                    "surface": "#2d2d30",
                    "text": "#ffffff",
                    "accent": "#4fc3f7"
                },
                "fonts": {
                    "primary": "Segoe UI",
                    "monospace": "Consolas"
                }
            },
            "high_contrast": {
                "name": "High Contrast",
                "colors": {
                    "primary": "#ffff00",
                    "secondary": "#ffffff",
                    "background": "#000000",
                    "surface": "#000000",
                    "text": "#ffffff",
                    "accent": "#00ff00"
                },
                "fonts": {
                    "primary": "Segoe UI",
                    "monospace": "Consolas"
                }
            }
        }
    
    @staticmethod
    def get_layout_presets():
        return {
            "standard": {
                "name": "Standard Layout",
                "sidebar_width": 250,
                "toolbar_height": 40,
                "status_bar": True,
                "panels": ["navigation", "properties", "output"]
            },
            "simplified": {
                "name": "Simplified Layout",
                "sidebar_width": 200,
                "toolbar_height": 50,
                "status_bar": True,
                "panels": ["navigation"],
                "large_buttons": True,
                "extra_spacing": True
            },
            "compact": {
                "name": "Compact Layout",
                "sidebar_width": 180,
                "toolbar_height": 30,
                "status_bar": False,
                "panels": ["navigation", "properties"],
                "dense_spacing": True
            },
            "developer": {
                "name": "Developer Layout",
                "sidebar_width": 300,
                "toolbar_height": 35,
                "status_bar": True,
                "panels": ["navigation", "properties", "output", "debug"],
                "show_debug_info": True
            }
        }
    
    @staticmethod
    def get_feature_categories():
        return {
            "basic": [
                "file_operations",
                "basic_navigation",
                "help_system",
                "settings",
                "user_profile"
            ],
            "intermediate": [
                "advanced_search",
                "batch_operations",
                "customization",
                "shortcuts",
                "workspace_management"
            ],
            "advanced": [
                "automation",
                "scripting",
                "api_access",
                "performance_tuning",
                "advanced_configuration"
            ],
            "expert": [
                "plugin_development",
                "system_integration",
                "debugging_tools",
                "performance_profiling",
                "custom_extensions"
            ]
        }


class TestConfigurationTemplates:
    """Test suite for configuration templates"""
    
    def setup_method(self):
        """Setup test environment"""
        self.templates = MockConfigurationTemplates()
    
    def test_default_global_config(self):
        """Test default global configuration"""
        config = self.templates.get_default_global_config()
        
        # Verify structure
        assert "system" in config
        assert "performance" in config
        assert "security" in config
        assert "accessibility" in config
        assert "onboarding" in config
        
        # Verify system settings
        assert config["system"]["version"] == "1.0.0"
        assert config["system"]["locale"] == "en_US"
        assert config["system"]["debug_mode"] is False
        
        # Verify performance settings
        assert config["performance"]["cache_size_mb"] == 100
        assert config["performance"]["lazy_loading"] is True
        
        # Verify security settings
        assert config["security"]["auto_lock_timeout"] == 30
        assert config["security"]["secure_storage"] is True
    
    def test_user_type_templates(self):
        """Test user type configuration templates"""
        user_types = [
            MockUserType.BEGINNER,
            MockUserType.POWER_USER,
            MockUserType.DEVELOPER,
            MockUserType.ADMINISTRATOR,
            MockUserType.RESEARCHER,
            MockUserType.EDUCATOR
        ]
        
        for user_type in user_types:
            config = self.templates.get_user_config_template(user_type)
            
            # Verify basic structure
            assert "user" in config
            assert "onboarding" in config
            assert "ui" in config
            assert "workflow" in config
            assert "privacy" in config
            
            # Verify user type is set correctly
            assert config["user"]["type"] == user_type
    
    def test_beginner_template_customizations(self):
        """Test beginner user template customizations"""
        config = self.templates.get_user_config_template(MockUserType.BEGINNER)
        
        # Verify beginner-specific settings
        assert config["onboarding"]["help_preferences"]["tutorial_speed"] == "slow"
        assert config["onboarding"]["feature_discovery"]["discovery_pace"] == "slow"
        assert config["onboarding"]["recommendations"]["frequency"] == "high"
        assert config["ui"]["layout"] == "simplified"
    
    def test_developer_template_customizations(self):
        """Test developer user template customizations"""
        config = self.templates.get_user_config_template(MockUserType.DEVELOPER)
        
        # Verify developer-specific settings
        assert config["onboarding"]["user_level"] == "advanced"
        assert config["onboarding"]["help_preferences"]["show_tips"] is False
        assert config["onboarding"]["feature_discovery"]["discovery_pace"] == "fast"
        assert "advanced" in config["onboarding"]["feature_discovery"]["feature_categories_enabled"]
        assert "expert" in config["onboarding"]["feature_discovery"]["feature_categories_enabled"]
        assert config["ui"]["theme"] == "dark"
        assert config["ui"]["layout"] == "developer"
        assert config["system"]["debug_mode"] is True
    
    def test_researcher_template_customizations(self):
        """Test researcher user template customizations"""
        config = self.templates.get_user_config_template(MockUserType.RESEARCHER)
        
        # Verify researcher-specific settings
        assert config["onboarding"]["user_level"] == "intermediate"
        assert "analysis" in config["onboarding"]["recommendations"]["types"]
        assert "data" in config["onboarding"]["recommendations"]["types"]
        assert config["workflow"]["auto_save_interval"] == 120
        assert config["workflow"]["backup_frequency"] == "hourly"
        assert config["ui"]["layout"] == "research"
    
    def test_onboarding_presets(self):
        """Test onboarding presets"""
        presets = self.templates.get_onboarding_presets()
        
        # Verify we have expected presets
        assert len(presets) == 5
        
        preset_names = [preset.name for preset in presets]
        expected_names = [
            "First-Time User",
            "Quick Start",
            "Developer Mode",
            "Accessibility Focus",
            "Research Workflow"
        ]
        
        for expected_name in expected_names:
            assert expected_name in preset_names
    
    def test_first_time_user_preset(self):
        """Test first-time user preset"""
        presets = self.templates.get_onboarding_presets()
        first_time_preset = next(p for p in presets if p.name == "First-Time User")
        
        # Verify preset properties
        assert first_time_preset.user_type == MockUserType.BEGINNER
        assert first_time_preset.description == "Comprehensive onboarding for new users"
        
        # Verify settings
        assert first_time_preset.settings["onboarding.help_preferences.show_tips"] is True
        assert first_time_preset.settings["onboarding.help_preferences.tutorial_speed"] == "slow"
        assert first_time_preset.settings["ui.layout"] == "simplified"
        
        # Verify features
        assert "welcome_wizard" in first_time_preset.features_enabled
        assert "interactive_tutorials" in first_time_preset.features_enabled
        assert "progress_tracking" in first_time_preset.features_enabled
        
        # Verify UI customizations
        assert first_time_preset.ui_customizations["show_welcome_banner"] is True
        assert first_time_preset.ui_customizations["simplified_menus"] is True
    
    def test_developer_mode_preset(self):
        """Test developer mode preset"""
        presets = self.templates.get_onboarding_presets()
        dev_preset = next(p for p in presets if p.name == "Developer Mode")
        
        # Verify preset properties
        assert dev_preset.user_type == MockUserType.DEVELOPER
        assert dev_preset.description == "Technical onboarding for developers"
        
        # Verify settings
        assert dev_preset.settings["onboarding.user_level"] == "advanced"
        assert dev_preset.settings["ui.theme"] == "dark"
        assert dev_preset.settings["system.debug_mode"] is True
        
        # Verify features
        assert "api_documentation" in dev_preset.features_enabled
        assert "debug_tools" in dev_preset.features_enabled
        assert "scripting_support" in dev_preset.features_enabled
        
        # Verify UI customizations
        assert dev_preset.ui_customizations["show_debug_info"] is True
        assert dev_preset.ui_customizations["technical_tooltips"] is True
    
    def test_accessibility_preset(self):
        """Test accessibility-focused preset"""
        presets = self.templates.get_onboarding_presets()
        a11y_preset = next(p for p in presets if p.name == "Accessibility Focus")
        
        # Verify accessibility settings
        assert a11y_preset.settings["accessibility.high_contrast"] is True
        assert a11y_preset.settings["accessibility.large_fonts"] is True
        assert a11y_preset.settings["accessibility.screen_reader_support"] is True
        assert a11y_preset.settings["accessibility.reduced_motion"] is True
        
        # Verify features
        assert "screen_reader_support" in a11y_preset.features_enabled
        assert "keyboard_navigation" in a11y_preset.features_enabled
        assert "high_contrast_mode" in a11y_preset.features_enabled
        
        # Verify UI customizations
        assert a11y_preset.ui_customizations["high_contrast"] is True
        assert a11y_preset.ui_customizations["large_buttons"] is True
        assert a11y_preset.ui_customizations["reduced_animations"] is True
    
    def test_ui_themes(self):
        """Test UI themes"""
        themes = self.templates.get_ui_themes()
        
        # Verify we have expected themes
        expected_themes = ["light", "dark", "high_contrast"]
        for theme_name in expected_themes:
            assert theme_name in themes
        
        # Test light theme
        light_theme = themes["light"]
        assert light_theme["name"] == "Light Theme"
        assert light_theme["colors"]["background"] == "#ffffff"
        assert light_theme["colors"]["text"] == "#212529"
        
        # Test dark theme
        dark_theme = themes["dark"]
        assert dark_theme["name"] == "Dark Theme"
        assert dark_theme["colors"]["background"] == "#1e1e1e"
        assert dark_theme["colors"]["text"] == "#ffffff"
        
        # Test high contrast theme
        hc_theme = themes["high_contrast"]
        assert hc_theme["name"] == "High Contrast"
        assert hc_theme["colors"]["background"] == "#000000"
        assert hc_theme["colors"]["text"] == "#ffffff"
    
    def test_layout_presets(self):
        """Test layout presets"""
        layouts = self.templates.get_layout_presets()
        
        # Verify we have expected layouts
        expected_layouts = ["standard", "simplified", "compact", "developer"]
        for layout_name in expected_layouts:
            assert layout_name in layouts
        
        # Test standard layout
        standard = layouts["standard"]
        assert standard["name"] == "Standard Layout"
        assert standard["sidebar_width"] == 250
        assert standard["status_bar"] is True
        assert "navigation" in standard["panels"]
        
        # Test simplified layout
        simplified = layouts["simplified"]
        assert simplified["name"] == "Simplified Layout"
        assert simplified["large_buttons"] is True
        assert simplified["extra_spacing"] is True
        
        # Test compact layout
        compact = layouts["compact"]
        assert compact["name"] == "Compact Layout"
        assert compact["sidebar_width"] == 180
        assert compact["status_bar"] is False
        assert compact["dense_spacing"] is True
        
        # Test developer layout
        developer = layouts["developer"]
        assert developer["name"] == "Developer Layout"
        assert developer["show_debug_info"] is True
        assert "debug" in developer["panels"]
    
    def test_feature_categories(self):
        """Test feature categories"""
        categories = self.templates.get_feature_categories()
        
        # Verify we have expected categories
        expected_categories = ["basic", "intermediate", "advanced", "expert"]
        for category in expected_categories:
            assert category in categories
            assert isinstance(categories[category], list)
            assert len(categories[category]) > 0
        
        # Test basic category
        basic_features = categories["basic"]
        assert "file_operations" in basic_features
        assert "basic_navigation" in basic_features
        assert "help_system" in basic_features
        
        # Test advanced category
        advanced_features = categories["advanced"]
        assert "automation" in advanced_features
        assert "scripting" in advanced_features
        assert "api_access" in advanced_features
        
        # Test expert category
        expert_features = categories["expert"]
        assert "plugin_development" in expert_features
        assert "system_integration" in expert_features
    
    def test_template_consistency(self):
        """Test consistency across templates"""
        user_types = [
            MockUserType.BEGINNER,
            MockUserType.POWER_USER,
            MockUserType.DEVELOPER,
            MockUserType.ADMINISTRATOR,
            MockUserType.RESEARCHER,
            MockUserType.EDUCATOR
        ]
        
        # Test that all templates have consistent structure
        for user_type in user_types:
            config = self.templates.get_user_config_template(user_type)
            
            # Verify all templates have required sections
            required_sections = ["user", "onboarding", "ui", "workflow", "privacy"]
            for section in required_sections:
                assert section in config, f"Missing section {section} in {user_type} template"
            
            # Verify onboarding subsections
            onboarding_subsections = ["help_preferences", "feature_discovery", "recommendations"]
            for subsection in onboarding_subsections:
                assert subsection in config["onboarding"], f"Missing onboarding.{subsection} in {user_type} template"
    
    def test_preset_feature_consistency(self):
        """Test that preset features are consistent"""
        presets = self.templates.get_onboarding_presets()
        
        for preset in presets:
            # Verify all presets have required properties
            assert hasattr(preset, 'name')
            assert hasattr(preset, 'description')
            assert hasattr(preset, 'user_type')
            assert hasattr(preset, 'settings')
            assert hasattr(preset, 'features_enabled')
            assert hasattr(preset, 'ui_customizations')
            
            # Verify properties are not empty
            assert preset.name
            assert preset.description
            assert preset.user_type
            assert isinstance(preset.settings, dict)
            assert isinstance(preset.features_enabled, list)
            assert isinstance(preset.ui_customizations, dict)


if __name__ == "__main__":
    # Run tests
    test_suite = TestConfigurationTemplates()
    
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
        print("🎉 All configuration template tests passed!")
    else:
        print(f"⚠️ {failed} tests failed")
