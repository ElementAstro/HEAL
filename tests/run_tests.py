#!/usr/bin/env python3
"""
Comprehensive test runner for the HEAL onboarding system

Provides different test execution modes, reporting, and performance analysis.
"""

import sys
import os
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest


class TestRunner:
    """Comprehensive test runner for onboarding system tests"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results = {}
    
    def run_unit_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run unit tests for individual components"""
        print("🧪 Running Unit Tests...")
        
        unit_test_files = [
            "test_user_state_tracker.py",
            "test_smart_tip_system.py", 
            "test_recommendation_engine.py",
            "test_tutorial_system.py"
        ]
        
        args = ["-v"] if verbose else []
        args.extend(["-m", "unit"])
        args.extend([str(self.test_dir / f) for f in unit_test_files])
        
        start_time = time.time()
        result = pytest.main(args)
        end_time = time.time()
        
        self.results["unit_tests"] = {
            "result": result,
            "duration": end_time - start_time,
            "files": unit_test_files
        }
        
        return self.results["unit_tests"]
    
    def run_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run integration tests for system interactions"""
        print("🔗 Running Integration Tests...")
        
        integration_test_files = [
            "test_onboarding_system.py",
            "test_integration_scenarios.py"
        ]
        
        args = ["-v"] if verbose else []
        args.extend(["-m", "integration"])
        args.extend([str(self.test_dir / f) for f in integration_test_files])
        
        start_time = time.time()
        result = pytest.main(args)
        end_time = time.time()
        
        self.results["integration_tests"] = {
            "result": result,
            "duration": end_time - start_time,
            "files": integration_test_files
        }
        
        return self.results["integration_tests"]
    
    def run_performance_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run performance and benchmark tests"""
        print("⚡ Running Performance Tests...")
        
        performance_test_files = [
            "test_performance_benchmarks.py"
        ]
        
        args = ["-v", "-s"] if verbose else ["-s"]  # -s to see print output
        args.extend(["-m", "performance"])
        args.extend([str(self.test_dir / f) for f in performance_test_files])
        
        start_time = time.time()
        result = pytest.main(args)
        end_time = time.time()
        
        self.results["performance_tests"] = {
            "result": result,
            "duration": end_time - start_time,
            "files": performance_test_files
        }
        
        return self.results["performance_tests"]
    
    def run_all_tests(self, verbose: bool = False, include_performance: bool = False) -> Dict[str, Any]:
        """Run all tests"""
        print("🚀 Running All Tests...")
        
        args = ["-v"] if verbose else []
        
        if include_performance:
            args.extend([str(self.test_dir)])
        else:
            # Run all except performance tests
            args.extend(["-m", "not performance"])
            args.extend([str(self.test_dir)])
        
        start_time = time.time()
        result = pytest.main(args)
        end_time = time.time()
        
        self.results["all_tests"] = {
            "result": result,
            "duration": end_time - start_time,
            "include_performance": include_performance
        }
        
        return self.results["all_tests"]
    
    def run_specific_test(self, test_pattern: str, verbose: bool = False) -> Dict[str, Any]:
        """Run specific test by pattern"""
        print(f"🎯 Running Specific Test: {test_pattern}")
        
        args = ["-v"] if verbose else []
        args.extend(["-k", test_pattern])
        args.extend([str(self.test_dir)])
        
        start_time = time.time()
        result = pytest.main(args)
        end_time = time.time()
        
        self.results["specific_test"] = {
            "result": result,
            "duration": end_time - start_time,
            "pattern": test_pattern
        }
        
        return self.results["specific_test"]
    
    def run_coverage_analysis(self, verbose: bool = False) -> Dict[str, Any]:
        """Run tests with coverage analysis"""
        print("📊 Running Coverage Analysis...")
        
        try:
            import coverage
        except ImportError:
            print("❌ Coverage package not installed. Install with: pip install coverage")
            return {"result": 1, "error": "coverage not installed"}
        
        args = [
            "--cov=src/heal/components/onboarding",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ]
        
        if verbose:
            args.append("-v")
        
        args.extend([str(self.test_dir)])
        
        start_time = time.time()
        result = pytest.main(args)
        end_time = time.time()
        
        self.results["coverage_analysis"] = {
            "result": result,
            "duration": end_time - start_time
        }
        
        return self.results["coverage_analysis"]
    
    def generate_report(self) -> None:
        """Generate a comprehensive test report"""
        print("\n" + "="*60)
        print("📋 TEST EXECUTION REPORT")
        print("="*60)
        
        total_duration = 0
        total_tests = 0
        failed_tests = 0
        
        for test_type, result_data in self.results.items():
            duration = result_data.get("duration", 0)
            result_code = result_data.get("result", 0)
            
            total_duration += duration
            
            status = "✅ PASSED" if result_code == 0 else "❌ FAILED"
            print(f"\n{test_type.upper().replace('_', ' ')}: {status}")
            print(f"  Duration: {duration:.2f}s")
            
            if result_code != 0:
                failed_tests += 1
            
            if "files" in result_data:
                print(f"  Files: {', '.join(result_data['files'])}")
            
            if "pattern" in result_data:
                print(f"  Pattern: {result_data['pattern']}")
        
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Test Suites: {len(self.results)}")
        print(f"  Failed Suites: {failed_tests}")
        print(f"  Success Rate: {((len(self.results) - failed_tests) / len(self.results) * 100):.1f}%")
        print(f"{'='*60}")
        
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {failed_tests} TEST SUITE(S) FAILED")
    
    def run_quick_smoke_test(self) -> bool:
        """Run a quick smoke test to verify basic functionality"""
        print("💨 Running Quick Smoke Test...")
        
        smoke_tests = [
            "test_user_state_tracker.py::TestUserStateTrackerCore::test_initialization",
            "test_smart_tip_system.py::TestSmartTipSystemCore::test_system_initialization",
            "test_recommendation_engine.py::TestRecommendationEngineCore::test_engine_initialization",
            "test_tutorial_system.py::TestTutorialSystemCore::test_system_initialization"
        ]
        
        args = ["-v", "--tb=short"]
        args.extend([str(self.test_dir / test) for test in smoke_tests])
        
        result = pytest.main(args)
        
        if result == 0:
            print("✅ Smoke test passed - basic functionality working")
            return True
        else:
            print("❌ Smoke test failed - basic functionality issues detected")
            return False


