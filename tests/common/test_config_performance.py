"""
Performance and stress tests for the configuration system

Tests performance characteristics including:
- Bulk operations performance
- Memory usage optimization
- Concurrent access performance
- Large configuration handling
- Cache performance
"""

import pytest
import time
import threading
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock
import gc
import sys

# Mock configuration system for performance testing
class MockPerformanceConfigManager:
    def __init__(self):
        self.config_data = {}
        self.change_listeners = []
        self.profiles = {}
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.operation_count = 0
        self.lock = threading.RLock()
    
    def get(self, key, default=None):
        with self.lock:
            self.operation_count += 1
            
            # Check cache first
            if key in self.cache:
                self.cache_hits += 1
                return self.cache[key]
            
            self.cache_misses += 1
            
            # Get from config data
            keys = key.split('.')
            current = self.config_data
            
            for k in keys:
                if not isinstance(current, dict) or k not in current:
                    self.cache[key] = default
                    return default
                current = current[k]
            
            self.cache[key] = current
            return current
    
    def set(self, key, value):
        with self.lock:
            self.operation_count += 1
            
            keys = key.split('.')
            current = self.config_data
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            old_value = current.get(keys[-1])
            current[keys[-1]] = value
            
            # Update cache
            self.cache[key] = value
            
            # Notify listeners (simulate)
            for listener in self.change_listeners:
                try:
                    listener(key, old_value, value)
                except Exception:
                    pass
            
            return True
    
    def add_change_listener(self, listener):
        with self.lock:
            self.change_listeners.append(listener)
    
    def create_profile(self, name, description):
        with self.lock:
            import uuid
            profile_id = str(uuid.uuid4())
            
            profile = {
                'profile_id': profile_id,
                'name': name,
                'description': description,
                'settings': {},
                'created_at': time.time()
            }
            
            self.profiles[profile_id] = profile
            return profile_id
    
    def clear_cache(self):
        with self.lock:
            self.cache.clear()
            self.cache_hits = 0
            self.cache_misses = 0
    
    def get_stats(self):
        with self.lock:
            return {
                'operation_count': self.operation_count,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_ratio': self.cache_hits / max(1, self.cache_hits + self.cache_misses),
                'config_size': len(self.config_data),
                'profile_count': len(self.profiles),
                'listener_count': len(self.change_listeners)
            }


