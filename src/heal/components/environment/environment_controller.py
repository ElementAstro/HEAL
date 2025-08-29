"""
Environment Controller
Consolidated controller that merges functionality from:
- EnvironmentConfigManager
- EnvironmentSignalManager  
- EnvironmentNavigationManager
- ToolStatusManager (coordination)

Provides unified interface for environment management operations.
"""

from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget

from ...common.logging_config import get_logger
from .platform_detector import PlatformDetector
from .tool_status_manager import ToolStatusManager, ToolStatus

logger = get_logger(__name__)


class EnvironmentState(Enum):
    """Environment states"""
    INITIALIZING = "initializing"
    READY = "ready"
    CONFIGURING = "configuring"
    ERROR = "error"
    UPDATING = "updating"


class NavigationContext(Enum):
    """Navigation contexts for environment interface"""
    OVERVIEW = "overview"
    TOOLS = "tools"
    CONFIGURATION = "configuration"
    STATUS = "status"
    ADVANCED = "advanced"


@dataclass
class EnvironmentConfig:
    """Environment configuration data"""
    platform: str = ""
    tools_directory: str = ""
    auto_detect_tools: bool = True
    check_updates: bool = True
    show_advanced_options: bool = False
    preferred_tools: List[str] = field(default_factory=list)
    tool_paths: Dict[str, str] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class EnvironmentController(QObject):
    """
    Unified environment controller that consolidates:
    - Configuration management
    - Signal coordination
    - Navigation state management
    - Tool status coordination
    """
    
    # Consolidated signals
    state_changed = Signal(str)  # new_state
    config_updated = Signal(dict)  # config_data
    tool_status_changed = Signal(str, str)  # tool_name, status
    navigation_changed = Signal(str)  # new_context
    environment_ready = Signal()
    environment_error = Signal(str)  # error_message
    
    # Tool-related signals
    tool_detected = Signal(str, str)  # tool_name, path
    tool_configured = Signal(str)  # tool_name
    tool_validation_completed = Signal(dict)  # validation_results
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.EnvironmentController")
        
        # State management
        self.current_state = EnvironmentState.INITIALIZING
        self.current_context = NavigationContext.OVERVIEW
        
        # Configuration
        self.config = EnvironmentConfig()
        self.config_file = Path("config/environment.json")
        
        # Integrated components
        self.platform_detector = PlatformDetector()
        self.tool_status_manager = ToolStatusManager(self)
        
        # Navigation and UI state
        self.navigation_history: List[NavigationContext] = []
        self.active_widgets: Dict[str, QWidget] = {}
        self.widget_states: Dict[str, Dict[str, Any]] = {}
        
        # Tool management
        self.detected_tools: Dict[str, str] = {}  # tool_name -> path
        self.tool_configs: Dict[str, Dict[str, Any]] = {}
        
        # Validation and monitoring
        self.validation_timer = QTimer()
        self.validation_timer.timeout.connect(self._periodic_validation)
        self.validation_timer.start(30000)  # Check every 30 seconds
        
        # Initialize
        self._load_configuration()
        self._initialize_platform()
        self._setup_tool_monitoring()
        
        self.logger.info("EnvironmentController initialized")
    
    def initialize_environment(self) -> bool:
        """Initialize the environment system"""
        try:
            self._set_state(EnvironmentState.INITIALIZING)
            
            # Detect platform
            platform_info = self.platform_detector.get_platform_info()
            self.config.platform = platform_info.get('platform', 'unknown')
            
            # Auto-detect tools if enabled
            if self.config.auto_detect_tools:
                self._auto_detect_tools()
            
            # Validate configuration
            if self._validate_environment():
                self._set_state(EnvironmentState.READY)
                self.environment_ready.emit()
                self.logger.info("Environment initialized successfully")
                return True
            else:
                self._set_state(EnvironmentState.ERROR)
                self.environment_error.emit("Environment validation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize environment: {e}")
            self._set_state(EnvironmentState.ERROR)
            self.environment_error.emit(str(e))
            return False
    
    def navigate_to(self, context: NavigationContext) -> None:
        """Navigate to a specific context"""
        if self.current_context != context:
            # Save current state
            self._save_widget_state(self.current_context)
            
            # Update navigation
            self.navigation_history.append(self.current_context)
            self.current_context = context
            
            # Restore state for new context
            self._restore_widget_state(context)
            
            self.navigation_changed.emit(context.value)
            self.logger.debug(f"Navigated to: {context.value}")
    
    def navigate_back(self) -> bool:
        """Navigate back to previous context"""
        if self.navigation_history:
            previous_context = self.navigation_history.pop()
            self.navigate_to(previous_context)
            return True
        return False
    
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """Update environment configuration"""
        try:
            # Update configuration
            for key, value in config_updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    self.config.custom_settings[key] = value
            
            # Save configuration
            self._save_configuration()
            
            # Emit signal
            self.config_updated.emit(config_updates)
            
            self.logger.info(f"Configuration updated: {list(config_updates.keys())}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
            return False
    
    def register_tool(self, tool_name: str, tool_path: str, auto_configure: bool = True) -> bool:
        """Register a tool with the environment"""
        try:
            # Validate tool exists
            if not Path(tool_path).exists():
                self.logger.warning(f"Tool path does not exist: {tool_path}")
                return False
            
            # Register with tool status manager
            self.tool_status_manager.add_tool(tool_name, tool_path)
            
            # Store in detected tools
            self.detected_tools[tool_name] = tool_path
            self.config.tool_paths[tool_name] = tool_path
            
            # Auto-configure if requested
            if auto_configure:
                self._configure_tool(tool_name, tool_path)
            
            # Emit signals
            self.tool_detected.emit(tool_name, tool_path)
            
            self.logger.info(f"Registered tool: {tool_name} at {tool_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register tool {tool_name}: {e}")
            return False
    
    def get_tool_status(self, tool_name: str) -> Optional[ToolStatus]:
        """Get status of a specific tool"""
        return self.tool_status_manager.get_tool_status(tool_name)
    
    def get_all_tool_statuses(self) -> Dict[str, ToolStatus]:
        """Get status of all tools"""
        return self.tool_status_manager.get_all_statuses()
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate current environment configuration"""
        validation_results = {
            'platform': self.config.platform,
            'tools_detected': len(self.detected_tools),
            'tools_configured': 0,
            'issues': [],
            'recommendations': []
        }
        
        # Validate tools
        for tool_name, tool_path in self.detected_tools.items():
            if Path(tool_path).exists():
                validation_results['tools_configured'] += 1
            else:
                validation_results['issues'].append(f"Tool not found: {tool_name} at {tool_path}")
        
        # Platform-specific validation
        platform_issues = self.platform_detector.validate_platform()
        validation_results['issues'].extend(platform_issues)
        
        # Generate recommendations
        if validation_results['tools_detected'] < 3:
            validation_results['recommendations'].append("Consider installing additional development tools")
        
        return validation_results
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """Get comprehensive environment summary"""
        return {
            'state': self.current_state.value,
            'context': self.current_context.value,
            'platform': self.config.platform,
            'tools_count': len(self.detected_tools),
            'config_file': str(self.config_file),
            'last_validation': time.time()
        }
    
    def register_widget(self, context: str, widget: QWidget) -> None:
        """Register a widget for state management"""
        self.active_widgets[context] = widget
        self.logger.debug(f"Registered widget for context: {context}")
    
    def _set_state(self, new_state: EnvironmentState) -> None:
        """Set environment state"""
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            self.state_changed.emit(new_state.value)
            self.logger.debug(f"Environment state: {old_state.value} -> {new_state.value}")
    
    def _auto_detect_tools(self) -> None:
        """Auto-detect development tools"""
        # Use platform detector to find common tools
        detected = self.platform_detector.detect_development_tools()
        
        for tool_name, tool_info in detected.items():
            if tool_info.get('path'):
                self.register_tool(tool_name, tool_info['path'], auto_configure=False)
    
    def _configure_tool(self, tool_name: str, tool_path: str) -> None:
        """Configure a specific tool"""
        try:
            # Basic tool configuration
            tool_config = {
                'path': tool_path,
                'configured_at': time.time(),
                'auto_detected': True
            }
            
            self.tool_configs[tool_name] = tool_config
            self.tool_configured.emit(tool_name)
            
            self.logger.debug(f"Configured tool: {tool_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to configure tool {tool_name}: {e}")
    
    def _validate_environment(self) -> bool:
        """Validate environment configuration"""
        try:
            # Basic validation
            if not self.config.platform:
                return False
            
            # Tool validation
            if self.config.auto_detect_tools and not self.detected_tools:
                self.logger.warning("Auto-detect enabled but no tools found")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Environment validation failed: {e}")
            return False
    
    def _periodic_validation(self) -> None:
        """Periodic environment validation"""
        try:
            validation_results = self.validate_environment()
            self.tool_validation_completed.emit(validation_results)
        except Exception as e:
            self.logger.error(f"Periodic validation failed: {e}")
    
    def _save_widget_state(self, context: NavigationContext) -> None:
        """Save widget state for context"""
        context_key = context.value
        if context_key in self.active_widgets:
            # Save basic state (placeholder for actual implementation)
            self.widget_states[context_key] = {
                'saved_at': time.time()
            }
    
    def _restore_widget_state(self, context: NavigationContext) -> None:
        """Restore widget state for context"""
        context_key = context.value
        if context_key in self.widget_states:
            # Restore state (placeholder for actual implementation)
            self.logger.debug(f"Restored state for context: {context_key}")
    
    def _load_configuration(self) -> None:
        """Load environment configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load configuration
                self.config.platform = data.get('platform', '')
                self.config.tools_directory = data.get('tools_directory', '')
                self.config.auto_detect_tools = data.get('auto_detect_tools', True)
                self.config.check_updates = data.get('check_updates', True)
                self.config.show_advanced_options = data.get('show_advanced_options', False)
                self.config.preferred_tools = data.get('preferred_tools', [])
                self.config.tool_paths = data.get('tool_paths', {})
                self.config.environment_variables = data.get('environment_variables', {})
                self.config.custom_settings = data.get('custom_settings', {})
                
                self.logger.info("Environment configuration loaded")
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
    
    def _save_configuration(self) -> None:
        """Save environment configuration"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'platform': self.config.platform,
                'tools_directory': self.config.tools_directory,
                'auto_detect_tools': self.config.auto_detect_tools,
                'check_updates': self.config.check_updates,
                'show_advanced_options': self.config.show_advanced_options,
                'preferred_tools': self.config.preferred_tools,
                'tool_paths': self.config.tool_paths,
                'environment_variables': self.config.environment_variables,
                'custom_settings': self.config.custom_settings,
                'last_updated': time.time()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.debug("Environment configuration saved")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def _initialize_platform(self) -> None:
        """Initialize platform-specific settings"""
        try:
            platform_info = self.platform_detector.get_platform_info()
            
            # Update configuration with platform info
            self.config.platform = platform_info.get('platform', 'unknown')
            
            # Set platform-specific defaults
            if self.config.platform == 'Windows':
                self.config.tools_directory = self.config.tools_directory or "C:/Tools"
            elif self.config.platform == 'Linux':
                self.config.tools_directory = self.config.tools_directory or "/usr/local/bin"
            elif self.config.platform == 'macOS':
                self.config.tools_directory = self.config.tools_directory or "/usr/local/bin"
            
            self.logger.info(f"Platform initialized: {self.config.platform}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize platform: {e}")
    
    def _setup_tool_monitoring(self) -> None:
        """Setup tool status monitoring"""
        try:
            # Connect tool status manager signals
            self.tool_status_manager.tool_status_changed.connect(
                lambda name, status: self.tool_status_changed.emit(name, status.value)
            )
            
            # Start monitoring
            self.tool_status_manager.start_monitoring()
            
            self.logger.debug("Tool monitoring setup complete")
            
        except Exception as e:
            self.logger.error(f"Failed to setup tool monitoring: {e}")


class EnvironmentUICoordinator(QObject):
    """
    Coordinates UI components for the environment interface.
    Manages widget lifecycle and state synchronization.
    """
    
    widget_activated = Signal(str)  # widget_name
    widget_deactivated = Signal(str)  # widget_name
    layout_changed = Signal(str)  # layout_name
    
    def __init__(self, controller: EnvironmentController, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.controller = controller
        self.logger = get_logger(f"{__name__}.EnvironmentUICoordinator")
        
        # UI state management
        self.active_cards: Set[str] = set()
        self.card_positions: Dict[str, Dict[str, int]] = {}
        self.layout_preferences: Dict[str, Any] = {}
        
        # Connect to controller signals
        self._connect_controller_signals()
        
        self.logger.info("EnvironmentUICoordinator initialized")
    
    def activate_card(self, card_name: str, position: Optional[Dict[str, int]] = None) -> None:
        """Activate an environment card"""
        self.active_cards.add(card_name)
        
        if position:
            self.card_positions[card_name] = position
        
        self.widget_activated.emit(card_name)
        self.logger.debug(f"Activated card: {card_name}")
    
    def deactivate_card(self, card_name: str) -> None:
        """Deactivate an environment card"""
        self.active_cards.discard(card_name)
        self.widget_deactivated.emit(card_name)
        self.logger.debug(f"Deactivated card: {card_name}")
    
    def get_active_cards(self) -> Set[str]:
        """Get currently active cards"""
        return self.active_cards.copy()
    
    def set_layout_preference(self, layout_name: str, preferences: Dict[str, Any]) -> None:
        """Set layout preferences"""
        self.layout_preferences[layout_name] = preferences
        self.layout_changed.emit(layout_name)
        self.logger.debug(f"Layout preferences updated: {layout_name}")
    
    def get_layout_preference(self, layout_name: str) -> Dict[str, Any]:
        """Get layout preferences"""
        return self.layout_preferences.get(layout_name, {})
    
    def _connect_controller_signals(self) -> None:
        """Connect to controller signals"""
        self.controller.navigation_changed.connect(self._on_navigation_changed)
        self.controller.tool_status_changed.connect(self._on_tool_status_changed)
        self.controller.state_changed.connect(self._on_state_changed)
    
    def _on_navigation_changed(self, new_context: str) -> None:
        """Handle navigation changes"""
        self.logger.debug(f"Navigation changed to: {new_context}")
        # Update UI based on new context
    
    def _on_tool_status_changed(self, tool_name: str, status: str) -> None:
        """Handle tool status changes"""
        self.logger.debug(f"Tool {tool_name} status changed to: {status}")
        # Update relevant UI components
    
    def _on_state_changed(self, new_state: str) -> None:
        """Handle environment state changes"""
        self.logger.debug(f"Environment state changed to: {new_state}")
        # Update UI based on new state
