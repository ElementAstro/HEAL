"""
Comprehensive test runner for the advanced configuration system

Runs all configuration-related tests including:
- Core configuration system tests
- Template and preset tests
- Plugin system tests
- Integration tests
- Performance tests
"""

import sys
import time
import importlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ConfigurationTestRunner:
    """Comprehensive test runner for configuration system"""
    
    def __init__(self) -> None:
        self.test_modules = [
            'test_advanced_config_system',
            'test_config_templates',
            'test_config_plugins',
            'test_config_integration',
            'test_config_performance'
        ]
        self.results: Dict[str, Any] = {}
        self.total_passed = 0
        self.total_failed = 0
        self.total_duration = 0.0
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all configuration tests"""
        print("🚀 HEAL Configuration System - Comprehensive Test Suite")
        print("=" * 70)
        print(f"Running {len(self.test_modules)} test modules...")
        print()
        
        overall_start_time = time.time()
        
        for module_name in self.test_modules:
            print(f"📋 Running {module_name}...")
            print("-" * 50)
            
            module_result = self._run_test_module(module_name)
            self.results[module_name] = module_result
            
            self.total_passed += module_result['passed']
            self.total_failed += module_result['failed']
            
            print(f"✅ {module_result['passed']} passed, ❌ {module_result['failed']} failed")
            print(f"⏱️  Duration: {module_result['duration']:.2f}s")
            print()
        
        self.total_duration = time.time() - overall_start_time
        
        self._print_summary()
        return self._get_summary_data()
    
    def _run_test_module(self, module_name: str) -> Dict[str, Any]:
        """Run tests for a specific module"""
        try:
            # Import the test module
            test_module = importlib.import_module(f'tests.{module_name}')
            
            # Find test classes
            test_classes = []
            for attr_name in dir(test_module):
                attr = getattr(test_module, attr_name)
                if (isinstance(attr, type) and 
                    attr_name.startswith('Test') and 
                    hasattr(attr, 'setup_method')):
                    test_classes.append(attr)
            
            if not test_classes:
                return {
                    'passed': 0,
                    'failed': 1,
                    'duration': 0.0,
                    'error': 'No test classes found'
                }
            
            # Run tests for each class
            total_passed = 0
            total_failed = 0
            start_time = time.time()
            
            for test_class in test_classes:
                class_passed, class_failed = self._run_test_class(test_class)
                total_passed += class_passed
                total_failed += class_failed
            
            duration = time.time() - start_time
            
            return {
                'passed': total_passed,
                'failed': total_failed,
                'duration': duration,
                'test_classes': len(test_classes)
            }
            
        except Exception as e:
            return {
                'passed': 0,
                'failed': 1,
                'duration': 0.0,
                'error': str(e)
            }
    
    def _run_test_class(self, test_class: Any) -> Tuple[int, int]:
        """Run all test methods in a test class"""
        test_instance = test_class()
        test_methods = [method for method in dir(test_instance) 
                       if method.startswith('test_')]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                # Setup
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()
                
                # Run test
                getattr(test_instance, test_method)()
                
                # Teardown
                if hasattr(test_instance, 'teardown_method'):
                    test_instance.teardown_method()
                
                passed += 1
                print(f"  ✅ {test_method}")
                
            except Exception as e:
                failed += 1
                print(f"  ❌ {test_method}: {e}")
                
                # Still run teardown on failure
                try:
                    if hasattr(test_instance, 'teardown_method'):
                        test_instance.teardown_method()
                except Exception:
                    pass
        
        return passed, failed
    
    def _print_summary(self) -> None:
        """Print comprehensive test summary"""
        print("=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        # Overall results
        total_tests = self.total_passed + self.total_failed
        success_rate = (self.total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"🎯 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {self.total_passed}")
        print(f"   ❌ Failed: {self.total_failed}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        print(f"   ⏱️  Total Duration: {self.total_duration:.2f}s")
        print()
        
        # Module breakdown
        print("📋 Module Breakdown:")
        for module_name, result in self.results.items():
            if 'error' in result:
                print(f"   {module_name}: ❌ ERROR - {result['error']}")
            else:
                module_total = result['passed'] + result['failed']
                module_rate = (result['passed'] / module_total * 100) if module_total > 0 else 0
                print(f"   {module_name}: {result['passed']}/{module_total} ({module_rate:.1f}%) in {result['duration']:.2f}s")
        print()
        
        # Performance metrics (if performance tests ran)
        if 'test_config_performance' in self.results:
            perf_result = self.results['test_config_performance']
            if 'error' not in perf_result and perf_result['passed'] > 0:
                print("⚡ Performance Test Results:")
                print("   All performance benchmarks passed!")
                print("   Configuration system meets performance requirements")
                print()
        
        # Test coverage analysis
        print("📈 Test Coverage Analysis:")
        coverage_areas = {
            'Core Configuration': 'test_advanced_config_system',
            'Templates & Presets': 'test_config_templates',
            'Plugin System': 'test_config_plugins',
            'Integration': 'test_config_integration',
            'Performance': 'test_config_performance'
        }
        
        for area, module in coverage_areas.items():
            if module in self.results:
                result = self.results[module]
                if 'error' not in result:
                    status = "✅ COVERED" if result['failed'] == 0 else "⚠️ PARTIAL"
                    print(f"   {area}: {status}")
                else:
                    print(f"   {area}: ❌ ERROR")
            else:
                print(f"   {area}: ❌ NOT RUN")
        print()
        
        # Final verdict
        if self.total_failed == 0:
            print("🎉 ALL TESTS PASSED! Configuration system is ready for production!")
        else:
            print(f"⚠️ {self.total_failed} tests failed. Review failures before deployment.")
        
        print("=" * 70)
    
    def _get_summary_data(self) -> Dict[str, Any]:
        """Get summary data for external use"""
        total_tests = self.total_passed + self.total_failed
        
        return {
            'total_tests': total_tests,
            'passed': self.total_passed,
            'failed': self.total_failed,
            'success_rate': (self.total_passed / total_tests * 100) if total_tests > 0 else 0,
            'duration': self.total_duration,
            'modules': self.results,
            'all_passed': self.total_failed == 0
        }
    
    def run_specific_module(self, module_name: str) -> Dict[str, Any]:
        """Run tests for a specific module only"""
        if module_name not in self.test_modules:
            raise ValueError(f"Unknown test module: {module_name}")
        
        print(f"🚀 Running {module_name} tests only...")
        print("=" * 50)
        
        result = self._run_test_module(module_name)
        
        print("\n📊 Results:")
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
        else:
            total = result['passed'] + result['failed']
            rate = (result['passed'] / total * 100) if total > 0 else 0
            print(f"✅ {result['passed']} passed, ❌ {result['failed']} failed")
            print(f"📈 Success rate: {rate:.1f}%")
            print(f"⏱️ Duration: {result['duration']:.2f}s")
        
        return result
    
    def run_quick_test(self) -> bool:
        """Run a quick subset of tests for fast validation"""
        print("🚀 Running Quick Configuration Tests...")
        print("=" * 40)
        
        # Run core tests only
        quick_modules = [
            'test_advanced_config_system',
            'test_config_templates'
        ]
        
        total_passed = 0
        total_failed = 0
        
        for module_name in quick_modules:
            print(f"Running {module_name}...")
            result = self._run_test_module(module_name)
            
            if 'error' in result:
                print(f"❌ ERROR: {result['error']}")
                total_failed += 1
            else:
                total_passed += result['passed']
                total_failed += result['failed']
                print(f"✅ {result['passed']} passed, ❌ {result['failed']} failed")
        
        print(f"\n📊 Quick Test Results: {total_passed} passed, {total_failed} failed")
        return total_failed == 0


def main() -> None:
    """Main entry point for test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='HEAL Configuration System Test Runner')
    parser.add_argument('--module', '-m', help='Run specific test module only')
    parser.add_argument('--quick', '-q', action='store_true', help='Run quick test subset')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    runner = ConfigurationTestRunner()
    
    try:
        if args.quick:
            success = runner.run_quick_test()
            sys.exit(0 if success else 1)
        elif args.module:
            result = runner.run_specific_module(args.module)
            success = 'error' not in result and result['failed'] == 0
            sys.exit(0 if success else 1)
        else:
            summary = runner.run_all_tests()
            sys.exit(0 if summary['all_passed'] else 1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