def main():
    """Main entry point for test runner"""
    parser = argparse.ArgumentParser(description="HEAL Onboarding System Test Runner")
    
    parser.add_argument(
        "mode",
        choices=["unit", "integration", "performance", "all", "coverage", "smoke", "specific"],
        help="Test execution mode"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "-p", "--include-performance",
        action="store_true",
        help="Include performance tests in 'all' mode"
    )
    
    parser.add_argument(
        "-k", "--pattern",
        type=str,
        help="Test pattern for specific mode"
    )
    
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating final report"
    )
    
    args = parser.parse_args()
    
    # Set environment variable for performance tests
    if args.mode == "performance" or args.include_performance:
        os.environ["RUN_PERFORMANCE_TESTS"] = "1"
    
    runner = TestRunner()
    
    print("🧪 HEAL Onboarding System Test Runner")
    print("="*50)
    
    try:
        if args.mode == "unit":
            runner.run_unit_tests(args.verbose)
        elif args.mode == "integration":
            runner.run_integration_tests(args.verbose)
        elif args.mode == "performance":
            runner.run_performance_tests(args.verbose)
        elif args.mode == "all":
            runner.run_all_tests(args.verbose, args.include_performance)
        elif args.mode == "coverage":
            runner.run_coverage_analysis(args.verbose)
        elif args.mode == "smoke":
            success = runner.run_quick_smoke_test()
            sys.exit(0 if success else 1)
        elif args.mode == "specific":
            if not args.pattern:
                print("❌ Pattern required for specific mode. Use -k/--pattern")
                sys.exit(1)
            runner.run_specific_test(args.pattern, args.verbose)
        
        if not args.no_report and args.mode != "smoke":
            runner.generate_report()
        
        # Exit with error code if any tests failed
        failed_suites = sum(1 for result in runner.results.values() if result.get("result", 0) != 0)
        sys.exit(failed_suites)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
