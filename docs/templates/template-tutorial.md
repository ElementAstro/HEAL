# Tutorial: [Tutorial Title]

Learn how to [specific learning objective] in this step-by-step tutorial. By the end, you'll be able to [specific outcome].

## What You'll Learn

- [ ] [Learning objective 1]
- [ ] [Learning objective 2]
- [ ] [Learning objective 3]
- [ ] [Learning objective 4]

## Prerequisites

Before starting this tutorial, you should have:

### Required Knowledge

- Basic understanding of [concept 1]
- Familiarity with [concept 2]
- Experience with [tool/language]

### Required Setup

- HEAL installed and running
- [Specific software/tools needed]
- [Access to specific resources]

### Estimated Time

⏱️ **Total Time:** [X] minutes

- Setup: [X] minutes
- Main tutorial: [X] minutes
- Optional extensions: [X] minutes

## Overview

Brief overview of what we'll build or accomplish:

- What the final result will look like
- Key concepts we'll explore
- Real-world applications

## Step 1: [Initial Setup/Preparation]

### Goal

Explain what we're accomplishing in this step.

### Instructions

1. **[Specific action]**

   ```bash
   # Command to run
   command --option value
   ```

   **Expected output:**

   ```
   Expected command output here
   ```

2. **[Next action]**

   Navigate to the appropriate location and perform the action.

   > **Note:** Important information about this step.

3. **[Verification step]**

   Verify that the step completed successfully by checking [specific indicator].

### Checkpoint ✅

At this point, you should have:

- [ ] [Specific achievement 1]
- [ ] [Specific achievement 2]

**Troubleshooting:**

- **Issue:** Common problem that might occur
  **Solution:** How to resolve it

## Step 2: [Main Implementation]

### Goal

Explain the main objective of this step.

### Code Implementation

Create a new file called `example.py`:

```python
# example.py
from heal.components import ComponentName

class TutorialExample:
    """Example class for tutorial demonstration."""
    
    def __init__(self, config: dict):
        self.config = config
        self.component = ComponentName(config)
    
    def process_data(self, data: str) -> str:
        """Process input data and return result."""
        # Step-by-step implementation
        processed = self.component.transform(data)
        return processed

# Usage example
if __name__ == "__main__":
    config = {
        "setting1": "value1",
        "setting2": "value2"
    }
    
    example = TutorialExample(config)
    result = example.process_data("sample input")
    print(f"Result: {result}")
```

### Explanation

Let's break down what this code does:

1. **Import statement** - We import the necessary component
2. **Class definition** - Create a class to encapsulate our functionality
3. **Initialization** - Set up the component with configuration
4. **Processing method** - Implement the main logic
5. **Usage example** - Demonstrate how to use the class

### Running the Code

Execute the script:

```bash
python example.py
```

**Expected output:**

```
Result: [processed sample input]
```

### Checkpoint ✅

You should now have:

- [ ] Working example script
- [ ] Successful execution
- [ ] Expected output displayed

## Step 3: [Enhancement/Extension]

### Goal

Add additional functionality to demonstrate more advanced concepts.

### Enhanced Implementation

Modify your `example.py` file to include error handling and logging:

```python
import logging
from typing import Optional
from heal.components import ComponentName
from heal.common.exceptions import HealException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTutorialExample:
    """Enhanced example with error handling and logging."""
    
    def __init__(self, config: dict):
        self.config = config
        try:
            self.component = ComponentName(config)
            logger.info("Component initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize component: {e}")
            raise
    
    def process_data(self, data: str) -> Optional[str]:
        """Process input data with error handling."""
        try:
            logger.info(f"Processing data: {data[:50]}...")
            
            # Validate input
            if not data or not isinstance(data, str):
                raise ValueError("Input data must be a non-empty string")
            
            # Process data
            processed = self.component.transform(data)
            logger.info("Data processed successfully")
            return processed
            
        except HealException as e:
            logger.error(f"HEAL-specific error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def batch_process(self, data_list: list) -> list:
        """Process multiple data items."""
        results = []
        for i, data in enumerate(data_list):
            logger.info(f"Processing item {i+1}/{len(data_list)}")
            result = self.process_data(data)
            results.append(result)
        return results

# Enhanced usage example
if __name__ == "__main__":
    config = {
        "setting1": "value1",
        "setting2": "value2",
        "debug": True
    }
    
    example = EnhancedTutorialExample(config)
    
    # Single item processing
    result = example.process_data("sample input")
    if result:
        print(f"Single result: {result}")
    
    # Batch processing
    data_list = ["input1", "input2", "input3"]
    results = example.batch_process(data_list)
    print(f"Batch results: {results}")
```

