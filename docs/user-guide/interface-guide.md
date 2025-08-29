# Module Interface User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Module Validation](#module-validation)
4. [Performance Monitoring](#performance-monitoring)
5. [User Interface Guide](#user-interface-guide)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Required dependencies (see requirements.txt)
- Basic understanding of Python modules

### Installation

The Module Interface is part of the HEAL application. To use it:

1. Ensure all dependencies are installed:

   ```bash
   pip install -r requirements.txt
   ```

2. Import the required components:

   ```python
   from src.heal.interfaces.module_interface import Module
   ```

### Quick Start

```python
from src.heal.interfaces.module_interface import Module

# Create configuration
config = {
    'base_path': '/path/to/your/modules',
    'auto_discovery': True,
    'monitoring_enabled': True
}

# Initialize interface
interface = ModuleInterface(config)

# Load and run a module
result = interface.load_module('my_module.py')
print(result)
```

## Basic Usage

### Loading Modules

#### Single Module Loading

The most basic operation is loading a single module:

```python
# Load a module
result = interface.load_module('calculator.py')

if result['success']:
    print(f"Result: {result['result']}")
    print(f"Execution time: {result['execution_time']:.2f}s")
else:
    print(f"Error: {result['error']}")
```

#### Module with Parameters

You can pass parameters to modules:

```python
result = interface.load_module('calculator.py', 
                              operation='add', 
                              x=10, 
                              y=5)
```

### Module Discovery

Find all available modules in a directory:

```python
# Discover modules in default path
modules = interface.discover_modules()
print(f"Found {len(modules)} modules:")
for module in modules:
    print(f"  - {module}")

# Discover modules in specific path
modules = interface.discover_modules('/custom/path')
```

### Getting Module Information

Get detailed information about a module before loading:

```python
info = interface.get_module_info('my_module.py')
print(f"Module: {info['name']}")
print(f"Version: {info['version']}")
print(f"Author: {info['author']}")
print(f"Dependencies: {info['dependencies']}")
```

### Configuration Management

#### Getting Current Configuration

```python
config = interface.get_configuration()
print(f"Base path: {config['base_path']}")
print(f"Auto discovery: {config['auto_discovery']}")
```

#### Updating Configuration

```python
# Update specific settings
interface.update_configuration({
    'auto_discovery': False,
    'monitoring_enabled': True,
    'validation_level': 'strict'
})
```

## Module Validation

### Understanding Validation Levels

The Module Interface provides four validation levels:

1. **Basic**: Syntax checking and basic structure validation
2. **Standard**: Basic validation + dependency checking
3. **Strict**: Standard validation + best practices enforcement
4. **Security**: All validations + security vulnerability scanning

### Validating a Single Module

```python
from app.components.module.module_validator import ModuleValidator, ValidationLevel

# Create validator
validator = ModuleValidator()

# Validate with standard level
result = validator.validate_module('my_module.py', ValidationLevel.STANDARD)

print(f"Valid: {result.is_valid}")
print(f"Issues found: {len(result.issues)}")

# Display issues
for issue in result.issues:
    print(f"{issue.severity}: {issue.description}")
    if issue.suggestion:
        print(f"  Suggestion: {issue.suggestion}")
```

### Batch Validation

Validate multiple modules at once:

```python
modules = ['module1.py', 'module2.py', 'module3.py']
results = validator.validate_batch(modules, ValidationLevel.SECURITY)

for i, result in enumerate(results):
    print(f"\nModule: {modules[i]}")
    print(f"Valid: {result.is_valid}")
    if not result.is_valid:
        for issue in result.issues:
            print(f"  {issue.severity}: {issue.description}")
```

### Security Validation

For security-critical environments, use security validation:

```python
# Security validation
result = validator.validate_module('module.py', ValidationLevel.SECURITY)

# Check for security issues specifically
security_issues = [issue for issue in result.issues 
                  if issue.category == 'security']

if security_issues:
    print("Security issues found:")
    for issue in security_issues:
        print(f"  {issue.severity}: {issue.description}")
```

### Understanding Validation Results

Validation results include:

- **is_valid**: Boolean indicating if module passed validation
- **issues**: List of problems found
- **metadata**: Extracted module information
- **execution_time**: Time taken for validation
- **validation_level**: Level used for validation

Issue severities:

- **LOW**: Minor issues, warnings
- **MEDIUM**: Moderate issues that should be addressed
- **HIGH**: Serious issues that may cause problems
- **CRITICAL**: Critical security or functionality issues

## Performance Monitoring

### Starting Performance Monitoring

```python
from app.components.module.performance_monitor import PerformanceMonitor

# Create and start monitor
monitor = PerformanceMonitor()
monitor.start()

# Monitor will now collect metrics in the background
```

### Getting Current Metrics

```python
metrics = monitor.get_current_metrics()
print(f"CPU Usage: {metrics['cpu_percent']:.1f}%")
print(f"Memory Usage: {metrics['memory_percent']:.1f}%")
print(f"Active Modules: {metrics['active_modules']}")
print(f"Total Operations: {metrics['total_operations']}")
print(f"Error Rate: {metrics['error_rate']:.2f}%")
```

### Tracking Module Operations

Track specific module operations:

```python
# Track module execution
start_time = time.time()
result = interface.load_module('heavy_module.py')
duration = time.time() - start_time

monitor.track_module_operation('heavy_module', 'execute', duration)
```

### Setting Up Alerts

Configure performance alerts:

```python
# Update alert thresholds
monitor.update_settings({
    'cpu_threshold': 80.0,      # Alert when CPU > 80%
    'memory_threshold': 85.0,   # Alert when memory > 85%
    'enable_alerts': True
})

# Check for active alerts
alerts = monitor.get_active_alerts()
for alert in alerts:
    print(f"{alert['severity']}: {alert['message']}")
```

### Exporting Performance Data

```python
# Export data for analysis
data = monitor.export_data()

# Save to file
import json
with open('performance_data.json', 'w') as f:
    json.dump(data, f, indent=2, default=str)
```

## User Interface Guide

### Module Validation UI

The validation UI provides a graphical interface for module validation:

```python
import tkinter as tk
from app.components.module.module_validation_ui import ModuleValidationUI
from app.components.module.module_validator import ModuleValidator

# Create main window
root = tk.Tk()
root.title("Module Validation")
root.geometry("1000x700")

# Create validator and UI
validator = ModuleValidator()
validation_ui = ModuleValidationUI(root, validator)

# Run the interface
root.mainloop()
```

#### Using the Validation UI

1. **Select Files**: Click "Browse" to select module files
2. **Choose Validation Level**: Select from Basic, Standard, Strict, or Security
3. **Validate**: Click "Validate" to start validation
4. **View Results**: Results appear in the main panel with color-coded issues
5. **Export Results**: Use "Export" to save results to file

### Performance Dashboard UI

The performance dashboard provides real-time monitoring:

```python
import tkinter as tk
from app.components.module.performance_dashboard_ui import PerformanceDashboardUI
from app.components.module.performance_monitor import PerformanceMonitor

# Create main window
root = tk.Tk()
root.title("Performance Dashboard")
root.geometry("1200x800")

# Create monitor and dashboard
monitor = PerformanceMonitor()
dashboard = PerformanceDashboardUI(root, monitor)

# Start monitoring
monitor.start()

# Run the interface
root.mainloop()
```

#### Dashboard Features

1. **Overview Tab**: Key metrics and real-time charts
2. **System Tab**: Detailed system information and resource usage
3. **Modules Tab**: Per-module performance metrics
4. **Settings Tab**: Configure monitoring parameters and thresholds

## Advanced Features

### Asynchronous Module Loading

For better performance, use asynchronous loading:

```python
from app.components.module.module_controller import ModuleController
import concurrent.futures

controller = ModuleController('/path/to/modules')

# Load module asynchronously
future = controller.load_module_async('slow_module.py')

# Do other work while module loads
print("Module loading in background...")

# Get result when ready
result = future.result(timeout=30)
print(f"Module loaded: {result}")
```

### Batch Operations

Process multiple modules efficiently:

```python
# Load multiple modules in batch
modules = ['module1.py', 'module2.py', 'module3.py']
results = controller.load_modules_batch(modules)

for i, result in enumerate(results):
    if result['success']:
        print(f"{modules[i]}: SUCCESS")
    else:
        print(f"{modules[i]}: FAILED - {result['error']}")
```

### Dependency Resolution

Automatically resolve and load module dependencies:

```python
# Check module dependencies
deps = controller.get_module_dependencies('complex_module.py')
print(f"Dependencies: {deps}")

# Resolve and load dependencies
success = controller.resolve_dependencies('complex_module.py')
if success:
    print("All dependencies loaded successfully")
else:
    print("Failed to resolve some dependencies")
```

### Event Handling

Register for module events:

```python
def on_module_loaded(event_data):
    print(f"Module loaded: {event_data['module_name']}")
    print(f"Load time: {event_data['load_time']:.2f}s")

def on_module_error(event_data):
    print(f"Module error: {event_data['error']}")

# Register event handlers
interface.register_event_handler('module_loaded', on_module_loaded)
interface.register_event_handler('module_error', on_module_error)
```

### Custom Validation Rules

Add custom validation rules:

```python
def check_custom_rule(module_path, module_content):
    """Custom validation rule example"""
    issues = []
    
    # Check for custom requirements
    if 'dangerous_function()' in module_content:
        issues.append({
            'severity': 'HIGH',
            'category': 'custom',
            'description': 'Found dangerous function call',
            'suggestion': 'Replace with safe alternative'
        })
    
    return issues

# Add custom rule to validator
validator.add_custom_rule('dangerous_function_check', check_custom_rule)
```

## Troubleshooting

### Common Issues

#### Module Not Found

**Problem**: `ModuleNotFoundError: Could not find module 'my_module.py'`

**Solutions**:

1. Check the file path is correct
2. Ensure the module is in the configured base_path
3. Verify file permissions
4. Use `discover_modules()` to list available modules

```python
# Check available modules
modules = interface.discover_modules()
print("Available modules:", modules)
```

#### Validation Failures

**Problem**: Module fails validation unexpectedly

**Solutions**:

1. Check validation level - try with 'basic' first
2. Review validation issues for specific problems
3. Ensure module follows Python best practices

```python
# Detailed validation
result = validator.validate_module('module.py', ValidationLevel.BASIC)
for issue in result.issues:
    print(f"{issue.severity}: {issue.description}")
    print(f"Line {issue.line_number}: {issue.suggestion}")
```

#### Performance Issues

**Problem**: Module loading is slow

**Solutions**:

1. Enable performance monitoring to identify bottlenecks
2. Use asynchronous loading for multiple modules
3. Check system resources

```python
# Monitor performance
monitor.start()
result = interface.load_module('slow_module.py')
metrics = monitor.get_current_metrics()
print(f"CPU: {metrics['cpu_percent']}%, Memory: {metrics['memory_percent']}%")
```

#### Memory Issues

**Problem**: High memory usage during module operations

**Solutions**:

1. Monitor memory usage patterns
2. Implement module unloading
3. Use batch processing with smaller batches

```python
# Unload modules when done
controller.unload_module('heavy_module')

# Check loaded modules
loaded = controller.get_loaded_modules()
print(f"Currently loaded: {loaded}")
```

### Debug Mode

Enable debug mode for detailed logging:

```python
from app.common.logging_config import get_logger, get_logging_config

# Get logger for debugging
logger = get_logger(__name__)

# Configure interface for debugging
config = {
    'base_path': '/path/to/modules',
    'logging_level': 'DEBUG',
    'error_reporting': True
}
interface = ModuleInterface(config)

# Enable debug level logging
logging_config = get_logging_config()
logging_config.set_level('DEBUG')
```

### Log Analysis

Check logs for detailed error information:

```python
from app.common.logging_config import get_logger

logger = get_logger(__name__)

# Log files are typically in logs/ directory
# Check for error patterns in:
# - module_interface.log
# - performance_monitor.log
# - module_validator.log
```

## FAQ

### General Questions

**Q: What file formats are supported?**
A: Currently, only Python (.py) files are supported.

**Q: Can I load modules from remote locations?**
A: No, for security reasons only local files are supported.

**Q: How many modules can be loaded simultaneously?**
A: There's no hard limit, but performance depends on system resources.

### Configuration Questions

**Q: Where should I store my modules?**
A: Create a dedicated directory and set it as the `base_path` in configuration.

**Q: Can I change configuration at runtime?**
A: Yes, use `update_configuration()` to change settings dynamically.

**Q: What's the default validation level?**
A: Standard validation is used by default.

### Performance Questions

**Q: How often are performance metrics updated?**
A: By default, every 1 second. This can be configured.

**Q: Do performance monitors affect system performance?**
A: Minimal impact - monitoring is optimized for low overhead.

**Q: Can I export performance data?**
A: Yes, data can be exported in JSON or CSV format.

### Security Questions

**Q: Is it safe to run untrusted modules?**
A: Use Security validation level and consider sandboxing for untrusted code.

**Q: What security checks are performed?**
A: Checks include dangerous imports, function calls, file operations, and more.

**Q: Can I add custom security rules?**
A: Yes, custom validation rules can be added to the validator.

### UI Questions

**Q: Can I customize the user interface?**
A: Yes, UI components are modular and can be customized or extended.

**Q: Is the UI required to use the module interface?**
A: No, the UI is optional - all functionality is available programmatically.

**Q: Can I integrate the UI into my own application?**
A: Yes, UI components are designed to be embedded in other applications.

### Best Practices

**Q: How should I structure my modules?**
A: Include metadata, proper error handling, and follow Python conventions.

**Q: When should I use different validation levels?**
A: Use Basic for development, Standard for testing, Security for production.

**Q: How can I optimize module loading performance?**
A: Use async loading, enable caching, and monitor performance metrics.

---

For more detailed information, see the [API Documentation](module_interface_api.md) or contact the development team.
