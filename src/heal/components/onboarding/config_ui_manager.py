"""
Configuration UI Manager for HEAL Onboarding System

Provides runtime configuration management with UI integration,
real-time updates, and user-friendly configuration interfaces.
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                               QGroupBox, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
                               QCheckBox, QComboBox, QSlider, QPushButton, QTextEdit,
                               QScrollArea, QSplitter, QTreeWidget, QTreeWidgetItem,
                               QDialog, QDialogButtonBox, QMessageBox, QProgressBar)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, pyqtSignal
from PySide6.QtGui import QFont, QIcon, QPalette

from .config_system import AdvancedConfigurationManager, ConfigScope, ConfigurationProfile
from .config_templates import ConfigurationTemplates, UserType, OnboardingPreset
from src.heal.common.logging_config import get_logger

logger = get_logger(__name__)


class ConfigWidgetType(Enum):
    """Configuration widget types"""
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    SLIDER = "slider"
    COLOR = "color"
    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    MULTI_CHOICE = "multi_choice"
    JSON_EDITOR = "json_editor"


@dataclass
class ConfigUIDefinition:
    """Configuration UI element definition"""
    key: str
    label: str
    widget_type: ConfigWidgetType
    description: str = ""
    default_value: Any = None
    options: List[Any] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    validation_func: Optional[Callable[[Any], bool]] = None
    group: str = "General"
    advanced: bool = False
    requires_restart: bool = False


class ConfigurationWidget(QWidget):
    """Base configuration widget"""
    
    value_changed = Signal(str, object)  # key, new_value
    
    def __init__(self, definition: ConfigUIDefinition, initial_value: Any = None):
        super().__init__()
        self.definition = definition
        self.current_value = initial_value or definition.default_value
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        
        # Label
        label = QLabel(self.definition.label)
        if self.definition.advanced:
            font = label.font()
            font.setItalic(True)
            label.setFont(font)
        layout.addWidget(label)
        
        # Description
        if self.definition.description:
            desc_label = QLabel(self.definition.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            layout.addWidget(desc_label)
        
        # Control widget
        self.control_widget = self._create_control_widget()
        layout.addWidget(self.control_widget)
        
        # Restart required indicator
        if self.definition.requires_restart:
            restart_label = QLabel("⚠ Requires restart")
            restart_label.setStyleSheet("color: orange; font-size: 9px;")
            layout.addWidget(restart_label)
    
    def _create_control_widget(self) -> QWidget:
        """Create the control widget based on type"""
        if self.definition.widget_type == ConfigWidgetType.TEXT:
            widget = QLineEdit()
            widget.setText(str(self.current_value or ""))
            widget.textChanged.connect(lambda text: self._emit_change(text))
            return widget
            
        elif self.definition.widget_type == ConfigWidgetType.NUMBER:
            if isinstance(self.definition.default_value, float):
                widget = QDoubleSpinBox()
                widget.setDecimals(2)
            else:
                widget = QSpinBox()
            
            if self.definition.min_value is not None:
                widget.setMinimum(self.definition.min_value)
            if self.definition.max_value is not None:
                widget.setMaximum(self.definition.max_value)
            if self.definition.step is not None:
                widget.setSingleStep(self.definition.step)
            
            widget.setValue(self.current_value or 0)
            widget.valueChanged.connect(lambda value: self._emit_change(value))
            return widget
            
        elif self.definition.widget_type == ConfigWidgetType.BOOLEAN:
            widget = QCheckBox()
            widget.setChecked(bool(self.current_value))
            widget.toggled.connect(lambda checked: self._emit_change(checked))
            return widget
            
        elif self.definition.widget_type == ConfigWidgetType.CHOICE:
            widget = QComboBox()
            if self.definition.options:
                for option in self.definition.options:
                    widget.addItem(str(option), option)
            
            # Set current value
            if self.current_value is not None:
                index = widget.findData(self.current_value)
                if index >= 0:
                    widget.setCurrentIndex(index)
            
            widget.currentDataChanged.connect(lambda data: self._emit_change(data))
            return widget
            
        elif self.definition.widget_type == ConfigWidgetType.SLIDER:
            widget = QSlider(Qt.Horizontal)
            if self.definition.min_value is not None:
                widget.setMinimum(int(self.definition.min_value))
            if self.definition.max_value is not None:
                widget.setMaximum(int(self.definition.max_value))
            
            widget.setValue(int(self.current_value or 0))
            widget.valueChanged.connect(lambda value: self._emit_change(value))
            return widget
            
        elif self.definition.widget_type == ConfigWidgetType.JSON_EDITOR:
            widget = QTextEdit()
            widget.setMaximumHeight(150)
            if self.current_value:
                widget.setPlainText(json.dumps(self.current_value, indent=2))
            widget.textChanged.connect(self._on_json_changed)
            return widget
        
        # Default to text widget
        widget = QLineEdit()
        widget.setText(str(self.current_value or ""))
        widget.textChanged.connect(lambda text: self._emit_change(text))
        return widget
    
    def _on_json_changed(self):
        """Handle JSON text changes"""
        try:
            text = self.control_widget.toPlainText()
            if text.strip():
                value = json.loads(text)
                self._emit_change(value)
        except json.JSONDecodeError:
            pass  # Invalid JSON, don't emit change
    
    def _emit_change(self, value):
        """Emit value change signal"""
        if self.definition.validation_func and not self.definition.validation_func(value):
            return
        
        self.current_value = value
        self.value_changed.emit(self.definition.key, value)
    
    def set_value(self, value):
        """Set widget value programmatically"""
        self.current_value = value
        
        if self.definition.widget_type == ConfigWidgetType.TEXT:
            self.control_widget.setText(str(value or ""))
        elif self.definition.widget_type == ConfigWidgetType.NUMBER:
            self.control_widget.setValue(value or 0)
        elif self.definition.widget_type == ConfigWidgetType.BOOLEAN:
            self.control_widget.setChecked(bool(value))
        elif self.definition.widget_type == ConfigWidgetType.CHOICE:
            index = self.control_widget.findData(value)
            if index >= 0:
                self.control_widget.setCurrentIndex(index)
        elif self.definition.widget_type == ConfigWidgetType.SLIDER:
            self.control_widget.setValue(int(value or 0))
        elif self.definition.widget_type == ConfigWidgetType.JSON_EDITOR:
            if value:
                self.control_widget.setPlainText(json.dumps(value, indent=2))


class ConfigurationDialog(QDialog):
    """Configuration dialog with tabbed interface"""
    
    def __init__(self, config_manager: AdvancedConfigurationManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config_widgets: Dict[str, ConfigurationWidget] = {}
        self.pending_changes: Dict[str, Any] = {}
        
        self.setWindowTitle("Configuration Settings")
        self.setMinimumSize(800, 600)
        self._setup_ui()
        self._load_current_values()
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create configuration tabs
        self._create_onboarding_tab()
        self._create_ui_tab()
        self._create_performance_tab()
        self._create_accessibility_tab()
        self._create_advanced_tab()
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self._apply_and_close)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_changes)
        layout.addWidget(button_box)
    
    def _create_onboarding_tab(self):
        """Create onboarding configuration tab"""
        tab = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # User Level
        self._add_config_widget(layout, ConfigUIDefinition(
            key="onboarding.user_level",
            label="User Experience Level",
            widget_type=ConfigWidgetType.CHOICE,
            description="Your experience level affects the complexity of features shown",
            options=["beginner", "intermediate", "advanced"],
            group="User Profile"
        ))
        
        # Help Preferences
        help_group = QGroupBox("Help & Guidance")
        help_layout = QVBoxLayout(help_group)
        
        self._add_config_widget(help_layout, ConfigUIDefinition(
            key="onboarding.help_preferences.show_tips",
            label="Show Smart Tips",
            widget_type=ConfigWidgetType.BOOLEAN,
            description="Display contextual tips and suggestions"
        ))
        
        self._add_config_widget(help_layout, ConfigUIDefinition(
            key="onboarding.help_preferences.tutorial_speed",
            label="Tutorial Speed",
            widget_type=ConfigWidgetType.CHOICE,
            description="Speed of interactive tutorials",
            options=["slow", "normal", "fast"]
        ))
        
        self._add_config_widget(help_layout, ConfigUIDefinition(
            key="onboarding.help_preferences.auto_advance",
            label="Auto-advance Tutorials",
            widget_type=ConfigWidgetType.BOOLEAN,
            description="Automatically advance to next tutorial step"
        ))
        
        layout.addWidget(help_group)
        
        # Feature Discovery
        discovery_group = QGroupBox("Feature Discovery")
        discovery_layout = QVBoxLayout(discovery_group)
        
        self._add_config_widget(discovery_layout, ConfigUIDefinition(
            key="onboarding.feature_discovery.auto_highlight",
            label="Auto-highlight New Features",
            widget_type=ConfigWidgetType.BOOLEAN,
            description="Automatically highlight newly available features"
        ))
        
        self._add_config_widget(discovery_layout, ConfigUIDefinition(
            key="onboarding.feature_discovery.discovery_pace",
            label="Discovery Pace",
            widget_type=ConfigWidgetType.CHOICE,
            description="How quickly new features are introduced",
            options=["slow", "normal", "fast"]
        ))
        
        layout.addWidget(discovery_group)
        
        tab.setWidget(content)
        self.tab_widget.addTab(tab, "Onboarding")
    
    def _create_ui_tab(self):
        """Create UI configuration tab"""
        tab = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Theme
        theme_group = QGroupBox("Appearance")
        theme_layout = QVBoxLayout(theme_group)
        
        self._add_config_widget(theme_layout, ConfigUIDefinition(
            key="ui.theme",
            label="Theme",
            widget_type=ConfigWidgetType.CHOICE,
            description="Application color theme",
            options=["light", "dark", "auto", "high_contrast"]
        ))
        
        self._add_config_widget(theme_layout, ConfigUIDefinition(
            key="ui.font_size",
            label="Font Size",
            widget_type=ConfigWidgetType.CHOICE,
            description="Base font size for the interface",
            options=["small", "medium", "large", "extra_large"]
        ))
        
        self._add_config_widget(theme_layout, ConfigUIDefinition(
            key="ui.animation_speed",
            label="Animation Speed",
            widget_type=ConfigWidgetType.SLIDER,
            description="Speed of UI animations (0.1 = slow, 3.0 = fast)",
            min_value=0.1,
            max_value=3.0,
            step=0.1
        ))
        
        layout.addWidget(theme_group)
        
        # Layout
        layout_group = QGroupBox("Layout")
        layout_layout = QVBoxLayout(layout_group)
        
        self._add_config_widget(layout_layout, ConfigUIDefinition(
            key="ui.layout",
            label="Layout Style",
            widget_type=ConfigWidgetType.CHOICE,
            description="Overall layout style",
            options=["standard", "simplified", "compact", "developer", "research"]
        ))
        
        self._add_config_widget(layout_layout, ConfigUIDefinition(
            key="ui.sidebar_position",
            label="Sidebar Position",
            widget_type=ConfigWidgetType.CHOICE,
            description="Position of the main sidebar",
            options=["left", "right", "hidden"]
        ))
        
        layout.addWidget(layout_group)
        
        tab.setWidget(content)
        self.tab_widget.addTab(tab, "Interface")
    
    def _create_performance_tab(self):
        """Create performance configuration tab"""
        tab = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QVBoxLayout(perf_group)
        
        self._add_config_widget(perf_layout, ConfigUIDefinition(
            key="performance.cache_size_mb",
            label="Cache Size (MB)",
            widget_type=ConfigWidgetType.NUMBER,
            description="Amount of memory to use for caching",
            min_value=50,
            max_value=1000,
            step=10
        ))
        
        self._add_config_widget(perf_layout, ConfigUIDefinition(
            key="performance.lazy_loading",
            label="Lazy Loading",
            widget_type=ConfigWidgetType.BOOLEAN,
            description="Load content only when needed"
        ))
        
        self._add_config_widget(perf_layout, ConfigUIDefinition(
            key="performance.animation_quality",
            label="Animation Quality",
            widget_type=ConfigWidgetType.CHOICE,
            description="Quality level for animations",
            options=["low", "medium", "high"]
        ))
        
        layout.addWidget(perf_group)
        
        tab.setWidget(content)
        self.tab_widget.addTab(tab, "Performance")
    
    def _create_accessibility_tab(self):
        """Create accessibility configuration tab"""
        tab = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        a11y_group = QGroupBox("Accessibility Options")
        a11y_layout = QVBoxLayout(a11y_group)
        
        self._add_config_widget(a11y_layout, ConfigUIDefinition(
            key="accessibility.high_contrast",
            label="High Contrast Mode",
            widget_type=ConfigWidgetType.BOOLEAN,
            description="Use high contrast colors for better visibility"
        ))
        
        self._add_config_widget(a11y_layout, ConfigUIDefinition(
            key="accessibility.large_fonts",
            label="Large Fonts",
            widget_type=ConfigWidgetType.BOOLEAN,
            description="Use larger fonts throughout the interface"
        ))
        
        self._add_config_widget(a11y_layout, ConfigUIDefinition(
            key="accessibility.reduced_motion",
            label="Reduced Motion",
            widget_type=ConfigWidgetType.BOOLEAN,
            description="Minimize animations and transitions"
        ))
        
        self._add_config_widget(a11y_layout, ConfigUIDefinition(
            key="accessibility.keyboard_navigation",
            label="Enhanced Keyboard Navigation",
            widget_type=ConfigWidgetType.BOOLEAN,
            description="Improve keyboard navigation support"
        ))
        
        layout.addWidget(a11y_group)
        
        tab.setWidget(content)
        self.tab_widget.addTab(tab, "Accessibility")
    
    def _create_advanced_tab(self):
        """Create advanced configuration tab"""
        tab = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # System settings
        system_group = QGroupBox("System Settings")
        system_layout = QVBoxLayout(system_group)
        
        self._add_config_widget(system_layout, ConfigUIDefinition(
            key="system.debug_mode",
            label="Debug Mode",
            widget_type=ConfigWidgetType.BOOLEAN,
            description="Enable debug logging and developer tools",
            advanced=True,
            requires_restart=True
        ))
        
        self._add_config_widget(system_layout, ConfigUIDefinition(
            key="system.telemetry_enabled",
            label="Telemetry",
            widget_type=ConfigWidgetType.BOOLEAN,
            description="Send anonymous usage data to help improve the application",
            advanced=True
        ))
        
        layout.addWidget(system_group)
        
        # Custom JSON configuration
        json_group = QGroupBox("Custom Configuration")
        json_layout = QVBoxLayout(json_group)
        
        self._add_config_widget(json_layout, ConfigUIDefinition(
            key="custom_settings",
            label="Custom Settings (JSON)",
            widget_type=ConfigWidgetType.JSON_EDITOR,
            description="Advanced custom configuration in JSON format",
            advanced=True
        ))
        
        layout.addWidget(json_group)
        
        tab.setWidget(content)
        self.tab_widget.addTab(tab, "Advanced")
    
    def _add_config_widget(self, layout: QVBoxLayout, definition: ConfigUIDefinition):
        """Add a configuration widget to the layout"""
        widget = ConfigurationWidget(definition)
        widget.value_changed.connect(self._on_value_changed)
        self.config_widgets[definition.key] = widget
        layout.addWidget(widget)
    
    def _on_value_changed(self, key: str, value: Any):
        """Handle configuration value change"""
        self.pending_changes[key] = value
    
    def _load_current_values(self):
        """Load current configuration values into widgets"""
        for key, widget in self.config_widgets.items():
            current_value = self.config_manager.get(key)
            if current_value is not None:
                widget.set_value(current_value)
    
    def _apply_changes(self):
        """Apply pending configuration changes"""
        for key, value in self.pending_changes.items():
            self.config_manager.set(key, value, scope=ConfigScope.USER)
        
        self.pending_changes.clear()
        QMessageBox.information(self, "Settings Applied", "Configuration changes have been applied.")
    
    def _apply_and_close(self):
        """Apply changes and close dialog"""
        self._apply_changes()
        self.accept()


class ConfigurationUIManager:
    """Manager for configuration UI components"""
    
    def __init__(self, config_manager: AdvancedConfigurationManager):
        self.config_manager = config_manager
        self.active_dialogs: List[QDialog] = []
        
        # Setup change listeners
        self.config_manager.add_change_listener(self._on_config_changed)
    
    def show_configuration_dialog(self, parent=None) -> ConfigurationDialog:
        """Show the main configuration dialog"""
        dialog = ConfigurationDialog(self.config_manager, parent)
        self.active_dialogs.append(dialog)
        dialog.finished.connect(lambda: self._remove_dialog(dialog))
        dialog.show()
        return dialog
    
    def show_profile_manager(self, parent=None):
        """Show the profile management dialog"""
        # Implementation for profile management UI
        pass
    
    def show_quick_settings(self, parent=None):
        """Show quick settings popup"""
        # Implementation for quick settings UI
        pass
    
    def _on_config_changed(self, key: str, old_value: Any, new_value: Any):
        """Handle configuration changes"""
        logger.debug(f"Configuration changed: {key} = {new_value}")
        
        # Update any active dialogs
        for dialog in self.active_dialogs:
            if isinstance(dialog, ConfigurationDialog) and key in dialog.config_widgets:
                dialog.config_widgets[key].set_value(new_value)
    
    def _remove_dialog(self, dialog: QDialog):
        """Remove dialog from active list"""
        if dialog in self.active_dialogs:
            self.active_dialogs.remove(dialog)
    
    def apply_theme_changes(self, theme_settings: Dict[str, Any]):
        """Apply theme changes to the UI"""
        # Implementation for applying theme changes
        pass
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            "user_level": self.config_manager.get("onboarding.user_level"),
            "theme": self.config_manager.get("ui.theme"),
            "layout": self.config_manager.get("ui.layout"),
            "help_enabled": self.config_manager.get("onboarding.help_preferences.show_tips"),
            "active_profile": self.config_manager.active_profile_id,
            "total_profiles": len(self.config_manager.profiles)
        }