### New Features Explained

The enhanced version adds:

1. **Logging** - Track what's happening during execution
2. **Error handling** - Gracefully handle various error conditions
3. **Input validation** - Ensure data meets requirements
4. **Batch processing** - Handle multiple items efficiently

### Checkpoint ✅

Your enhanced implementation should have:

- [ ] Proper error handling
- [ ] Logging output
- [ ] Input validation
- [ ] Batch processing capability

## Step 4: [Testing and Validation]

### Goal

Verify that our implementation works correctly and handles edge cases.

### Create Test Cases

Create a test file `test_example.py`:

```python
import pytest
from example import EnhancedTutorialExample

class TestTutorialExample:
    """Test cases for tutorial example."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "setting1": "test_value1",
            "setting2": "test_value2"
        }
        self.example = EnhancedTutorialExample(self.config)
    
    def test_basic_processing(self):
        """Test basic data processing."""
        result = self.example.process_data("test input")
        assert result is not None
        assert isinstance(result, str)
    
    def test_empty_input(self):
        """Test handling of empty input."""
        result = self.example.process_data("")
        assert result is None
    
    def test_batch_processing(self):
        """Test batch processing functionality."""
        data_list = ["input1", "input2", "input3"]
        results = self.example.batch_process(data_list)
        assert len(results) == len(data_list)
```

### Run Tests

Execute the tests:

```bash
pytest test_example.py -v
```

**Expected output:**

```
test_example.py::TestTutorialExample::test_basic_processing PASSED
test_example.py::TestTutorialExample::test_empty_input PASSED
test_example.py::TestTutorialExample::test_batch_processing PASSED
```

### Checkpoint ✅

Your tests should:

- [ ] All pass successfully
- [ ] Cover basic functionality
- [ ] Test error conditions
- [ ] Validate batch processing

## What You've Accomplished

Congratulations! You've successfully:

- ✅ [Achievement 1 from learning objectives]
- ✅ [Achievement 2 from learning objectives]
- ✅ [Achievement 3 from learning objectives]
- ✅ [Achievement 4 from learning objectives]

## Next Steps

Now that you've completed this tutorial, you can:

### Immediate Next Steps

1. **Experiment** with different configuration options
2. **Modify** the code to handle your specific use case
3. **Integrate** this pattern into your own projects

### Advanced Learning

- [Related Tutorial](advanced-tutorial.md) - Build on these concepts
- [Developer Guide](../developer-guide/component-development.md) - Deep dive into development
- [API Reference](../developer-guide/api-reference/) - Complete API documentation

### Community Resources

- [Examples Repository](https://github.com/ElementAstro/HEAL/tree/main/examples) - More examples
- [Discussion Forum](https://github.com/ElementAstro/HEAL/discussions) - Ask questions
- [Issue Tracker](https://github.com/ElementAstro/HEAL/issues) - Report problems

## Troubleshooting

### Common Issues

#### Issue: Import Error

**Error message:** `ModuleNotFoundError: No module named 'heal'`
**Solution:** Ensure HEAL is properly installed:

```bash
pip install heal
# or for development
pip install -e .
```

#### Issue: Configuration Error

**Error message:** `Configuration validation failed`
**Solution:** Check your configuration dictionary matches the expected format:

```python
config = {
    "setting1": "string_value",
    "setting2": "another_string",
    "debug": True  # boolean value
}
```

### Getting Help

If you encounter issues not covered here:

1. Check the [troubleshooting guide](../user-guide/troubleshooting.md)
2. Search existing [GitHub issues](https://github.com/ElementAstro/HEAL/issues)
3. Create a new issue with:
   - Your code
   - Error messages
   - System information
   - Steps to reproduce

## Feedback

Help us improve this tutorial:

- **Found an error?** [Report it](https://github.com/ElementAstro/HEAL/issues)
- **Have suggestions?** [Share them](https://github.com/ElementAstro/HEAL/discussions)
- **Want more tutorials?** [Request them](https://github.com/ElementAstro/HEAL/issues)

---

**Tutorial Version:** [Version]  
**Last Updated:** [Date]  
**Difficulty Level:** [Beginner/Intermediate/Advanced]  
**Estimated Completion Time:** [X] minutes
