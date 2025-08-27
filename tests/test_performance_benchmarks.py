"""
Performance benchmarks and stress tests for the onboarding system

Tests system performance under various load conditions, memory usage,
response times, and scalability limits.
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Any, Dict, List
import gc
import sys

from PySide6.QtWidgets import QApplication, QWidget

from src.heal.components.onboarding.onboarding_manager import OnboardingManager
from src.heal.components.onboarding.user_state_tracker import UserLevel, OnboardingStep


class TestPerformanceBenchmarks:
    """Performance benchmarks for onboarding system components"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    @pytest.fixture
    def onboarding_manager(self, main_window):
        """Create an onboarding manager for testing"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            return manager
    
    def test_initialization_performance(self, main_window):
        """Test onboarding system initialization performance"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            start_time = time.time()
            
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            end_time = time.time()
            initialization_time = end_time - start_time
            
            # Should initialize within reasonable time (adjust threshold as needed)
            assert initialization_time < 2.0, f"Initialization took {initialization_time:.2f}s, expected < 2.0s"
            
            print(f"Initialization time: {initialization_time:.3f}s")
    
    def test_action_tracking_performance(self, onboarding_manager):
        """Test performance of action tracking under load"""
        num_actions = 1000
        
        start_time = time.time()
        
        for i in range(num_actions):
            onboarding_manager.track_user_action(
                f"performance_test_action_{i % 10}",
                {"index": i, "timestamp": datetime.now().isoformat()}
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        actions_per_second = num_actions / total_time
        
        # Should handle at least 100 actions per second
        assert actions_per_second > 100, f"Only {actions_per_second:.1f} actions/sec, expected > 100"
        
        print(f"Action tracking: {actions_per_second:.1f} actions/sec")
    
    def test_recommendation_generation_performance(self, onboarding_manager):
        """Test recommendation generation performance"""
        # Generate system state that should trigger recommendations
        onboarding_manager.track_system_state({
            "cpu_usage": 85,
            "memory_usage": 80,
            "servers_configured": False,
            "performance_issues": True
        })
        
        # Track actions that should trigger recommendations
        trigger_actions = [
            "visited_home_page",
            "server_error_occurred", 
            "connection_failed",
            "performance_issue_detected"
        ]
        
        start_time = time.time()
        
        for action in trigger_actions * 10:  # Repeat to test performance
            onboarding_manager.track_user_action(action, {})
            recommendations = onboarding_manager.get_recommendations()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time
        assert total_time < 1.0, f"Recommendation generation took {total_time:.2f}s, expected < 1.0s"
        
        print(f"Recommendation generation time: {total_time:.3f}s")
    
    def test_documentation_search_performance(self, onboarding_manager):
        """Test documentation search performance"""
        search_queries = [
            "server setup",
            "configuration",
            "troubleshooting",
            "module development",
            "performance optimization",
            "connection issues",
            "getting started",
            "advanced features"
        ]
        
        start_time = time.time()
        
        for query in search_queries * 5:  # Repeat searches
            results = onboarding_manager.search_documentation(query)
            assert isinstance(results, list)
        
        end_time = time.time()
        total_time = end_time - start_time
        searches_per_second = (len(search_queries) * 5) / total_time
        
        # Should handle at least 10 searches per second
        assert searches_per_second > 10, f"Only {searches_per_second:.1f} searches/sec, expected > 10"
        
        print(f"Documentation search: {searches_per_second:.1f} searches/sec")
    
    def test_statistics_generation_performance(self, onboarding_manager):
        """Test statistics generation performance"""
        # Generate some activity first
        for i in range(100):
            onboarding_manager.track_user_action(f"stats_test_action_{i}", {"index": i})
            onboarding_manager.track_feature_usage(f"feature_{i % 10}")
        
        start_time = time.time()
        
        # Generate statistics multiple times
        for _ in range(10):
            stats = onboarding_manager.get_comprehensive_statistics()
            assert isinstance(stats, dict)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should generate statistics quickly
        assert total_time < 0.5, f"Statistics generation took {total_time:.2f}s, expected < 0.5s"
        
        print(f"Statistics generation time: {total_time:.3f}s")


class TestMemoryUsage:
    """Test memory usage and leak detection"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    def test_memory_usage_baseline(self, main_window):
        """Test baseline memory usage of onboarding system"""
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Perform some operations
            for i in range(100):
                manager.track_user_action(f"memory_test_{i}", {"index": i})
            
            # Force garbage collection
            gc.collect()
            final_objects = len(gc.get_objects())
            
            object_increase = final_objects - initial_objects
            
            # Should not create excessive objects
            assert object_increase < 1000, f"Created {object_increase} objects, expected < 1000"
            
            print(f"Object count increase: {object_increase}")
    
    def test_memory_leak_detection(self, main_window):
        """Test for memory leaks during repeated operations"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Baseline measurement
            gc.collect()
            baseline_objects = len(gc.get_objects())
            
            # Perform repeated operations that might cause leaks
            for cycle in range(5):
                for i in range(100):
                    manager.track_user_action(f"leak_test_{i}", {"cycle": cycle})
                    manager.get_recommendations()
                    manager.search_documentation("test query")
                    manager.get_discovery_progress()
                
                # Force garbage collection after each cycle
                gc.collect()
            
            final_objects = len(gc.get_objects())
            object_growth = final_objects - baseline_objects
            
            # Should not have significant object growth
            assert object_growth < 500, f"Object growth: {object_growth}, possible memory leak"
            
            print(f"Object growth after repeated operations: {object_growth}")
    
    def test_large_data_handling(self, main_window):
        """Test handling of large amounts of data"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Track large amount of data
            large_context = {"data": "x" * 1000}  # 1KB of data per action
            
            start_time = time.time()
            
            for i in range(1000):
                manager.track_user_action(f"large_data_test_{i}", large_context)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should handle large data efficiently
            assert total_time < 5.0, f"Large data handling took {total_time:.2f}s, expected < 5.0s"
            
            print(f"Large data handling time: {total_time:.3f}s")


class TestConcurrencyAndThreadSafety:
    """Test concurrent access and thread safety"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    def test_concurrent_action_tracking(self, main_window):
        """Test concurrent action tracking from multiple threads"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            results = []
            errors = []
            
            def track_actions(thread_id, num_actions):
                try:
                    for i in range(num_actions):
                        manager.track_user_action(
                            f"concurrent_test_thread_{thread_id}_action_{i}",
                            {"thread_id": thread_id, "action_index": i}
                        )
                    results.append(f"Thread {thread_id} completed")
                except Exception as e:
                    errors.append(f"Thread {thread_id} error: {e}")
            
            # Create multiple threads
            threads = []
            num_threads = 5
            actions_per_thread = 50
            
            start_time = time.time()
            
            for thread_id in range(num_threads):
                thread = threading.Thread(
                    target=track_actions,
                    args=(thread_id, actions_per_thread)
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=10)  # 10 second timeout
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verify all threads completed successfully
            assert len(errors) == 0, f"Errors in concurrent execution: {errors}"
            assert len(results) == num_threads, f"Only {len(results)} threads completed, expected {num_threads}"
            
            print(f"Concurrent action tracking time: {total_time:.3f}s")
    
    def test_concurrent_system_operations(self, main_window):
        """Test concurrent system operations"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            results = []
            errors = []
            
            def perform_operations(thread_id):
                try:
                    operations = [
                        lambda: manager.track_user_action(f"op_test_{thread_id}", {}),
                        lambda: manager.get_recommendations(),
                        lambda: manager.search_documentation("test"),
                        lambda: manager.get_discovery_progress(),
                        lambda: manager.get_comprehensive_statistics(),
                    ]
                    
                    for i, operation in enumerate(operations * 10):  # Repeat operations
                        operation()
                    
                    results.append(f"Thread {thread_id} completed")
                except Exception as e:
                    errors.append(f"Thread {thread_id} error: {e}")
            
            # Create multiple threads performing different operations
            threads = []
            num_threads = 3
            
            for thread_id in range(num_threads):
                thread = threading.Thread(target=perform_operations, args=(thread_id,))
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join(timeout=15)
            
            # Verify no errors occurred
            assert len(errors) == 0, f"Errors in concurrent operations: {errors}"
            assert len(results) == num_threads, f"Only {len(results)} threads completed"
            
            print(f"Concurrent operations completed successfully")


class TestScalabilityLimits:
    """Test system scalability limits"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    def test_maximum_recommendations(self, main_window):
        """Test handling of maximum number of recommendations"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Generate many recommendations by triggering various conditions
            for i in range(100):
                manager.track_user_action("visited_home_page", {"iteration": i})
                manager.track_error("connection_error", {"attempt": i})
                manager.track_system_state({"cpu_usage": 85 + (i % 10)})
            
            recommendations = manager.get_recommendations(limit=50)
            
            # Should handle large number of recommendations
            assert isinstance(recommendations, list)
            assert len(recommendations) <= 50
            
            print(f"Generated {len(recommendations)} recommendations")
    
    def test_maximum_documentation_items(self, main_window):
        """Test handling of large documentation database"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Test search with various queries
            search_queries = [
                "server", "configuration", "setup", "troubleshooting",
                "module", "development", "performance", "optimization",
                "connection", "error", "guide", "tutorial"
            ]
            
            total_results = 0
            
            for query in search_queries:
                results = manager.search_documentation(query)
                total_results += len(results)
            
            # Should handle searches efficiently
            assert total_results >= 0
            
            print(f"Total search results across all queries: {total_results}")
    
    def test_long_running_session(self, main_window):
        """Test system behavior during long-running session"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Simulate long-running session with various activities
            session_duration = 60  # seconds (reduced for testing)
            start_time = time.time()
            action_count = 0
            
            while time.time() - start_time < session_duration:
                # Simulate user activity
                manager.track_user_action(f"session_action_{action_count}", {
                    "timestamp": datetime.now().isoformat(),
                    "session_time": time.time() - start_time
                })
                
                # Occasionally get recommendations and search docs
                if action_count % 10 == 0:
                    manager.get_recommendations()
                    manager.search_documentation("session test")
                
                action_count += 1
                time.sleep(0.1)  # Small delay to simulate real usage
            
            # Verify system is still responsive
            final_stats = manager.get_comprehensive_statistics()
            assert isinstance(final_stats, dict)
            
            print(f"Long-running session: {action_count} actions over {session_duration}s")


class TestResourceCleanup:
    """Test proper resource cleanup and shutdown"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        return QApplication.instance() or QApplication([])
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing"""
        return QWidget()
    
    def test_system_shutdown(self, main_window):
        """Test proper system shutdown and cleanup"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            manager = OnboardingManager(main_window)
            manager.initialize_all_systems()
            
            # Perform some operations
            for i in range(50):
                manager.track_user_action(f"shutdown_test_{i}", {})
            
            # Start some timers and operations
            if hasattr(manager._smart_tip_system, 'start_rotation'):
                manager._smart_tip_system.start_rotation(1000)
            
            # Shutdown system
            start_time = time.time()
            manager.shutdown_all_systems()
            end_time = time.time()
            
            shutdown_time = end_time - start_time
            
            # Should shutdown quickly
            assert shutdown_time < 1.0, f"Shutdown took {shutdown_time:.2f}s, expected < 1.0s"
            
            print(f"System shutdown time: {shutdown_time:.3f}s")
    
    def test_repeated_initialization_shutdown(self, main_window):
        """Test repeated initialization and shutdown cycles"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            cycles = 5
            
            for cycle in range(cycles):
                start_time = time.time()
                
                # Initialize
                manager = OnboardingManager(main_window)
                manager.initialize_all_systems()
                
                # Perform some operations
                for i in range(10):
                    manager.track_user_action(f"cycle_{cycle}_action_{i}", {})
                
                # Shutdown
                manager.shutdown_all_systems()
                
                end_time = time.time()
                cycle_time = end_time - start_time
                
                # Each cycle should complete quickly
                assert cycle_time < 2.0, f"Cycle {cycle} took {cycle_time:.2f}s, expected < 2.0s"
            
            print(f"Completed {cycles} initialization/shutdown cycles")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print output
