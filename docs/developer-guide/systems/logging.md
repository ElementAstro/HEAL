# Logging System Guide

Comprehensive guide to HEAL's unified logging system, including architecture, integration, and optimization.

## Overview

HEAL uses a comprehensive logging system based on loguru that provides structured logging, performance monitoring, and unified log management across all components.

## System Architecture

### Core Components

#### Loguru-Based Foundation

- **High-performance logging** with structured output
- **Automatic log rotation** and archiving
- **Multi-level filtering** and configuration
- **Correlation ID tracking** for cross-component request tracing
- **Structured logging** for downloads, network, performance, and exceptions

#### Unified Log Panel UI

Complete log management interface consisting of:

- **LogPanel** - Main log panel with real-time statistics and health monitoring
- **LogViewer** - Multi-tab log viewer with syntax highlighting
- **LogFilter** - Advanced filtering (level, time, module, keywords, regex)
- **LogExporter** - Multi-format export (TXT, CSV, JSON, compressed)
- **LogIntegrationManager** - Integration with existing log components

### Integration Points

#### Main Interface Components

- **Home Interface** (`app/home_interface.py`)
  - Server start/stop operation logging
  - Process state change logging
  - Performance monitoring decorators
  - Correlation ID tracking

- **Launcher Interface** (`app/launcher_interface.py`)
  - Interface initialization logging

- **Main Navigation** (`app/components/main/navigation_manager.py`)
  - Log management interface entry point
  - Navigation operation logging

#### Business Components

- **Download Interface** (`app/download_interface.py`) - Integrated
- **Module Interface** (`app/module_interface.py`) - Integrated
- **Environment Interface** (`app/environment_interface.py`) - Integrated

#### Tool Components

- **Nginx Configurator** (`app/components/tools/nginx.py`) - Integrated
- **Telescope Manager** (`app/components/tools/telescope.py`) - New logging added
- **JSON Editor** (`app/components/tools/editor.py`) - New logging added

#### Core Components

- **Resource Manager** (`app/common/resource_manager.py`) - Integrated
- **Exception Handler** (`app/common/exception_handler.py`) - Integrated

## Configuration

### Basic Configuration

```python
from heal.common.logging_config import setup_logging, get_logger

# Initialize logging system
setup_logging()

# Get logger for your component
logger = get_logger('component_name')
```

### Advanced Configuration

```python
# Configure with custom settings
setup_logging(
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    format="{time} | {level} | {name} | {message}"
)
```

### Environment Variables

```bash
# Set log level
export HEAL_LOG_LEVEL=DEBUG

# Set log file location
export HEAL_LOG_FILE=/path/to/logs/heal.log

# Enable correlation tracking
export HEAL_CORRELATION_TRACKING=true
```

## Usage Patterns

### Basic Logging

```python
from heal.common.logging_config import get_logger

logger = get_logger(__name__)

def my_function():
    logger.info("Function started")
    try:
        # Your code here
        result = perform_operation()
        logger.success("Operation completed successfully")
        return result
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise
```

### Structured Logging

```python
# Log with structured data
logger.info("User action", extra={
    "user_id": user.id,
    "action": "download_start",
    "file_name": filename,
    "file_size": size
})

# Performance logging
with logger.contextualize(operation="file_processing"):
    logger.info("Processing started")
    process_file(filename)
    logger.info("Processing completed")
```

### Correlation ID Tracking

```python
from heal.common.logging_config import with_correlation_id

@with_correlation_id
def process_request(request_data):
    logger.info("Request processing started")
    # All logs in this context will have the same correlation ID
    result = handle_request(request_data)
    logger.info("Request processing completed")
    return result
```

## Performance Optimization

### Caching System

- **High-performance cache** with TTL and LRU eviction
- **Thread-safe operations** using QMutex for concurrent access
- **Intelligent cache management** with configurable size limits
- **Cache statistics** for monitoring hit rates and performance
- **Batch operations** to reduce I/O overhead

### Benefits

