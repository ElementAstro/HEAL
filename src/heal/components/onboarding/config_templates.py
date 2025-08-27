"""
Configuration Templates and Presets for HEAL Onboarding System

Provides pre-defined configuration templates, user profiles, and customization presets
for different user types and use cases.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .config_system import ConfigurationProfile, ConfigValidationRule, ConfigSchema


class UserType(Enum):
    """User type classifications"""
    BEGINNER = "beginner"
    POWER_USER = "power_user"
    DEVELOPER = "developer"
    ADMINISTRATOR = "administrator"
    RESEARCHER = "researcher"
    EDUCATOR = "educator"


class ConfigTemplate(Enum):
    """Configuration template types"""
    MINIMAL = "minimal"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"


@dataclass
class OnboardingPreset:
    """Onboarding configuration preset"""
    name: str
    description: str
    user_type: UserType
    settings: Dict[str, Any]
    features_enabled: List[str]
    ui_customizations: Dict[str, Any]


class ConfigurationTemplates:
    """Configuration templates and presets manager"""
    
    @staticmethod
    def get_default_global_config() -> Dict[str, Any]:
        """Get default global configuration"""
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
    def get_user_config_template(user_type: UserType) -> Dict[str, Any]:
        """Get user configuration template based on user type"""
        base_config = {
            "user": {
                "type": user_type.value,
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
        if user_type == UserType.BEGINNER:
            base_config["onboarding"]["help_preferences"]["tutorial_speed"] = "slow"
            base_config["onboarding"]["feature_discovery"]["discovery_pace"] = "slow"
            base_config["onboarding"]["recommendations"]["frequency"] = "high"
            base_config["ui"]["layout"] = "simplified"
            
        elif user_type == UserType.POWER_USER:
            base_config["onboarding"]["user_level"] = "intermediate"
            base_config["onboarding"]["help_preferences"]["tutorial_speed"] = "fast"
            base_config["onboarding"]["feature_discovery"]["show_advanced_features"] = True
            base_config["onboarding"]["feature_discovery"]["feature_categories_enabled"].append("advanced")
            base_config["ui"]["layout"] = "compact"
            
        elif user_type == UserType.DEVELOPER:
            base_config["onboarding"]["user_level"] = "advanced"
            base_config["onboarding"]["help_preferences"]["show_tips"] = False
            base_config["onboarding"]["feature_discovery"]["discovery_pace"] = "fast"
            base_config["onboarding"]["feature_discovery"]["feature_categories_enabled"].extend(["advanced", "expert"])
            base_config["ui"]["theme"] = "dark"
            base_config["ui"]["layout"] = "developer"
            base_config["system"]["debug_mode"] = True
            
        elif user_type == UserType.ADMINISTRATOR:
            base_config["onboarding"]["user_level"] = "advanced"
            base_config["onboarding"]["recommendations"]["types"].append("security")
            base_config["onboarding"]["feature_discovery"]["feature_categories_enabled"].extend(["advanced", "admin"])
            base_config["security"]["audit_logging"] = True
            base_config["ui"]["layout"] = "admin"
            
        elif user_type == UserType.RESEARCHER:
            base_config["onboarding"]["user_level"] = "intermediate"
            base_config["onboarding"]["recommendations"]["types"].extend(["analysis", "data"])
            base_config["workflow"]["auto_save_interval"] = 120
            base_config["workflow"]["backup_frequency"] = "hourly"
            base_config["ui"]["layout"] = "research"
            
        elif user_type == UserType.EDUCATOR:
            base_config["onboarding"]["help_preferences"]["tutorial_speed"] = "normal"
            base_config["onboarding"]["recommendations"]["types"].append("teaching")
            base_config["ui"]["layout"] = "presentation"
            base_config["accessibility"]["large_fonts"] = True
        
        return base_config
    
    @staticmethod
    def get_onboarding_presets() -> List[OnboardingPreset]:
        """Get predefined onboarding presets"""
        return [
            OnboardingPreset(
                name="First-Time User",
                description="Comprehensive onboarding for new users",
                user_type=UserType.BEGINNER,
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
            OnboardingPreset(
                name="Quick Start",
                description="Minimal onboarding for experienced users",
                user_type=UserType.POWER_USER,
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
            OnboardingPreset(
                name="Developer Mode",
                description="Technical onboarding for developers",
                user_type=UserType.DEVELOPER,
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
            OnboardingPreset(
                name="Accessibility Focus",
                description="Optimized for accessibility needs",
                user_type=UserType.BEGINNER,
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
            OnboardingPreset(
                name="Research Workflow",
                description="Optimized for research and analysis",
                user_type=UserType.RESEARCHER,
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
    def get_ui_themes() -> Dict[str, Dict[str, Any]]:
        """Get predefined UI themes"""
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
            },
            "blue": {
                "name": "Blue Theme",
                "colors": {
                    "primary": "#2196f3",
                    "secondary": "#03dac6",
                    "background": "#f5f5f5",
                    "surface": "#ffffff",
                    "text": "#212121",
                    "accent": "#ff4081"
                },
                "fonts": {
                    "primary": "Roboto",
                    "monospace": "Roboto Mono"
                }
            }
        }
    
    @staticmethod
    def get_layout_presets() -> Dict[str, Dict[str, Any]]:
        """Get predefined layout presets"""
        return {
            "standard": {
                "name": "Standard Layout",
                "sidebar_width": 250,
                "toolbar_height": 40,
                "status_bar": True,
                "panels": ["navigation", "properties", "output"],
                "panel_positions": {
                    "navigation": "left",
                    "properties": "right",
                    "output": "bottom"
                }
            },
            "simplified": {
                "name": "Simplified Layout",
                "sidebar_width": 200,
                "toolbar_height": 50,
                "status_bar": True,
                "panels": ["navigation"],
                "panel_positions": {
                    "navigation": "left"
                },
                "large_buttons": True,
                "extra_spacing": True
            },
            "compact": {
                "name": "Compact Layout",
                "sidebar_width": 180,
                "toolbar_height": 30,
                "status_bar": False,
                "panels": ["navigation", "properties"],
                "panel_positions": {
                    "navigation": "left",
                    "properties": "right"
                },
                "dense_spacing": True
            },
            "developer": {
                "name": "Developer Layout",
                "sidebar_width": 300,
                "toolbar_height": 35,
                "status_bar": True,
                "panels": ["navigation", "properties", "output", "debug"],
                "panel_positions": {
                    "navigation": "left",
                    "properties": "right",
                    "output": "bottom",
                    "debug": "bottom"
                },
                "show_debug_info": True
            },
            "research": {
                "name": "Research Layout",
                "sidebar_width": 280,
                "toolbar_height": 40,
                "status_bar": True,
                "panels": ["navigation", "analysis", "data"],
                "panel_positions": {
                    "navigation": "left",
                    "analysis": "right",
                    "data": "bottom"
                },
                "data_focused": True
            }
        }
    
    @staticmethod
    def get_feature_categories() -> Dict[str, List[str]]:
        """Get feature categories for progressive disclosure"""
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
            ],
            "admin": [
                "user_management",
                "security_settings",
                "audit_logs",
                "system_monitoring",
                "backup_management"
            ]
        }
    
    @staticmethod
    def create_custom_profile(name: str, user_type: UserType, 
                            customizations: Dict[str, Any]) -> ConfigurationProfile:
        """Create a custom configuration profile"""
        base_settings = ConfigurationTemplates.get_user_config_template(user_type)
        
        # Apply customizations
        for key, value in customizations.items():
            keys = key.split('.')
            current = base_settings
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
        
        return ConfigurationProfile(
            profile_id=f"custom_{name.lower().replace(' ', '_')}",
            name=name,
            description=f"Custom profile for {user_type.value}",
            created_at=datetime.now(),
            last_modified=datetime.now(),
            settings=base_settings
        )
