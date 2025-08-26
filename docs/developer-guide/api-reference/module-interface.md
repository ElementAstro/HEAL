# Module Interface API Documentation

## Overview

The Module Interface system provides a comprehensive framework for managing, validating, and monitoring Python modules within the HEAL application. This documentation covers all APIs, components, and usage patterns.

## Table of Contents

1. [Core Components](#core-components)
2. [Module Interface API](#module-interface-api)
3. [Module Validator API](#module-validator-api)
4. [Performance Monitor API](#performance-monitor-api)
5. [Module Controller API](#module-controller-api)
6. [UI Components API](#ui-components-api)
7. [Configuration Reference](#configuration-reference)
8. [Examples](#examples)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)

## Core Components

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Module Interface                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Module    │  │ Performance │  │    Event Manager    │  │
│  │ Validator   │  │  Monitor    │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Module    │  │ Validation  │  │ Performance         │  │
│  │ Controller  │  │     UI      │  │ Dashboard UI        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Relationships

- **ModuleInterface**: Main orchestrator that coordinates all components
- **ModuleValidator**: Handles module validation with multiple security levels
- **PerformanceMonitor**: Monitors system and module performance metrics
- **ModuleController**: Manages module lifecycle and operations
- **UI Components**: Provide user interfaces for validation and monitoring

## Module Interface API

### Class: `ModuleInterface`

The main interface class that orchestrates all module operations.

#### Constructor

```python
ModuleInterface(config: Dict[str, Any])
```

**Parameters:**

- `config`: Configuration dictionary with the following keys:
  - `base_path` (str): Base directory for module discovery
  - `auto_discovery` (bool): Enable automatic module discovery
  - `monitoring_enabled` (bool): Enable performance monitoring
  - `validation_level` (str): Default validation level ('basic', 'standard', 'strict', 'security')

#### Methods

##### `load_module(module_path: str, **kwargs) -> Dict[str, Any]`

Load and execute a module.

**Parameters:**

- `module_path`: Path to the module file
- `**kwargs`: Additional arguments passed to the module

**Returns:**

- Dictionary with keys:
  - `success` (bool): Whether the operation succeeded
  - `result` (Any): Module execution result
  - `error` (str, optional): Error message if failed
  - `execution_time` (float): Time taken to execute
  - `module_info` (dict): Module metadata

**Example:**

```python
interface = ModuleInterface({
    'base_path': '/path/to/modules',
    'auto_discovery': True,
    'monitoring_enabled': True
})

result = interface.load_module('my_module.py')
if result['success']:
    print(f"Module executed successfully: {result['result']}")
else:
    print(f"Module failed: {result['error']}")
```

##### `discover_modules(path: Optional[str] = None) -> List[str]`

Discover available modules in the specified path.

**Parameters:**

- `path`: Directory to search (defaults to configured base_path)

**Returns:**

- List of discovered module file paths

##### `validate_module(module_path: str, level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationResult`

Validate a module using the integrated validator.

**Parameters:**

- `module_path`: Path to the module file
- `level`: Validation level to apply

**Returns:**

- `ValidationResult` object with validation details

##### `get_module_info(module_path: str) -> Dict[str, Any]`

Get detailed information about a module.

**Parameters:**

- `module_path`: Path to the module file

**Returns:**

- Dictionary with module metadata, dependencies, and analysis

##### `register_event_handler(event_type: str, handler: Callable) -> None`

Register an event handler for module events.

**Parameters:**

- `event_type`: Type of event to listen for
- `handler`: Callback function to handle the event

##### `get_state() -> ModuleState`

Get the current state of the module interface.

**Returns:**

- Current `ModuleState` enum value

##### `get_configuration() -> Dict[str, Any]`

Get current configuration.

**Returns:**

- Configuration dictionary

##### `update_configuration(new_config: Dict[str, Any]) -> None`

Update configuration settings.

**Parameters:**

- `new_config`: New configuration values to apply

### Enums

#### `ModuleState`

```python
class ModuleState(Enum):
    READY = "ready"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    SHUTDOWN = "shutdown"
```

## Module Validator API

### Class: `ModuleValidator`

Provides comprehensive module validation with multiple security levels.

#### Constructor

```python
ModuleValidator(config: Optional[Dict[str, Any]] = None)
```

#### Methods

##### `validate_module(module_path: str, level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationResult`

Validate a single module.

**Parameters:**

- `module_path`: Path to the module file
- `level`: Validation level to apply

**Returns:**

- `ValidationResult` object

##### `validate_batch(module_paths: List[str], level: ValidationLevel = ValidationLevel.STANDARD) -> List[ValidationResult]`

Validate multiple modules in batch.

**Parameters:**

- `module_paths`: List of module file paths
- `level`: Validation level to apply

**Returns:**

- List of `ValidationResult` objects

##### `analyze_module_structure(module_path: str) -> Dict[str, Any]`

Analyze module structure and extract metadata.

**Parameters:**

- `module_path`: Path to the module file

**Returns:**

- Dictionary with structure analysis

##### `check_security_issues(module_path: str) -> List[SecurityIssue]`

Perform security analysis on a module.

**Parameters:**

- `module_path`: Path to the module file

**Returns:**

- List of security issues found

### Enums

#### `ValidationLevel`

```python
class ValidationLevel(Enum):
    BASIC = "basic"          # Basic syntax and structure
    STANDARD = "standard"    # Standard validation + dependencies
    STRICT = "strict"        # Strict validation + best practices
    SECURITY = "security"    # Security-focused validation
```

### Data Classes

#### `ValidationResult`

```python
@dataclass
class ValidationResult:
    is_valid: bool
    issues: List[ValidationIssue]
    metadata: Dict[str, Any]
    execution_time: float
    validation_level: ValidationLevel
```

#### `ValidationIssue`

```python
@dataclass
class ValidationIssue:
    severity: str           # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    category: str          # Issue category
    description: str       # Human-readable description
    line_number: Optional[int]
    suggestion: Optional[str]
```

## Performance Monitor API

### Class: `PerformanceMonitor`

Real-time performance monitoring for modules and system resources.

#### Constructor

```python
PerformanceMonitor(config: Optional[Dict[str, Any]] = None)
```

#### Methods

##### `start() -> None`

Start performance monitoring.

##### `stop() -> None`

Stop performance monitoring.

##### `get_current_metrics() -> Dict[str, Any]`

Get current performance metrics.

**Returns:**

- Dictionary with current metrics:
  - `cpu_percent`: CPU usage percentage
  - `memory_percent`: Memory usage percentage
  - `disk_io_mb`: Disk I/O in MB/s
  - `network_io_kb`: Network I/O in KB/s
  - `active_modules`: Number of active modules
  - `total_operations`: Total operations performed
  - `error_rate`: Error rate percentage
  - `timestamp`: Current timestamp

##### `get_system_info() -> Dict[str, Any]`

Get system information.

**Returns:**

- Dictionary with system details

##### `track_module_operation(module_name: str, operation: str, duration: float) -> None`

Track a module operation for performance analysis.

**Parameters:**

- `module_name`: Name of the module
- `operation`: Type of operation performed
- `duration`: Operation duration in seconds

##### `get_module_metrics(module_name: str) -> Dict[str, Any]`

Get performance metrics for a specific module.

**Parameters:**

- `module_name`: Name of the module

**Returns:**

- Dictionary with module-specific metrics

##### `get_active_alerts() -> List[Dict[str, Any]]`

Get current performance alerts.

**Returns:**

- List of active alerts

##### `export_data(format: str = 'json') -> Dict[str, Any]`

Export performance data.

**Parameters:**

- `format`: Export format ('json', 'csv')

**Returns:**

- Exported data dictionary

##### `update_settings(settings: Dict[str, Any]) -> None`

Update monitoring settings.

**Parameters:**

- `settings`: New settings to apply

## Module Controller API

### Class: `ModuleController`

Centralized module management with async operations and batch processing.

#### Constructor

```python
ModuleController(base_path: str, config: Optional[Dict[str, Any]] = None)
```

#### Methods

##### `discover_modules() -> List[str]`

Discover available modules.

**Returns:**

- List of discovered module paths

##### `load_module(module_name: str) -> Dict[str, Any]`

Load a specific module.

**Parameters:**

- `module_name`: Name or path of the module

**Returns:**

- Load operation result

##### `load_module_async(module_name: str) -> concurrent.futures.Future`

Load a module asynchronously.

**Parameters:**

- `module_name`: Name or path of the module

**Returns:**

- Future object for the async operation

##### `load_modules_batch(module_names: List[str]) -> List[Dict[str, Any]]`

Load multiple modules in batch.

**Parameters:**

- `module_names`: List of module names to load

**Returns:**

- List of load operation results

##### `unload_module(module_name: str) -> bool`

Unload a loaded module.

**Parameters:**

- `module_name`: Name of the module to unload

**Returns:**

- Success status

##### `get_loaded_modules() -> List[str]`

Get list of currently loaded modules.

**Returns:**

- List of loaded module names

##### `get_module_dependencies(module_name: str) -> List[str]`

Get dependencies for a module.

**Parameters:**

- `module_name`: Name of the module

**Returns:**

- List of dependency names

##### `resolve_dependencies(module_name: str) -> bool`

Resolve and load module dependencies.

**Parameters:**

- `module_name`: Name of the module

**Returns:**

- Success status

## UI Components API

### Class: `ModuleValidationUI`

UI component for module validation with detailed reporting.

#### Constructor

```python
ModuleValidationUI(parent: tk.Widget, validator: ModuleValidator)
```

#### Methods

##### `validate_file(file_path: str) -> None`

Validate a single file and display results.

##### `validate_batch(file_paths: List[str]) -> None`

Validate multiple files in batch.

##### `export_results(format: str = 'json') -> None`

Export validation results.

### Class: `PerformanceDashboardUI`

Real-time performance monitoring dashboard.

#### Constructor

```python
PerformanceDashboardUI(parent: tk.Widget, performance_monitor: PerformanceMonitor)
```

#### Methods

##### `start_monitoring() -> None`

Start the monitoring dashboard.

##### `stop_monitoring() -> None`

Stop the monitoring dashboard.

##### `export_data() -> None`

Export performance data.

## Configuration Reference

### Module Interface Configuration

```python
{
    "base_path": "/path/to/modules",           # Base directory for modules
    "auto_discovery": True,                    # Enable auto-discovery
    "monitoring_enabled": True,                # Enable performance monitoring
    "validation_level": "standard",            # Default validation level
    "cache_enabled": True,                     # Enable module caching
    "max_cache_size": 100,                     # Maximum cache entries
    "timeout": 30,                             # Operation timeout in seconds
    "security_scan": True,                     # Enable security scanning
    "dependency_resolution": True,             # Enable dependency resolution
    "parallel_loading": True,                  # Enable parallel module loading
    "max_workers": 4,                          # Maximum worker threads
    "error_reporting": True,                   # Enable error reporting
    "logging_level": "INFO"                    # Logging level
}
```

### Validator Configuration

```python
{
    "validation_rules": {
        "syntax_check": True,                  # Check Python syntax
        "import_analysis": True,               # Analyze imports
        "security_scan": True,                 # Security scanning
        "metadata_validation": True,           # Validate metadata
        "dependency_check": True,              # Check dependencies
        "best_practices": True                 # Best practices check
    },
    "security_settings": {
        "dangerous_imports": ["os", "subprocess"],  # Flagged imports
        "dangerous_functions": ["eval", "exec"],    # Flagged functions
        "max_file_size": 10485760,             # Max file size (10MB)
        "scan_depth": 5                        # Maximum analysis depth
    }
}
```

### Performance Monitor Configuration

```python
{
    "monitoring_interval": 1.0,                # Monitoring interval in seconds
    "cpu_threshold": 80.0,                     # CPU alert threshold (%)
    "memory_threshold": 85.0,                  # Memory alert threshold (%)
    "disk_threshold": 90.0,                    # Disk alert threshold (%)
    "network_threshold": 1000.0,               # Network alert threshold (KB/s)
    "history_size": 1000,                      # Number of metrics to keep
    "enable_alerts": True,                     # Enable alert system
    "alert_cooldown": 300,                     # Alert cooldown in seconds
    "export_interval": 3600                    # Data export interval
}
```

## Examples

### Basic Module Loading

```python
from app.module_interface import ModuleInterface

# Initialize interface
config = {
    'base_path': '/path/to/modules',
    'auto_discovery': True,
    'monitoring_enabled': True
}
interface = ModuleInterface(config)

# Load and execute a module
result = interface.load_module('my_module.py', param1='value1')

if result['success']:
    print(f"Module output: {result['result']}")
    print(f"Execution time: {result['execution_time']:.2f}s")
else:
    print(f"Error: {result['error']}")
```

### Module Validation

```python
from app.components.module.module_validator import ModuleValidator, ValidationLevel

# Initialize validator
validator = ModuleValidator()

# Validate a module
result = validator.validate_module('module.py', ValidationLevel.SECURITY)

print(f"Valid: {result.is_valid}")
for issue in result.issues:
    print(f"{issue.severity}: {issue.description}")
```

### Performance Monitoring

```python
from app.components.module.performance_monitor import PerformanceMonitor

# Initialize monitor
monitor = PerformanceMonitor()

# Start monitoring
monitor.start()

# Get current metrics
metrics = monitor.get_current_metrics()
print(f"CPU: {metrics['cpu_percent']:.1f}%")
print(f"Memory: {metrics['memory_percent']:.1f}%")

# Track module operation
monitor.track_module_operation('my_module', 'execute', 0.5)

# Stop monitoring
monitor.stop()
```

### Batch Operations

```python
from app.components.module.module_controller import ModuleController

# Initialize controller
controller = ModuleController('/path/to/modules')

# Discover modules
modules = controller.discover_modules()
print(f"Found {len(modules)} modules")

# Load modules in batch
results = controller.load_modules_batch(modules[:5])
for result in results:
    if result['success']:
        print(f"Loaded: {result['module_name']}")
    else:
        print(f"Failed: {result['module_name']} - {result['error']}")
```

### UI Integration

```python
import tkinter as tk
from app.components.module.module_validation_ui import ModuleValidationUI
from app.components.module.module_validator import ModuleValidator

# Create main window
root = tk.Tk()
root.title("Module Validation")

# Create validator and UI
validator = ModuleValidator()
validation_ui = ModuleValidationUI(root, validator)

# Run GUI
root.mainloop()
```

## Error Handling

### Exception Types

The module interface system uses several custom exception types:

```python
class ModuleInterfaceError(Exception):
    """Base exception for module interface errors"""
    pass

class ModuleLoadError(ModuleInterfaceError):
    """Raised when module loading fails"""
    pass

class ModuleValidationError(ModuleInterfaceError):
    """Raised when module validation fails"""
    pass

class ModuleNotFoundError(ModuleInterfaceError):
    """Raised when module is not found"""
    pass

class ModuleSecurityError(ModuleInterfaceError):
    """Raised when security validation fails"""
    pass
```

### Error Handling Patterns

#### Try-Catch Pattern

```python
try:
    result = interface.load_module('module.py')
    if not result['success']:
        # Handle load failure
        logger.error(f"Module load failed: {result['error']}")
except ModuleLoadError as e:
    logger.error(f"Module load error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

#### Result-Based Pattern

```python
result = interface.load_module('module.py')
if result['success']:
    # Process successful result
    process_result(result['result'])
else:
    # Handle error
    handle_error(result['error'])
```

## Best Practices

### Module Development

1. **Include Metadata**: Always include module metadata:

   ```python
   """
   Module description
   """
   __version__ = "1.0.0"
   __author__ = "Author Name"
   __dependencies__ = ["requests", "numpy"]
   ```

2. **Error Handling**: Implement proper error handling:

   ```python
   def main():
       try:
           # Module logic here
           return {"success": True, "result": result}
       except Exception as e:
           return {"success": False, "error": str(e)}
   ```

3. **Resource Cleanup**: Always clean up resources:

   ```python
   def main():
       resource = None
       try:
           resource = acquire_resource()
           # Use resource
       finally:
           if resource:
               resource.cleanup()
   ```

### Performance Optimization

1. **Monitor Resource Usage**: Use performance monitoring to identify bottlenecks
2. **Implement Caching**: Cache frequently used modules and results
3. **Use Async Operations**: Use async loading for better performance
4. **Batch Operations**: Process multiple modules in batches when possible

### Security Considerations

1. **Validate All Modules**: Always validate modules before loading
2. **Use Security Level**: Use appropriate validation levels for different environments
3. **Monitor Permissions**: Monitor file system and network access
4. **Sandbox Execution**: Consider sandboxing for untrusted modules

### Configuration Management

1. **Environment-Specific Configs**: Use different configurations for development/production
2. **Validate Configuration**: Validate configuration values on startup
3. **Monitor Configuration Changes**: Log configuration changes for auditing
4. **Use Default Values**: Provide sensible defaults for all configuration options

### Logging and Monitoring

1. **Structured Logging**: Use structured logging for better analysis
2. **Monitor Key Metrics**: Monitor CPU, memory, and operation counts
3. **Set Up Alerts**: Configure alerts for threshold breaches
4. **Regular Audits**: Perform regular security and performance audits
