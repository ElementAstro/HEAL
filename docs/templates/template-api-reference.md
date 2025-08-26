# [Module/Package] API Reference

Brief description of the module or package and its primary purpose. Include version information and compatibility notes.

## Overview

### Module Purpose

Explain what this module provides and its role in the larger system.

### Import Statement

```python
from heal.module_name import ClassName, function_name
# or
import heal.module_name as module
```

### Quick Example

```python
# Basic usage example
from heal.module_name import MainClass

instance = MainClass(config="example")
result = instance.process("data")
print(result)
```

## Classes

### `ClassName`

Brief description of the class and its primary responsibility.

**Inheritance:** `BaseClass` → `ClassName`

#### Constructor

```python
def __init__(
    self,
    required_param: str,
    optional_param: int = 10,
    *args,
    **kwargs
) -> None
```

**Parameters:**

- `required_param` (str): Description of required parameter
- `optional_param` (int, optional): Description with default value. Defaults to 10.
- `*args`: Additional positional arguments passed to parent class
- `**kwargs`: Additional keyword arguments

**Raises:**

- `ValueError`: When required_param is empty or invalid
- `TypeError`: When optional_param is not an integer

**Example:**

```python
# Basic initialization
instance = ClassName("required_value")

# With optional parameters
instance = ClassName("required_value", optional_param=20)
```

#### Properties

##### `property_name`

```python
@property
def property_name(self) -> str
```

**Returns:** `str` - Description of what the property returns

**Example:**

```python
instance = ClassName("test")
print(instance.property_name)  # Output: "test_processed"
```

#### Methods

##### `public_method()`

```python
def public_method(
    self,
    param1: str,
    param2: Optional[List[str]] = None,
    **options
) -> Dict[str, Any]
```

**Description:** Detailed description of what the method does and when to use it.

**Parameters:**

- `param1` (str): Description of first parameter
- `param2` (List[str], optional): Description of optional parameter. Defaults to None.
- `**options`: Additional options:
  - `timeout` (int): Operation timeout in seconds
  - `retry` (bool): Whether to retry on failure

**Returns:** `Dict[str, Any]` - Dictionary containing:

- `success` (bool): Whether operation succeeded
- `data` (Any): Result data if successful
- `error` (str): Error message if failed

**Raises:**

- `ConnectionError`: When unable to connect to required service
- `TimeoutError`: When operation exceeds timeout
- `ValueError`: When param1 contains invalid characters

**Example:**

```python
instance = ClassName("config")

# Basic usage
result = instance.public_method("input_data")
if result["success"]:
    print(f"Result: {result['data']}")

# With options
result = instance.public_method(
    "input_data",
    param2=["option1", "option2"],
    timeout=30,
    retry=True
)
```

##### `async_method()`

```python
async def async_method(self, data: bytes) -> AsyncIterator[str]
```

**Description:** Asynchronous method that processes data in chunks.

**Parameters:**

- `data` (bytes): Binary data to process

**Yields:** `str` - Processed data chunks

**Raises:**

- `asyncio.TimeoutError`: When processing takes too long
- `ProcessingError`: When data cannot be processed

**Example:**

```python
import asyncio

async def process_data():
    instance = ClassName("config")
    data = b"binary_data_here"
    
    async for chunk in instance.async_method(data):
        print(f"Processed chunk: {chunk}")

# Run the async function
asyncio.run(process_data())
```

## Functions

### `standalone_function()`

```python
def standalone_function(
    input_data: Union[str, bytes],
    format_type: Literal["json", "xml", "yaml"] = "json",
    validate: bool = True
) -> Tuple[bool, Optional[Dict[str, Any]]]
```

**Description:** Processes input data and returns formatted result.

**Parameters:**

- `input_data` (Union[str, bytes]): Data to process, accepts string or bytes
- `format_type` (Literal["json", "xml", "yaml"]): Output format. Defaults to "json".
- `validate` (bool): Whether to validate input. Defaults to True.

**Returns:** `Tuple[bool, Optional[Dict[str, Any]]]` - Tuple containing:

- Success status (bool)
- Processed data dictionary (None if failed)

**Raises:**

- `ValidationError`: When validate=True and input is invalid
- `FormatError`: When format_type is not supported

**Example:**

```python
# Basic usage
success, data = standalone_function("input_string")
if success:
    print(f"Processed: {data}")

# With specific format
success, data = standalone_function(
    b"binary_input",
    format_type="xml",
    validate=False
)
```

## Constants

### Module Constants

```python
DEFAULT_TIMEOUT: int = 30
MAX_RETRIES: int = 3
SUPPORTED_FORMATS: List[str] = ["json", "xml", "yaml"]
VERSION: str = "1.0.0"
```

**Description:**

- `DEFAULT_TIMEOUT`: Default timeout for operations in seconds
- `MAX_RETRIES`: Maximum number of retry attempts
- `SUPPORTED_FORMATS`: List of supported output formats
- `VERSION`: Current module version

## Exceptions

### `ModuleException`

```python
class ModuleException(Exception):
    """Base exception for module-specific errors."""
    pass
```

Base exception class for all module-specific errors.

### `ValidationError`

```python
class ValidationError(ModuleException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field
```

**Attributes:**

- `field` (str): Name of the field that failed validation

**Example:**

```python
try:
    result = validate_input("invalid_data")
except ValidationError as e:
    print(f"Validation failed: {e}")
    if e.field:
        print(f"Field: {e.field}")
```

## Type Definitions

### Custom Types

```python
from typing import TypedDict, Union, Literal

class ConfigDict(TypedDict):
    """Configuration dictionary structure."""
    name: str
    timeout: int
    retries: int
    options: Dict[str, Any]

ProcessResult = Union[str, bytes, None]
FormatType = Literal["json", "xml", "yaml"]
```

## Usage Examples

### Basic Usage Pattern

```python
from heal.module_name import ClassName, standalone_function

# Initialize with configuration
config = {
    "name": "example",
    "timeout": 30,
    "retries": 3,
    "options": {"debug": True}
}

instance = ClassName("config_string")

# Process data
result = instance.public_method("input_data")
if result["success"]:
    print("Processing successful")
else:
    print(f"Error: {result['error']}")
```

### Advanced Usage Pattern

```python
import asyncio
from heal.module_name import ClassName

async def advanced_processing():
    """Example of advanced async usage."""
    instance = ClassName("advanced_config")
    
    try:
        # Async processing
        results = []
        async for chunk in instance.async_method(b"large_data"):
            results.append(chunk)
        
        # Combine results
        final_result = "".join(results)
        return final_result
        
    except Exception as e:
        print(f"Processing failed: {e}")
        return None

# Run advanced processing
result = asyncio.run(advanced_processing())
```

## Migration Guide

### From Version 0.x to 1.x

- `old_method()` has been renamed to `public_method()`
- `config` parameter is now required in constructor
- Return types have changed from `str` to `Dict[str, Any]`

**Migration Example:**

```python
# Old version (0.x)
instance = ClassName()
result = instance.old_method("data")

# New version (1.x)
instance = ClassName("config")
result = instance.public_method("data")
success = result["success"]
data = result["data"]
```

## See Also

- [User Guide](../user-guide/module-usage.md) - For usage instructions
- [Developer Guide](../developer-guide/module-development.md) - For development details
- [Examples Repository](https://github.com/ElementAstro/HEAL/tree/main/examples) - For more examples

---

**Module Version:** [Version]  
**Last Updated:** [Date]  
**Compatibility:** Python 3.11+, HEAL v1.0+