- ⚡ **90%+ faster** access to frequently used log data
- 🔄 **Reduced I/O** by caching frequently accessed log entries
- 📊 **Real-time monitoring** of cache performance and hit rates
- 🛡️ **Thread-safe** operations for concurrent log access

### Lazy Loading

- **Lazy log proxies** that load expensive operations only when needed
- **Background loading** using worker threads for non-blocking operations
- **Preloading queue** for predictive loading of commonly accessed logs

## Log Management

### Log Rotation

```python
# Configure automatic rotation
logger.add(
    "logs/heal.log",
    rotation="10 MB",  # Rotate when file reaches 10MB
    retention="30 days",  # Keep logs for 30 days
    compression="zip"  # Compress old logs
)
```

### Log Filtering

```python
# Filter by level
logger.add("debug.log", level="DEBUG")
logger.add("error.log", level="ERROR")

# Filter by module
logger.add("module.log", filter=lambda record: "module" in record["name"])
```

### Log Export

The system supports multiple export formats:

- **TXT** - Plain text format
- **CSV** - Comma-separated values
- **JSON** - Structured JSON format
- **Compressed** - ZIP archives for large log sets

## Monitoring and Health Checks

### Real-time Statistics

- Log entry counts by level
- Performance metrics
- Error rates and trends
- System health indicators

### Health Monitoring

```python
from heal.common.logging_health import LogHealthMonitor

monitor = LogHealthMonitor()
health_status = monitor.get_health_status()

if health_status.is_healthy:
    logger.info("Logging system healthy")
else:
    logger.warning(f"Logging issues detected: {health_status.issues}")
```

## Best Practices

### Logging Levels

- **DEBUG** - Detailed diagnostic information
- **INFO** - General operational messages
- **SUCCESS** - Successful operations (loguru specific)
- **WARNING** - Warning messages for potential issues
- **ERROR** - Error messages for failures
- **CRITICAL** - Critical errors that may cause system failure

### Message Formatting

```python
# Good: Structured and informative
logger.info("File downloaded", extra={
    "filename": "data.csv",
    "size_mb": 15.2,
    "duration_ms": 1250
})

# Avoid: Unstructured and vague
logger.info("File done")
```

### Performance Considerations

- Use appropriate log levels to avoid performance impact
- Leverage structured logging for better analysis
- Use correlation IDs for request tracing
- Configure appropriate rotation and retention policies

### Error Handling

```python
try:
    risky_operation()
except SpecificException as e:
    logger.error("Specific error occurred", exc_info=True, extra={
        "error_type": type(e).__name__,
        "error_details": str(e)
    })
except Exception as e:
    logger.exception("Unexpected error occurred")
    raise
```

## Troubleshooting

### Common Issues

#### High Memory Usage

- Check log retention settings
- Verify rotation configuration
- Monitor cache size limits

#### Performance Issues

- Review log level configuration
- Check for excessive logging in tight loops
- Verify async logging is enabled

#### Missing Logs

- Verify logger initialization
- Check file permissions
- Confirm log level settings

### Debugging Tips

- Enable DEBUG level temporarily for detailed diagnostics
- Use correlation IDs to trace request flows
- Monitor log statistics for performance insights
- Check log health status regularly

## Migration from Old Logging

### Legacy System Replacement

The new logging system replaces the previous logging implementation with:

- Unified loguru-based architecture
- Structured logging capabilities
- Enhanced performance and reliability
- Comprehensive UI for log management

### Migration Steps

1. Replace old logging imports with new logging_config
2. Update log calls to use structured format
3. Configure appropriate log levels and rotation
4. Test logging functionality thoroughly

## API Reference

### Core Functions

- `setup_logging()` - Initialize the logging system
- `get_logger(name)` - Get a logger instance
- `with_correlation_id` - Decorator for correlation tracking

### Configuration Options

- Log levels, rotation, retention
- Output formats and destinations
- Performance and caching settings
- Health monitoring configuration

## See Also

- [Architecture Overview](../architecture/overview.md) - System architecture
- [Performance Guide](../../deployment/monitoring.md) - Performance monitoring
- [Configuration Reference](../../reference/configuration-reference.md) - All settings