class TestConfigurationPerformance:
    """Performance test suite for configuration system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config_manager = MockPerformanceConfigManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        gc.collect()  # Force garbage collection
    
    def test_bulk_set_operations_performance(self):
        """Test performance of bulk set operations"""
        start_time = time.time()
        
        # Set 1000 configuration values
        for i in range(1000):
            key = f"performance.test.key_{i}"
            value = f"value_{i}"
            self.config_manager.set(key, value)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time (less than 2 seconds)
        assert duration < 2.0, f"Bulk set operations took {duration:.2f} seconds"
        
        # Verify operations per second
        ops_per_second = 1000 / duration
        assert ops_per_second > 500, f"Only {ops_per_second:.0f} ops/sec, expected > 500"
        
        print(f"✅ Bulk set: {ops_per_second:.0f} ops/sec in {duration:.3f}s")
    
    def test_bulk_get_operations_performance(self):
        """Test performance of bulk get operations"""
        # Setup test data
        for i in range(1000):
            self.config_manager.set(f"performance.test.key_{i}", f"value_{i}")
        
        # Clear cache to test raw performance
        self.config_manager.clear_cache()
        
        start_time = time.time()
        
        # Get 1000 configuration values
        for i in range(1000):
            key = f"performance.test.key_{i}"
            value = self.config_manager.get(key)
            assert value == f"value_{i}"
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 1.0, f"Bulk get operations took {duration:.2f} seconds"
        
        ops_per_second = 1000 / duration
        assert ops_per_second > 1000, f"Only {ops_per_second:.0f} ops/sec, expected > 1000"
        
        print(f"✅ Bulk get: {ops_per_second:.0f} ops/sec in {duration:.3f}s")
    
    def test_cache_performance(self):
        """Test cache performance and hit ratio"""
        # Setup test data
        for i in range(100):
            self.config_manager.set(f"cache.test.key_{i}", f"value_{i}")
        
        # Clear cache
        self.config_manager.clear_cache()
        
        # First access - should miss cache
        for i in range(100):
            self.config_manager.get(f"cache.test.key_{i}")
        
        # Second access - should hit cache
        start_time = time.time()
        for i in range(100):
            self.config_manager.get(f"cache.test.key_{i}")
        end_time = time.time()
        
        stats = self.config_manager.get_stats()
        
        # Verify cache hit ratio
        assert stats['cache_hit_ratio'] > 0.5, f"Cache hit ratio too low: {stats['cache_hit_ratio']:.2f}"
        
        # Cached access should be very fast
        cached_duration = end_time - start_time
        assert cached_duration < 0.1, f"Cached access took {cached_duration:.3f} seconds"
        
        print(f"✅ Cache hit ratio: {stats['cache_hit_ratio']:.2f}, cached access: {cached_duration:.3f}s")
    
    def test_concurrent_access_performance(self):
        """Test concurrent access performance"""
        results = []
        errors = []
        
        def worker_thread(worker_id, operation_count):
            try:
                start_time = time.time()
                
                for i in range(operation_count):
                    # Mix of set and get operations
                    if i % 2 == 0:
                        key = f"concurrent.worker_{worker_id}.item_{i}"
                        value = f"value_{worker_id}_{i}"
                        self.config_manager.set(key, value)
                    else:
                        key = f"concurrent.worker_{worker_id}.item_{i-1}"
                        value = self.config_manager.get(key)
                
                end_time = time.time()
                duration = end_time - start_time
                results.append((worker_id, duration, operation_count))
                
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Create and start multiple threads
        threads = []
        operation_count = 100
        thread_count = 10
        
        start_time = time.time()
        
        for worker_id in range(thread_count):
            thread = threading.Thread(
                target=worker_thread,
                args=(worker_id, operation_count)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Errors in concurrent access: {errors}"
        
        # Verify all threads completed
        assert len(results) == thread_count, f"Only {len(results)} threads completed"
        
        # Calculate performance metrics
        total_operations = thread_count * operation_count
        ops_per_second = total_operations / total_duration
        
        # Should handle concurrent access efficiently
        assert ops_per_second > 500, f"Concurrent ops/sec too low: {ops_per_second:.0f}"
        
        print(f"✅ Concurrent access: {ops_per_second:.0f} ops/sec with {thread_count} threads")
    
    def test_large_configuration_handling(self):
        """Test handling of large configuration structures"""
        # Create large nested configuration
        large_config = {}
        
        start_time = time.time()
        
        # Create 10 levels deep, 10 items per level
        for level1 in range(10):
            for level2 in range(10):
                for level3 in range(10):
                    key = f"large.level1_{level1}.level2_{level2}.level3_{level3}"
                    value = {
                        "string_value": f"test_string_{level1}_{level2}_{level3}",
                        "number_value": level1 * 100 + level2 * 10 + level3,
                        "boolean_value": (level1 + level2 + level3) % 2 == 0,
                        "list_value": [f"item_{i}" for i in range(5)],
                        "nested_dict": {
                            "sub_key_1": "sub_value_1",
                            "sub_key_2": "sub_value_2"
                        }
                    }
                    self.config_manager.set(key, value)
        
        set_time = time.time() - start_time
        
        # Test retrieval performance
        start_time = time.time()
        
        for level1 in range(10):
            for level2 in range(10):
                for level3 in range(10):
                    key = f"large.level1_{level1}.level2_{level2}.level3_{level3}"
                    value = self.config_manager.get(key)
                    assert value is not None
        
        get_time = time.time() - start_time
        
        # Performance should be reasonable even with large configs
        assert set_time < 5.0, f"Large config set took {set_time:.2f} seconds"
        assert get_time < 2.0, f"Large config get took {get_time:.2f} seconds"
        
        print(f"✅ Large config: set {set_time:.2f}s, get {get_time:.2f}s")
    
    def test_memory_usage_optimization(self):
        """Test memory usage characteristics"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large amount of configuration data
        for i in range(5000):
            key = f"memory.test.section_{i // 100}.key_{i}"
            value = {
                "data": f"test_data_{i}" * 10,  # Larger string
                "metadata": {
                    "created": time.time(),
                    "index": i,
                    "tags": [f"tag_{j}" for j in range(5)]
                }
            }
            self.config_manager.set(key, value)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Clear configuration and force garbage collection
        self.config_manager.config_data.clear()
        self.config_manager.cache.clear()
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_freed = peak_memory - final_memory
        
        # Memory usage should be reasonable
        assert memory_increase < 100, f"Memory increase too high: {memory_increase:.1f} MB"
        
        # Should free most memory when cleared
        memory_efficiency = memory_freed / memory_increase if memory_increase > 0 else 1.0
        assert memory_efficiency > 0.5, f"Memory efficiency too low: {memory_efficiency:.2f}"
        
        print(f"✅ Memory: +{memory_increase:.1f}MB, freed {memory_freed:.1f}MB ({memory_efficiency:.1%})")
    
    def test_profile_operations_performance(self):
        """Test profile operations performance"""
        start_time = time.time()
        
        # Create many profiles
        profile_ids = []
        for i in range(1000):
            profile_id = self.config_manager.create_profile(
                f"Profile {i}",
                f"Test profile {i}"
            )
            profile_ids.append(profile_id)
        
        creation_time = time.time() - start_time
        
        # Test profile lookup performance
        start_time = time.time()
        
        for profile_id in profile_ids:
            profile = self.config_manager.profiles.get(profile_id)
            assert profile is not None
        
        lookup_time = time.time() - start_time
        
        # Performance should be reasonable
        assert creation_time < 2.0, f"Profile creation took {creation_time:.2f} seconds"
        assert lookup_time < 0.5, f"Profile lookup took {lookup_time:.2f} seconds"
        
        creation_rate = 1000 / creation_time
        lookup_rate = 1000 / lookup_time
        
        print(f"✅ Profiles: create {creation_rate:.0f}/s, lookup {lookup_rate:.0f}/s")
    
    def test_change_listener_performance(self):
        """Test change listener performance impact"""
        # Test without listeners
        start_time = time.time()
        
        for i in range(1000):
            self.config_manager.set(f"listener.test.key_{i}", f"value_{i}")
        
        no_listener_time = time.time() - start_time
        
        # Add multiple listeners
        listeners = []
        for i in range(10):
            def listener(key, old_val, new_val, listener_id=i):
                # Simulate some processing
                pass
            listeners.append(listener)
            self.config_manager.add_change_listener(listener)
        
        # Test with listeners
        start_time = time.time()
        
        for i in range(1000):
            self.config_manager.set(f"listener.test.with_listeners_{i}", f"value_{i}")
        
        with_listener_time = time.time() - start_time
        
        # Listener overhead should be reasonable
        overhead_ratio = with_listener_time / no_listener_time
        assert overhead_ratio < 3.0, f"Listener overhead too high: {overhead_ratio:.1f}x"
        
        print(f"✅ Listeners: {overhead_ratio:.1f}x overhead with 10 listeners")
    
    def test_nested_key_performance(self):
        """Test performance with deeply nested keys"""
        # Test various nesting levels
        nesting_levels = [1, 5, 10, 15, 20]
        results = {}
        
        for level in nesting_levels:
            # Create deeply nested key
            key_parts = [f"level_{i}" for i in range(level)]
            key = ".".join(key_parts)
            
            # Test set performance
            start_time = time.time()
            for i in range(100):
                test_key = f"{key}.item_{i}"
                self.config_manager.set(test_key, f"value_{i}")
            set_time = time.time() - start_time
            
            # Test get performance
            start_time = time.time()
            for i in range(100):
                test_key = f"{key}.item_{i}"
                value = self.config_manager.get(test_key)
                assert value == f"value_{i}"
            get_time = time.time() - start_time
            
            results[level] = (set_time, get_time)
        
        # Performance should not degrade significantly with nesting
        shallow_set, shallow_get = results[1]
        deep_set, deep_get = results[20]
        
        set_degradation = deep_set / shallow_set
        get_degradation = deep_get / shallow_get
        
        assert set_degradation < 5.0, f"Set performance degraded {set_degradation:.1f}x with deep nesting"
        assert get_degradation < 5.0, f"Get performance degraded {get_degradation:.1f}x with deep nesting"
        
        print(f"✅ Nesting: set {set_degradation:.1f}x, get {get_degradation:.1f}x degradation at 20 levels")
    
    def test_stress_test_mixed_operations(self):
        """Stress test with mixed operations"""
        operations = []
        errors = []
        
        def stress_worker(worker_id, duration_seconds):
            try:
                start_time = time.time()
                op_count = 0
                
                while time.time() - start_time < duration_seconds:
                    op_type = op_count % 4
                    
                    if op_type == 0:  # Set operation
                        key = f"stress.worker_{worker_id}.set_{op_count}"
                        self.config_manager.set(key, f"value_{op_count}")
                    elif op_type == 1:  # Get operation
                        key = f"stress.worker_{worker_id}.set_{max(0, op_count-10)}"
                        self.config_manager.get(key)
                    elif op_type == 2:  # Profile operation
                        if op_count % 50 == 0:  # Less frequent
                            self.config_manager.create_profile(
                                f"Stress Profile {worker_id}_{op_count}",
                                "Stress test profile"
                            )
                    else:  # Cache operation
                        key = f"stress.worker_{worker_id}.set_{max(0, op_count-5)}"
                        self.config_manager.get(key)  # Should hit cache
                    
                    op_count += 1
                
                operations.append((worker_id, op_count))
                
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Run stress test with multiple workers
        threads = []
        worker_count = 5
        duration = 2.0  # 2 seconds
        
        start_time = time.time()
        
        for worker_id in range(worker_count):
            thread = threading.Thread(
                target=stress_worker,
                args=(worker_id, duration)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Verify no errors
        assert len(errors) == 0, f"Stress test errors: {errors}"
        
        # Calculate total operations
        total_ops = sum(ops for _, ops in operations)
        ops_per_second = total_ops / total_time
        
        # Should handle stress test well
        assert ops_per_second > 1000, f"Stress test ops/sec too low: {ops_per_second:.0f}"
        
        stats = self.config_manager.get_stats()
        print(f"✅ Stress test: {ops_per_second:.0f} ops/sec, {stats['cache_hit_ratio']:.2f} cache ratio")


if __name__ == "__main__":
    # Run performance tests
    test_suite = TestConfigurationPerformance()
    
    # Run all test methods
    test_methods = [method for method in dir(test_suite) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    print("🚀 Running Configuration Performance Tests")
    print("=" * 50)
    
    for test_method in test_methods:
        try:
            print(f"\nRunning {test_method}...")
            test_suite.setup_method()
            getattr(test_suite, test_method)()
            test_suite.teardown_method()
            print(f"✅ {test_method} PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_method} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Performance Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All configuration performance tests passed!")
    else:
        print(f"⚠️ {failed} performance tests failed")
