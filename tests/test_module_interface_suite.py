"""
Comprehensive Unit Test Suite for Module Interface Components

Tests all newly implemented components including:
- Module Interface Core
- Module Validator
- Performance Monitor
- Module Controller
- UI Components
"""

import unittest
import tempfile
import shutil
import os
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tkinter as tk

# Import modules to test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.module_interface import ModuleInterface, ModuleState
from app.components.module.module_validator import ModuleValidator, ValidationLevel, ValidationResult
from app.components.module.performance_monitor import PerformanceMonitor
from app.components.module.module_controller import ModuleController
from app.components.module.module_validation_ui import ModuleValidationUI
from app.components.module.performance_dashboard_ui import PerformanceDashboardUI


class TestModuleInterface(unittest.TestCase):
    """Test cases for ModuleInterface class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config = {
            'base_path': self.test_dir,
            'auto_discovery': True,
            'monitoring_enabled': True
        }
        self.interface = ModuleInterface(self.config)
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self.interface, 'cleanup'):
            self.interface.cleanup()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test module interface initialization"""
        self.assertIsNotNone(self.interface)
        self.assertEqual(self.interface.state, ModuleState.READY)
        self.assertIsNotNone(self.interface.event_manager)
        self.assertIsNotNone(self.interface.performance_monitor)
    
    def test_state_management(self):
        """Test state management functionality"""
        # Test state transitions
        initial_state = self.interface.get_state()
        self.assertEqual(initial_state, ModuleState.READY)
        
        # Test state change
        self.interface._change_state(ModuleState.LOADING)
        self.assertEqual(self.interface.get_state(), ModuleState.LOADING)
    
    def test_event_handling(self):
        """Test event handling system"""
        event_received = {'received': False}
        
        def test_handler(event_data):
            event_received['received'] = True
        
        # Register event handler
        self.interface.register_event_handler('test_event', test_handler)
        
        # Trigger event
        self.interface.trigger_event('test_event', {'test': 'data'})
        
        # Check if event was received
        time.sleep(0.1)  # Allow event processing
        self.assertTrue(event_received['received'])
    
    def test_module_discovery(self):
        """Test module discovery functionality"""
        # Create test module file
        test_module_path = os.path.join(self.test_dir, 'test_module.py')
        with open(test_module_path, 'w') as f:
            f.write("""
def main():
    return "Test module"

if __name__ == "__main__":
    main()
""")
        
        # Test discovery
        modules = self.interface.discover_modules(self.test_dir)
        self.assertIsInstance(modules, list)
    
    def test_configuration_management(self):
        """Test configuration management"""
        # Test getting configuration
        config = self.interface.get_configuration()
        self.assertIsInstance(config, dict)
        self.assertEqual(config['base_path'], self.test_dir)
        
        # Test updating configuration
        new_config = {'auto_discovery': False}
        self.interface.update_configuration(new_config)
        updated_config = self.interface.get_configuration()
        self.assertFalse(updated_config['auto_discovery'])
    
    def test_error_handling(self):
        """Test error handling mechanisms"""
        # Test with invalid module path
        result = self.interface.load_module("nonexistent_module.py")
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestModuleValidator(unittest.TestCase):
    """Test cases for ModuleValidator class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.validator = ModuleValidator()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test validator initialization"""
        self.assertIsNotNone(self.validator)
        self.assertIsInstance(self.validator.validation_rules, dict)
    
    def test_basic_validation(self):
        """Test basic module validation"""
        # Create test module
        test_module = os.path.join(self.test_dir, 'valid_module.py')
        with open(test_module, 'w') as f:
            f.write("""
def main():
    print("Hello World")

if __name__ == "__main__":
    main()
""")
        
        # Validate module
        result = self.validator.validate_module(test_module, ValidationLevel.BASIC)
        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.is_valid)
    
    def test_syntax_validation(self):
        """Test syntax validation"""
        # Create module with syntax error
        test_module = os.path.join(self.test_dir, 'invalid_syntax.py')
        with open(test_module, 'w') as f:
            f.write("""
def main(:  # Syntax error - missing parameter
    print("Hello World")
""")
        
        # Validate module
        result = self.validator.validate_module(test_module, ValidationLevel.STANDARD)
        self.assertIsInstance(result, ValidationResult)
        self.assertFalse(result.is_valid)
        self.assertTrue(any('syntax' in issue.description.lower() for issue in result.issues))
    
    def test_security_validation(self):
        """Test security validation"""
        # Create module with potential security issue
        test_module = os.path.join(self.test_dir, 'security_risk.py')
        with open(test_module, 'w') as f:
            f.write("""
import os
os.system("rm -rf /")  # Dangerous command
""")
        
        # Validate module
        result = self.validator.validate_module(test_module, ValidationLevel.SECURITY)
        self.assertIsInstance(result, ValidationResult)
        # Should flag security issues
        self.assertTrue(any(issue.severity == 'HIGH' for issue in result.issues))
    
    def test_metadata_validation(self):
        """Test metadata validation"""
        # Create module with metadata
        test_module = os.path.join(self.test_dir, 'with_metadata.py')
        with open(test_module, 'w') as f:
            f.write("""
\"\"\"
Module with metadata
\"\"\"
__version__ = "1.0.0"
__author__ = "Test Author"

def main():
    print("Hello World")
""")
        
        # Validate module
        result = self.validator.validate_module(test_module, ValidationLevel.STANDARD)
        self.assertIsInstance(result, ValidationResult)
    
    def test_batch_validation(self):
        """Test batch validation functionality"""
        # Create multiple test modules
        modules = []
        for i in range(3):
            module_path = os.path.join(self.test_dir, f'module_{i}.py')
            with open(module_path, 'w') as f:
                f.write(f"""
def main():
    print("Module {i}")
""")
            modules.append(module_path)
        
        # Batch validate
        results = self.validator.validate_batch(modules, ValidationLevel.BASIC)
        self.assertEqual(len(results), 3)
        self.assertTrue(all(isinstance(r, ValidationResult) for r in results))


