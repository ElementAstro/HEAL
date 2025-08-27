"""
Advanced Configuration Integration for HEAL Onboarding System

Integrates the advanced configuration system with the existing onboarding components,
providing seamless configuration management across all onboarding features.
"""

from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import json
from datetime import datetime

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, Signal

from .config_system import AdvancedConfigurationManager, ConfigScope, ConfigurationProfile
from .config_templates import ConfigurationTemplates, UserType, OnboardingPreset
from .config_plugins import ConfigurationPluginManager, create_default_plugin_manager
from .config_ui_manager import ConfigurationUIManager
from .user_state_tracker import UserStateTracker, UserLevel, OnboardingStep
from src.heal.common.logging_config import get_logger

logger = get_logger(__name__)


class ConfigurationIntegrator(QObject):
    """Integrates advanced configuration with onboarding system"""
    
    # Signals for configuration changes
    configuration_changed = Signal(str, object)  # key, new_value
    profile_changed = Signal(str)  # profile_id
    theme_changed = Signal(str)  # theme_name
    user_level_changed = Signal(str)  # user_level
    
    def __init__(self, base_path: Optional[Path] = None):
        super().__init__()
        
        # Initialize configuration system
        self.config_manager = AdvancedConfigurationManager(base_path)
        self.plugin_manager = create_default_plugin_manager(self.config_manager)
        self.ui_manager = ConfigurationUIManager(self.config_manager)
        
        # Integration state
        self.user_tracker: Optional[UserStateTracker] = None
        self.onboarding_components: Dict[str, Any] = {}
        
        # Setup configuration change handling
        self.config_manager.add_change_listener(self._on_configuration_changed)
        
        # Initialize with default configuration
        self._initialize_default_configuration()
        
        logger.info("Configuration integrator initialized")
    
    def _initialize_default_configuration(self):
        """Initialize with default configuration values"""
        # Load global defaults
        global_defaults = ConfigurationTemplates.get_default_global_config()
        for key, value in self._flatten_dict(global_defaults).items():
            if self.config_manager.get(key) is None:
                self.config_manager.set(key, value, scope=ConfigScope.GLOBAL, persist=True)
        
        # Check if user configuration exists, if not create default
        if not self.config_manager.get("onboarding.is_first_time"):
            user_defaults = ConfigurationTemplates.get_user_config_template(UserType.BEGINNER)
            for key, value in self._flatten_dict(user_defaults).items():
                if self.config_manager.get(key) is None:
                    self.config_manager.set(key, value, scope=ConfigScope.USER, persist=True)
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def integrate_user_tracker(self, user_tracker: UserStateTracker):
        """Integrate with user state tracker"""
        self.user_tracker = user_tracker
        
        # Sync configuration with user tracker state
        self._sync_user_tracker_config()
        
        # Setup bidirectional sync
        self.config_manager.add_change_listener(self._sync_config_to_user_tracker)
        
        logger.info("User tracker integrated with configuration system")
    
    def _sync_user_tracker_config(self):
        """Sync configuration with user tracker state"""
        if not self.user_tracker:
            return
        
        # Sync user level
        tracker_level = self.user_tracker.get_user_level()
        config_level = self.config_manager.get("onboarding.user_level")
        
        if tracker_level.value != config_level:
            self.config_manager.set("onboarding.user_level", tracker_level.value)
        
        # Sync first-time status
        is_first_time = self.user_tracker.is_first_time_user()
        self.config_manager.set("onboarding.is_first_time", is_first_time)
        
        # Sync completed steps
        completed_steps = [step.value for step in self.user_tracker.get_completed_steps()]
        self.config_manager.set("onboarding.completed_steps", completed_steps)
        
        # Sync help preferences
        help_prefs = self.user_tracker.get_help_preferences()
        for key, value in help_prefs.items():
            self.config_manager.set(f"onboarding.help_preferences.{key}", value)
    
    def _sync_config_to_user_tracker(self, key: str, old_value: Any, new_value: Any):
        """Sync configuration changes to user tracker"""
        if not self.user_tracker:
            return
        
        try:
            if key == "onboarding.user_level":
                # Update user level in tracker
                user_level = UserLevel(new_value)
                self.user_tracker.set_user_level(user_level)
                self.user_level_changed.emit(new_value)
                
            elif key.startswith("onboarding.help_preferences."):
                # Update help preferences
                pref_key = key.split(".")[-1]
                current_prefs = self.user_tracker.get_help_preferences()
                current_prefs[pref_key] = new_value
                self.user_tracker.update_help_preferences(current_prefs)
                
            elif key == "ui.theme":
                # Emit theme change signal
                self.theme_changed.emit(new_value)
                
        except Exception as e:
            logger.error(f"Failed to sync config change to user tracker: {e}")
    
    def register_onboarding_component(self, name: str, component: Any):
        """Register an onboarding component for configuration integration"""
        self.onboarding_components[name] = component
        
        # Apply current configuration to component
        self._apply_configuration_to_component(name, component)
        
        logger.info(f"Registered onboarding component: {name}")
    
    def _apply_configuration_to_component(self, name: str, component: Any):
        """Apply current configuration to a component"""
        try:
            # Apply theme if component supports it
            if hasattr(component, 'set_theme'):
                theme = self.config_manager.get("ui.theme", "light")
                component.set_theme(theme)
            
            # Apply animation settings
            if hasattr(component, 'set_animation_speed'):
                speed = self.config_manager.get("ui.animation_speed", 1.0)
                component.set_animation_speed(speed)
            
            # Apply help preferences for onboarding components
            if hasattr(component, 'update_help_preferences'):
                help_prefs = {
                    "show_tips": self.config_manager.get("onboarding.help_preferences.show_tips", True),
                    "show_tooltips": self.config_manager.get("onboarding.help_preferences.show_tooltips", True),
                    "tutorial_speed": self.config_manager.get("onboarding.help_preferences.tutorial_speed", "normal")
                }
                component.update_help_preferences(help_prefs)
            
        except Exception as e:
            logger.error(f"Failed to apply configuration to component {name}: {e}")
    
    def _on_configuration_changed(self, key: str, old_value: Any, new_value: Any):
        """Handle configuration changes"""
        # Emit general configuration change signal
        self.configuration_changed.emit(key, new_value)
        
        # Apply changes to registered components
        for name, component in self.onboarding_components.items():
            self._apply_configuration_to_component(name, component)
        
        # Handle specific configuration changes
        if key == "onboarding.user_level":
            self._handle_user_level_change(new_value)
        elif key.startswith("ui."):
            self._handle_ui_change(key, new_value)
        elif key.startswith("onboarding."):
            self._handle_onboarding_change(key, new_value)
    
    def _handle_user_level_change(self, new_level: str):
        """Handle user level changes"""
        logger.info(f"User level changed to: {new_level}")
        
        # Update feature visibility based on user level
        if new_level == "beginner":
            self.config_manager.set("onboarding.feature_discovery.show_advanced_features", False)
            self.config_manager.set("onboarding.help_preferences.tutorial_speed", "slow")
        elif new_level == "advanced":
            self.config_manager.set("onboarding.feature_discovery.show_advanced_features", True)
            self.config_manager.set("onboarding.help_preferences.tutorial_speed", "fast")
    
    def _handle_ui_change(self, key: str, new_value: Any):
        """Handle UI configuration changes"""
        if key == "ui.theme":
            logger.info(f"Theme changed to: {new_value}")
            # Theme change is handled by signal emission
        elif key == "ui.layout":
            logger.info(f"Layout changed to: {new_value}")
            # Apply layout changes to components
        elif key == "ui.animation_speed":
            logger.info(f"Animation speed changed to: {new_value}")
    
    def _handle_onboarding_change(self, key: str, new_value: Any):
        """Handle onboarding configuration changes"""
        logger.info(f"Onboarding setting changed: {key} = {new_value}")
    
    def apply_preset(self, preset: OnboardingPreset) -> bool:
        """Apply an onboarding preset"""
        try:
            # Apply preset settings
            for key, value in preset.settings.items():
                self.config_manager.set(key, value)
            
            # Apply UI customizations
            for key, value in preset.ui_customizations.items():
                ui_key = f"ui.{key}"
                self.config_manager.set(ui_key, value)
            
            logger.info(f"Applied onboarding preset: {preset.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply preset {preset.name}: {e}")
            return False
    
    def create_user_profile_from_template(self, user_type: UserType, 
                                        profile_name: Optional[str] = None) -> str:
        """Create a user profile from template"""
        if not profile_name:
            profile_name = f"{user_type.value.title()} Profile"
        
        # Get template configuration
        template_config = ConfigurationTemplates.get_user_config_template(user_type)
        
        # Create profile
        profile_id = self.config_manager.create_profile(
            profile_name, 
            f"Profile for {user_type.value} users"
        )
        
        # Apply template settings to profile
        profile = self.config_manager.get_profile(profile_id)
        if profile:
            profile.settings = template_config
            profile.last_modified = datetime.now()
        
        logger.info(f"Created user profile from template: {profile_name}")
        return profile_id
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get comprehensive configuration summary"""
        return {
            "system_info": self.config_manager.get_configuration_info(),
            "current_settings": {
                "user_level": self.config_manager.get("onboarding.user_level"),
                "theme": self.config_manager.get("ui.theme"),
                "layout": self.config_manager.get("ui.layout"),
                "help_enabled": self.config_manager.get("onboarding.help_preferences.show_tips"),
                "tutorial_speed": self.config_manager.get("onboarding.help_preferences.tutorial_speed")
            },
            "profiles": {
                "active": self.config_manager.active_profile_id,
                "total": len(self.config_manager.profiles),
                "available": [
                    {"id": p.profile_id, "name": p.name} 
                    for p in self.config_manager.list_profiles()
                ]
            },
            "plugins": self.plugin_manager.list_plugins(),
            "components": list(self.onboarding_components.keys())
        }
    
    def show_configuration_dialog(self, parent: Optional[QWidget] = None):
        """Show configuration dialog"""
        return self.ui_manager.show_configuration_dialog(parent)
    
    def export_user_configuration(self, file_path: str) -> bool:
        """Export user configuration to file"""
        return self.config_manager.export_configuration(file_path, include_profiles=True)
    
    def import_user_configuration(self, file_path: str, merge: bool = True) -> bool:
        """Import user configuration from file"""
        return self.config_manager.import_configuration(file_path, merge=merge)
    
    def reset_to_defaults(self, scope: ConfigScope = ConfigScope.USER):
        """Reset configuration to defaults"""
        self.config_manager.reset_to_defaults(scope)
        
        # Re-initialize defaults if needed
        if scope == ConfigScope.USER:
            self._initialize_default_configuration()
    
    def get_available_presets(self) -> List[OnboardingPreset]:
        """Get available onboarding presets"""
        return ConfigurationTemplates.get_onboarding_presets()
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """Validate all configuration"""
        return self.config_manager.validate_all()
    
    def shutdown(self):
        """Shutdown configuration system"""
        try:
            # Shutdown plugin manager
            self.plugin_manager.shutdown_all_plugins()
            
            # Clear component registrations
            self.onboarding_components.clear()
            
            logger.info("Configuration integrator shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during configuration shutdown: {e}")


# Global configuration integrator instance
_config_integrator: Optional[ConfigurationIntegrator] = None


def get_configuration_integrator(base_path: Optional[Path] = None) -> ConfigurationIntegrator:
    """Get global configuration integrator instance"""
    global _config_integrator
    
    if _config_integrator is None:
        _config_integrator = ConfigurationIntegrator(base_path)
    
    return _config_integrator


def initialize_configuration_system(base_path: Optional[Path] = None) -> ConfigurationIntegrator:
    """Initialize the configuration system"""
    integrator = get_configuration_integrator(base_path)
    logger.info("Configuration system initialized")
    return integrator


def shutdown_configuration_system():
    """Shutdown the configuration system"""
    global _config_integrator
    
    if _config_integrator:
        _config_integrator.shutdown()
        _config_integrator = None
    
    logger.info("Configuration system shutdown")


# Convenience functions for common operations
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value"""
    return get_configuration_integrator().config_manager.get(key, default)


def set_config(key: str, value: Any, scope: ConfigScope = ConfigScope.USER) -> bool:
    """Set configuration value"""
    return get_configuration_integrator().config_manager.set(key, value, scope=scope)


def apply_onboarding_preset(preset_name: str) -> bool:
    """Apply onboarding preset by name"""
    integrator = get_configuration_integrator()
    presets = integrator.get_available_presets()
    
    for preset in presets:
        if preset.name == preset_name:
            return integrator.apply_preset(preset)
    
    logger.warning(f"Preset not found: {preset_name}")
    return False
