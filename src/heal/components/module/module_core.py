"""
Module Core Components
Consolidated business logic components for module management.
Merges previously separate manager classes into cohesive units.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import time
import json
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from ...common.logging_config import get_logger
from .module_models import ModuleConfig, ModuleMetrics, ModuleState
from .module_workflow_manager import ModuleWorkflowManager
from .module_operation_handler import ModuleOperationHandler
from .module_bulk_operations import ModuleBulkOperations

logger = get_logger(__name__)


@dataclass
class ModuleInfo:
    """Consolidated module information"""
    name: str
    path: str
    enabled: bool = True
    auto_load: bool = False
    version: str = "unknown"
    author: str = "unknown"
    description: str = ""
    dependencies: List[str] = None
    tags: Set[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = set()
        if self.metadata is None:
            self.metadata = {}


class ModuleController(QObject):
    """
    Consolidated module controller that merges functionality from:
    - ModuleConfigManager
    - ModuleEventManager  
    - ModuleMetricsManager
    - ModuleOperationHandler (partially)
    
    Provides unified interface for module management operations.
    """
    
    # Consolidated signals
    module_added = Signal(str)
    module_removed = Signal(str)
    module_enabled = Signal(str)
    module_disabled = Signal(str)
    module_loaded = Signal(str)
    module_unloaded = Signal(str)
    config_changed = Signal(str, dict)
    metrics_updated = Signal(str, dict)
    operation_started = Signal(str, str)  # module_name, operation
    operation_completed = Signal(str, str, bool)  # module_name, operation, success
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.ModuleController")
        
        # Consolidated data storage
        self.modules: Dict[str, ModuleInfo] = {}
        self.module_configs: Dict[str, ModuleConfig] = {}
        self.module_metrics: Dict[str, ModuleMetrics] = {}
        self.module_states: Dict[str, ModuleState] = {}
        
        # Integrated managers
        self.workflow_manager = ModuleWorkflowManager(self)
        self.operation_handler = ModuleOperationHandler(self)
        self.bulk_operations = ModuleBulkOperations(self)
        
        # Configuration
        self.config_file = Path("config/modules.json")
        self.metrics_file = Path("config/module_metrics.json")
        
        # Load initial data
        self._load_configuration()
        self._load_metrics()
        
        self.logger.info("ModuleController initialized")
    
    def add_module(self, module_info: ModuleInfo) -> bool:
        """Add a new module"""
        try:
            if module_info.name in self.modules:
                self.logger.warning(f"Module {module_info.name} already exists")
                return False
            
            self.modules[module_info.name] = module_info
            self.module_states[module_info.name] = ModuleState.IDLE
            
            # Initialize metrics
            self.module_metrics[module_info.name] = ModuleMetrics()
            
            # Initialize config
            self.module_configs[module_info.name] = ModuleConfig(
                name=module_info.name,
                enabled=module_info.enabled,
                auto_load=module_info.auto_load
            )
            
            self.module_added.emit(module_info.name)
            self._save_configuration()
            
            self.logger.info(f"Added module: {module_info.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add module {module_info.name}: {e}")
            return False
    
    def remove_module(self, module_name: str) -> bool:
        """Remove a module"""
        try:
            if module_name not in self.modules:
                self.logger.warning(f"Module {module_name} not found")
                return False
            
            # Cleanup
            self.modules.pop(module_name, None)
            self.module_configs.pop(module_name, None)
            self.module_metrics.pop(module_name, None)
            self.module_states.pop(module_name, None)
            
            self.module_removed.emit(module_name)
            self._save_configuration()
            
            self.logger.info(f"Removed module: {module_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove module {module_name}: {e}")
            return False
    
    def enable_module(self, module_name: str) -> bool:
        """Enable a module"""
        try:
            if module_name not in self.modules:
                return False
            
            self.modules[module_name].enabled = True
            if module_name in self.module_configs:
                self.module_configs[module_name].enabled = True
            
            self.module_enabled.emit(module_name)
            self._save_configuration()
            
            self.logger.info(f"Enabled module: {module_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable module {module_name}: {e}")
            return False
    
    def disable_module(self, module_name: str) -> bool:
        """Disable a module"""
        try:
            if module_name not in self.modules:
                return False
            
            self.modules[module_name].enabled = False
            if module_name in self.module_configs:
                self.module_configs[module_name].enabled = False
            
            self.module_disabled.emit(module_name)
            self._save_configuration()
            
            self.logger.info(f"Disabled module: {module_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable module {module_name}: {e}")
            return False
    
    def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """Get module information"""
        return self.modules.get(module_name)
    
    def get_module_config(self, module_name: str) -> Optional[ModuleConfig]:
        """Get module configuration"""
        return self.module_configs.get(module_name)
    
    def get_module_metrics(self, module_name: str) -> Optional[ModuleMetrics]:
        """Get module metrics"""
        return self.module_metrics.get(module_name)
    
    def get_module_state(self, module_name: str) -> Optional[ModuleState]:
        """Get module state"""
        return self.module_states.get(module_name)
    
    def update_module_metrics(self, module_name: str, metrics: Dict[str, Any]) -> None:
        """Update module metrics"""
        if module_name not in self.module_metrics:
            self.module_metrics[module_name] = ModuleMetrics()
        
        module_metrics = self.module_metrics[module_name]
        
        # Update metrics fields
        for key, value in metrics.items():
            if hasattr(module_metrics, key):
                setattr(module_metrics, key, value)
        
        self.metrics_updated.emit(module_name, metrics)
        self._save_metrics()
    
    def set_module_state(self, module_name: str, state: ModuleState) -> None:
        """Set module state"""
        if module_name in self.modules:
            old_state = self.module_states.get(module_name, ModuleState.IDLE)
            self.module_states[module_name] = state
            
            self.logger.debug(f"Module {module_name} state: {old_state} -> {state}")
    
    def get_all_modules(self) -> Dict[str, ModuleInfo]:
        """Get all modules"""
        return self.modules.copy()
    
    def get_enabled_modules(self) -> Dict[str, ModuleInfo]:
        """Get enabled modules"""
        return {name: info for name, info in self.modules.items() if info.enabled}
    
    def _load_configuration(self) -> None:
        """Load module configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for name, module_data in data.get('modules', {}).items():
                    module_info = ModuleInfo(
                        name=module_data['name'],
                        path=module_data['path'],
                        enabled=module_data.get('enabled', True),
                        auto_load=module_data.get('auto_load', False),
                        version=module_data.get('version', 'unknown'),
                        author=module_data.get('author', 'unknown'),
                        description=module_data.get('description', ''),
                        dependencies=module_data.get('dependencies', []),
                        tags=set(module_data.get('tags', [])),
                        metadata=module_data.get('metadata', {})
                    )
                    self.modules[name] = module_info
                    self.module_states[name] = ModuleState.IDLE
                
                self.logger.info(f"Loaded {len(self.modules)} modules from configuration")
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
    
    def _save_configuration(self) -> None:
        """Save module configuration"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'modules': {
                    name: {
                        'name': info.name,
                        'path': info.path,
                        'enabled': info.enabled,
                        'auto_load': info.auto_load,
                        'version': info.version,
                        'author': info.author,
                        'description': info.description,
                        'dependencies': info.dependencies,
                        'tags': list(info.tags),
                        'metadata': info.metadata
                    }
                    for name, info in self.modules.items()
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.debug("Configuration saved")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def _load_metrics(self) -> None:
        """Load module metrics"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for name, metrics_data in data.get('metrics', {}).items():
                    if name in self.modules:
                        metrics = ModuleMetrics()
                        for key, value in metrics_data.items():
                            if hasattr(metrics, key):
                                setattr(metrics, key, value)
                        self.module_metrics[name] = metrics
                
                self.logger.debug("Metrics loaded")
                
        except Exception as e:
            self.logger.error(f"Failed to load metrics: {e}")
    
    def _save_metrics(self) -> None:
        """Save module metrics"""
        try:
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'metrics': {
                    name: {
                        'load_time': metrics.load_time,
                        'memory_usage': metrics.memory_usage,
                        'cpu_usage': metrics.cpu_usage,
                        'error_count': metrics.error_count,
                        'last_error': metrics.last_error,
                        'operations_count': metrics.operations_count,
                        'success_rate': metrics.success_rate
                    }
                    for name, metrics in self.module_metrics.items()
                }
            }
            
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