class TestPerformanceMonitor(unittest.TestCase):
    """Test cases for PerformanceMonitor class"""
    
    def setUp(self):
        """Set up test environment"""
        self.monitor = PerformanceMonitor()
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self.monitor, 'stop'):
            self.monitor.stop()
    
    def test_initialization(self):
        """Test monitor initialization"""
        self.assertIsNotNone(self.monitor)
        self.assertIsInstance(self.monitor.metrics_history, list)
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        # Start monitoring
        self.monitor.start()
        time.sleep(1.1)  # Allow time for metrics collection
        
        # Get current metrics
        metrics = self.monitor.get_current_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn('cpu_percent', metrics)
        self.assertIn('memory_percent', metrics)
        self.assertIn('timestamp', metrics)
    
    def test_system_info_collection(self):
        """Test system information collection"""
        system_info = self.monitor.get_system_info()
        self.assertIsInstance(system_info, dict)
        self.assertIn('platform', system_info)
        self.assertIn('cpu_count', system_info)
    
    def test_alert_system(self):
        """Test alert system"""
        # Set low thresholds to trigger alerts
        self.monitor.update_settings({
            'cpu_threshold': 0.1,
            'memory_threshold': 0.1
        })
        
        # Start monitoring
        self.monitor.start()
        time.sleep(1.1)  # Allow time for monitoring
        
        # Check for alerts
        alerts = self.monitor.get_active_alerts()
        self.assertIsInstance(alerts, list)
    
    def test_data_export(self):
        """Test data export functionality"""
        # Start monitoring to generate some data
        self.monitor.start()
        time.sleep(1.1)
        
        # Export data
        data = self.monitor.export_data()
        self.assertIsInstance(data, dict)
        self.assertIn('metrics_history', data)
        self.assertIn('system_info', data)
    
    def test_module_tracking(self):
        """Test module performance tracking"""
        # Track a mock module
        self.monitor.track_module_operation('test_module', 'load', 0.5)
        
        # Get module metrics
        module_metrics = self.monitor.get_module_metrics('test_module')
        self.assertIsInstance(module_metrics, dict)


class TestModuleController(unittest.TestCase):
    """Test cases for ModuleController class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.controller = ModuleController(base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self.controller, 'cleanup'):
            self.controller.cleanup()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test controller initialization"""
        self.assertIsNotNone(self.controller)
        self.assertEqual(self.controller.base_path, self.test_dir)
    
    def test_module_management(self):
        """Test module management operations"""
        # Create test module
        test_module = os.path.join(self.test_dir, 'test_module.py')
        with open(test_module, 'w') as f:
            f.write("""
def main():
    return "Test module executed"

if __name__ == "__main__":
    main()
""")
        
        # Test discovery
        modules = self.controller.discover_modules()
        self.assertIsInstance(modules, list)
        
        # Test loading
        result = self.controller.load_module('test_module.py')
        self.assertIsInstance(result, dict)
    
    def test_async_operations(self):
        """Test asynchronous operations"""
        # Test async module loading
        future = self.controller.load_module_async('nonexistent.py')
        self.assertIsNotNone(future)
    
    def test_batch_operations(self):
        """Test batch operations"""
        # Create multiple test modules
        modules = []
        for i in range(3):
            module_path = os.path.join(self.test_dir, f'batch_module_{i}.py')
            with open(module_path, 'w') as f:
                f.write(f"""
def main():
    return "Batch module {i}"
""")
            modules.append(f'batch_module_{i}.py')
        
        # Test batch loading
        results = self.controller.load_modules_batch(modules)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 3)
    
    def test_configuration_management(self):
        """Test configuration management"""
        # Test getting configuration
        config = self.controller.get_configuration()
        self.assertIsInstance(config, dict)
        
        # Test updating configuration
        new_config = {'auto_discovery': False}
        self.controller.update_configuration(new_config)
        updated_config = self.controller.get_configuration()
        self.assertFalse(updated_config['auto_discovery'])


