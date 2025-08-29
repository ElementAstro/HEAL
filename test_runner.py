#!/usr/bin/env python3
"""
Simple test runner to validate the test structure without pytest.
This script will import and validate the test modules to ensure they're properly structured.
"""

import sys
import os
import importlib
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Create a simple test framework
class SimpleTestRunner:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def assert_equal(self, actual, expected, message=""):
        self.tests_run += 1
        if actual == expected:
            self.tests_passed += 1
            print(f"  ✓ PASS: {message or f'{actual} == {expected}'}")
        else:
            self.tests_failed += 1
            failure_msg = f"FAIL: {message or f'{actual} != {expected}'}"
            self.failures.append(failure_msg)
            print(f"  ✗ {failure_msg}")

    def assert_not_none(self, value, message=""):
        self.tests_run += 1
        if value is not None:
            self.tests_passed += 1
            print(f"  ✓ PASS: {message or 'Value is not None'}")
        else:
            self.tests_failed += 1
            failure_msg = f"FAIL: {message or 'Value is None'}"
            self.failures.append(failure_msg)
            print(f"  ✗ {failure_msg}")

    def assert_true(self, condition, message=""):
        self.tests_run += 1
        if condition:
            self.tests_passed += 1
            print(f"  ✓ PASS: {message or 'Condition is True'}")
        else:
            self.tests_failed += 1
            failure_msg = f"FAIL: {message or 'Condition is False'}"
            self.failures.append(failure_msg)
            print(f"  ✗ {failure_msg}")

    def print_summary(self):
        print(f"\n📊 TEST SUMMARY:")
        print(f"Tests run: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        if self.failures:
            print(f"\n❌ FAILURES:")
            for failure in self.failures:
                print(f"  - {failure}")
        return self.tests_failed == 0

# Mock external dependencies
sys.modules['loguru'] = Mock()
sys.modules['aiofiles'] = Mock()
sys.modules['aiohttp'] = Mock()
sys.modules['asyncio'] = Mock()
sys.modules['jsonschema'] = Mock()
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtNetwork'] = Mock()
sys.modules['PySide6.QtGui'] = Mock()
sys.modules['qfluentwidgets'] = Mock()
sys.modules['requests'] = Mock()
sys.modules['psutil'] = Mock()
sys.modules['watchdog'] = Mock()
sys.modules['yaml'] = Mock()
sys.modules['toml'] = Mock()

def discover_test_files():
    """Discover all test files in the tests directory"""
    test_files = []
    tests_dir = Path("tests")

    for test_file in tests_dir.rglob("test_*.py"):
        if test_file.name != "__init__.py":
            # Convert path to module name
            try:
                module_path = str(test_file).replace(os.sep, ".").replace(".py", "")
                test_files.append((test_file, module_path))
            except Exception as e:
                print(f"Warning: Could not process {test_file}: {e}")
                continue

    return test_files

def validate_test_module(test_file, module_name):
    """Validate that a test module can be imported and has test classes"""
    try:
        print(f"Validating {test_file}...")
        
        # Import the module
        module = importlib.import_module(module_name)
        
        # Check for test classes
        test_classes = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                attr_name.startswith('Test') and 
                attr.__module__ == module_name):
                test_classes.append(attr_name)
        
        # Check for test methods in classes
        test_methods = []
        for class_name in test_classes:
            test_class = getattr(module, class_name)
            for method_name in dir(test_class):
                if method_name.startswith('test_'):
                    test_methods.append(f"{class_name}.{method_name}")
        
        print(f"  ✓ Module imported successfully")
        print(f"  ✓ Found {len(test_classes)} test classes: {test_classes}")
        print(f"  ✓ Found {len(test_methods)} test methods")
        
        return True, len(test_classes), len(test_methods)
        
    except Exception as e:
        print(f"  ✗ Error importing {module_name}: {e}")
        return False, 0, 0

def main():
    """Main test validation function"""
    print("🧪 HEAL Test Structure Validation")
    print("=" * 50)
    
    test_files = discover_test_files()
    print(f"Found {len(test_files)} test files")
    print()
    
    total_classes = 0
    total_methods = 0
    successful_imports = 0
    failed_imports = 0
    
    for test_file, module_name in test_files:
        success, classes, methods = validate_test_module(test_file, module_name)
        
        if success:
            successful_imports += 1
            total_classes += classes
            total_methods += methods
        else:
            failed_imports += 1
        
        print()
    
    print("=" * 50)
    print("📊 VALIDATION SUMMARY")
    print(f"✓ Successful imports: {successful_imports}")
    print(f"✗ Failed imports: {failed_imports}")
    print(f"📁 Total test classes: {total_classes}")
    print(f"🧪 Total test methods: {total_methods}")
    
    if failed_imports == 0:
        print("\n🎉 All test modules imported successfully!")
        print("The test structure is properly organized and ready for use.")
    else:
        print(f"\n⚠️  {failed_imports} modules failed to import.")
        print("Please check the error messages above for details.")
    
    return failed_imports == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