class TestUIComponents(unittest.TestCase):
    """Test cases for UI components"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
        # Create mock dependencies
        self.mock_validator = Mock(spec=ModuleValidator)
        self.mock_monitor = Mock(spec=PerformanceMonitor)
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_validation_ui_creation(self):
        """Test validation UI component creation"""
        try:
            validation_ui = ModuleValidationUI(self.root, self.mock_validator)
            self.assertIsNotNone(validation_ui)
            validation_ui.destroy()
        except Exception as e:
            self.fail(f"Failed to create validation UI: {e}")
    
    def test_performance_dashboard_creation(self):
        """Test performance dashboard creation"""
        try:
            dashboard = PerformanceDashboardUI(self.root, self.mock_monitor)
            self.assertIsNotNone(dashboard)
            dashboard.destroy()
        except Exception as e:
            self.fail(f"Failed to create performance dashboard: {e}")


class TestIntegration(unittest.TestCase):
    """Integration tests for all components working together"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test module
        self.test_module = os.path.join(self.test_dir, 'integration_test.py')
        with open(self.test_module, 'w') as f:
            f.write("""
def main():
    return "Integration test module"

if __name__ == "__main__":
    main()
""")
        
        # Initialize components
        self.validator = ModuleValidator()
        self.monitor = PerformanceMonitor()
        self.controller = ModuleController(base_path=self.test_dir)
        
        config = {
            'base_path': self.test_dir,
            'auto_discovery': True,
            'monitoring_enabled': True
        }
        self.interface = ModuleInterface(config)
    
    def tearDown(self):
        """Clean up integration test environment"""
        # Clean up components
        for component in [self.interface, self.monitor, self.controller]:
            if hasattr(component, 'cleanup'):
                component.cleanup()
            if hasattr(component, 'stop'):
                component.stop()
        
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_module_workflow(self):
        """Test complete module workflow"""
        # 1. Discover modules
        modules = self.controller.discover_modules()
        self.assertTrue(len(modules) > 0)
        
        # 2. Validate discovered module
        result = self.validator.validate_module(self.test_module, ValidationLevel.STANDARD)
        self.assertTrue(result.is_valid)
        
        # 3. Load module through interface
        load_result = self.interface.load_module('integration_test.py')
        self.assertIsInstance(load_result, dict)
        
        # 4. Check performance monitoring
        self.monitor.start()
        time.sleep(1.1)
        metrics = self.monitor.get_current_metrics()
        self.assertIsInstance(metrics, dict)
    
    def test_error_propagation(self):
        """Test error handling across components"""
        # Test with invalid module
        invalid_module = os.path.join(self.test_dir, 'invalid.py')
        with open(invalid_module, 'w') as f:
            f.write("invalid python syntax !!!")
        
        # Validation should catch syntax error
        result = self.validator.validate_module(invalid_module, ValidationLevel.BASIC)
        self.assertFalse(result.is_valid)
        
        # Interface should handle load failure gracefully
        load_result = self.interface.load_module('invalid.py')
        self.assertFalse(load_result['success'])
    
    def test_configuration_consistency(self):
        """Test configuration consistency across components"""
        # Update configuration in interface
        new_config = {'monitoring_enabled': False}
        self.interface.update_configuration(new_config)
        
        # Verify configuration is consistent
        interface_config = self.interface.get_configuration()
        self.assertFalse(interface_config['monitoring_enabled'])


class TestSuite:
    """Main test suite class"""
    
    @staticmethod
    def create_suite():
        """Create comprehensive test suite"""
        suite = unittest.TestSuite()
        
        # Add test cases
        test_classes = [
            TestModuleInterface,
            TestModuleValidator,
            TestPerformanceMonitor,
            TestModuleController,
            TestUIComponents,
            TestIntegration
        ]
        
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        return suite
    
    @staticmethod
    def run_tests(verbosity=2):
        """Run all tests with specified verbosity"""
        suite = TestSuite.create_suite()
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        
        return result
    
    @staticmethod
    def run_specific_test(test_class_name, test_method=None):
        """Run specific test class or method"""
        # Map test class names to classes
        test_classes = {
            'ModuleInterface': TestModuleInterface,
            'ModuleValidator': TestModuleValidator,
            'PerformanceMonitor': TestPerformanceMonitor,
            'ModuleController': TestModuleController,
            'UIComponents': TestUIComponents,
            'Integration': TestIntegration
        }
        
        if test_class_name not in test_classes:
            print(f"Unknown test class: {test_class_name}")
            return None
        
        test_class = test_classes[test_class_name]
        
        if test_method:
            suite = unittest.TestSuite()
            suite.addTest(test_class(test_method))
        else:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result


def main():
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Module Interface Test Suite')
    parser.add_argument('--test-class', help='Run specific test class')
    parser.add_argument('--test-method', help='Run specific test method')
    parser.add_argument('--verbosity', type=int, default=2, help='Test verbosity level')
    
    args = parser.parse_args()
    
    if args.test_class:
        result = TestSuite.run_specific_test(args.test_class, args.test_method)
    else:
        result = TestSuite.run_tests(args.verbosity)
    
    # Print summary
    if result:
        print(f"\nTests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
        
        success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
        print(f"\nSuccess rate: {success_rate:.1f}%")
        
        return len(result.failures) + len(result.errors) == 0
    
    return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
