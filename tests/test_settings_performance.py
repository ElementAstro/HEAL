"""
Settings Performance Testing and Validation
Tests the performance improvements and validates functionality
"""

import unittest
import time
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Mock PySide6 components for testing
class MockQObject:
    def __init__(self, parent=None):
        self.parent = parent

class MockSignal:
    def __init__(self):
        self.callbacks = []
    
    def connect(self, callback):
        self.callbacks.append(callback)
    
    def emit(self, *args, **kwargs):
        for callback in self.callbacks:
            callback(*args, **kwargs)

class MockQMutex:
    def __init__(self):
        pass

class MockQMutexLocker:
    def __init__(self, mutex):
        self.mutex = mutex
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class MockQTimer:
    def __init__(self):
        self.timeout = MockSignal()
        self.active = False
    
    def start(self, interval):
        self.active = True
    
    def stop(self):
        self.active = False
    
    def isActive(self):
        return self.active
    
    def setSingleShot(self, single):
        pass

# Mock the PySide6 imports
import sys
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtGui'] = Mock()
sys.modules['qfluentwidgets'] = Mock()

# Mock the Qt classes
sys.modules['PySide6.QtCore'].QObject = MockQObject
sys.modules['PySide6.QtCore'].Signal = MockSignal
sys.modules['PySide6.QtCore'].QMutex = MockQMutex
sys.modules['PySide6.QtCore'].QMutexLocker = MockQMutexLocker
sys.modules['PySide6.QtCore'].QTimer = MockQTimer
sys.modules['PySide6.QtCore'].QThread = MockQObject
sys.modules['PySide6.QtCore'].pyqtSignal = MockSignal

# Now import our performance components
from app.components.setting.performance_manager import (
    SettingsCache, SettingsPerformanceManager, CacheEntry
)
from app.components.setting.lazy_settings import LazySettingsManager, LazySettingProxy
from app.components.setting.error_handler import (
    SettingsErrorHandler, SettingsValidator, SettingsBackupManager, ErrorSeverity
)


class TestSettingsCache(unittest.TestCase):
    """Test the settings cache functionality"""
    
    def setUp(self):
        self.cache = SettingsCache(max_size=10, default_ttl=1.0)
    
    def test_cache_set_get(self):
        """Test basic cache set and get operations"""
        self.cache.set('test_key', 'test_value')
        value = self.cache.get('test_key')
        self.assertEqual(value, 'test_value')
    
    def test_cache_default_value(self):
        """Test cache returns default value for missing keys"""
        value = self.cache.get('missing_key', 'default')
        self.assertEqual(value, 'default')
    
    def test_cache_expiration(self):
        """Test cache entry expiration"""
        self.cache.set('expire_key', 'expire_value')
        time.sleep(1.1)  # Wait for expiration
        value = self.cache.get('expire_key', 'default')
        self.assertEqual(value, 'default')
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        # Fill cache to max size
        for i in range(10):
            self.cache.set(f'key_{i}', f'value_{i}')
        
        # Add one more item to trigger eviction
        self.cache.set('new_key', 'new_value')
        
        # The first item should be evicted
        value = self.cache.get('key_0', 'not_found')
        self.assertEqual(value, 'not_found')
        
        # The new item should be present
        value = self.cache.get('new_key')
        self.assertEqual(value, 'new_value')
    
    def test_cache_stats(self):
        """Test cache statistics"""
        self.cache.set('stat_key', 'stat_value')
        self.cache.get('stat_key')
        
        stats = self.cache.get_stats()
        self.assertIn('size', stats)
        self.assertIn('max_size', stats)
        self.assertIn('total_accesses', stats)
        self.assertEqual(stats['size'], 1)
        self.assertEqual(stats['max_size'], 10)


class TestLazySettings(unittest.TestCase):
    """Test lazy loading functionality"""
    
    def setUp(self):
        self.lazy_manager = LazySettingsManager()
    
    def test_lazy_setting_proxy(self):
        """Test lazy setting proxy functionality"""
        def expensive_loader():
            time.sleep(0.1)  # Simulate expensive operation
            return "loaded_value"
        
        proxy = LazySettingProxy('test_setting', expensive_loader, 'fallback')
        
        # Should not be loaded initially
        self.assertFalse(proxy.is_loaded())
        
        # First access should trigger loading
        start_time = time.time()
        value = proxy.value
        load_time = time.time() - start_time
        
        self.assertEqual(value, "loaded_value")
        self.assertTrue(proxy.is_loaded())
        self.assertGreater(load_time, 0.05)  # Should take some time
        
        # Second access should be fast (cached)
        start_time = time.time()
        value2 = proxy.value
        fast_time = time.time() - start_time
        
        self.assertEqual(value2, "loaded_value")
        self.assertLess(fast_time, 0.01)  # Should be very fast
    
    def test_lazy_manager_registration(self):
        """Test lazy manager setting registration"""
        def test_loader():
            return "test_result"
        
        proxy = self.lazy_manager.register_lazy_setting(
            'test_lazy', test_loader, 'fallback'
        )
        
        self.assertIsInstance(proxy, LazySettingProxy)
        self.assertEqual(proxy.setting_key, 'test_lazy')
        self.assertEqual(proxy.fallback_value, 'fallback')
    
    def test_lazy_manager_get_setting(self):
        """Test getting settings through lazy manager"""
        def test_loader():
            return "manager_result"
        
        self.lazy_manager.register_lazy_setting('manager_test', test_loader)
        value = self.lazy_manager.get_setting('manager_test')
        
        self.assertEqual(value, "manager_result")
    
    def test_lazy_loading_stats(self):
        """Test lazy loading statistics"""
        def loader1():
            return "value1"
        
        def loader2():
            return "value2"
        
        self.lazy_manager.register_lazy_setting('stat1', loader1)
        self.lazy_manager.register_lazy_setting('stat2', loader2)
        
        # Load one setting
        self.lazy_manager.get_setting('stat1')
        
        stats = self.lazy_manager.get_loading_stats()
        self.assertEqual(stats['total_settings'], 2)
        self.assertEqual(stats['loaded_settings'], 1)
        self.assertEqual(stats['load_percentage'], 50.0)


class TestErrorHandler(unittest.TestCase):
    """Test error handling and recovery"""
    
    def setUp(self):
        self.error_handler = SettingsErrorHandler()
        self.validator = SettingsValidator()
    
    def test_error_handling(self):
        """Test basic error handling"""
        test_error = ValueError("Test error")
        result = self.error_handler.handle_error(
            'test_operation', test_error, {'test': 'context'}
        )
        
        # Should have recorded the error
        self.assertEqual(self.error_handler.error_stats['total_errors'], 1)
        self.assertTrue(len(self.error_handler.errors) > 0)
    
    def test_validator_registration(self):
        """Test validation rule registration"""
        def test_validator(value):
            return isinstance(value, str) and len(value) > 0
        
        self.validator.register_validation_rule('test_setting', test_validator)
        
        # Valid value should pass
        self.assertTrue(self.validator.validate_setting('test_setting', 'valid'))
        
        # Invalid value should fail
        self.assertFalse(self.validator.validate_setting('test_setting', ''))
        self.assertFalse(self.validator.validate_setting('test_setting', 123))
    
    def test_backup_manager(self):
        """Test backup functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_manager = SettingsBackupManager(backup_dir=temp_dir)
            
            # Create a test file
            test_file = Path(temp_dir) / 'test_config.json'
            test_data = {'test': 'data', 'value': 123}
            
            with open(test_file, 'w') as f:
                json.dump(test_data, f)
            
            # Create backup
            backup_path = backup_manager.create_backup(str(test_file))
            self.assertIsNotNone(backup_path)
            self.assertTrue(Path(backup_path).exists())
            
            # Modify original file
            modified_data = {'test': 'modified', 'value': 456}
            with open(test_file, 'w') as f:
                json.dump(modified_data, f)
            
            # Restore from backup
            success = backup_manager.restore_backup(str(test_file), backup_path)
            self.assertTrue(success)
            
            # Verify restoration
            with open(test_file, 'r') as f:
                restored_data = json.load(f)
            
            self.assertEqual(restored_data, test_data)


class TestPerformanceIntegration(unittest.TestCase):
    """Test integrated performance improvements"""
    
    def setUp(self):
        # Mock the parent widget
        self.mock_parent = Mock()
        self.mock_parent.tr = lambda x: x
        
        # Create performance manager
        self.perf_manager = SettingsPerformanceManager()
    
    def test_performance_manager_get_set(self):
        """Test performance manager get/set operations"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {'existing_key': 'existing_value'}
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            # Test setting a value
            self.perf_manager.set_setting(temp_file, 'test_key', 'test_value')
            
            # Test getting the value (should be cached)
            value = self.perf_manager.get_setting(temp_file, 'test_key')
            self.assertEqual(value, 'test_value')
            
            # Test getting existing value
            existing_value = self.perf_manager.get_setting(temp_file, 'existing_key')
            self.assertEqual(existing_value, 'existing_value')
            
            # Test default value for missing key
            default_value = self.perf_manager.get_setting(temp_file, 'missing_key', 'default')
            self.assertEqual(default_value, 'default')
            
        finally:
            os.unlink(temp_file)
    
    def test_performance_stats(self):
        """Test performance statistics collection"""
        stats = self.perf_manager.get_performance_stats()
        
        self.assertIn('cache', stats)
        self.assertIn('pending_saves', stats)
        self.assertIn('lazy_loaded_settings', stats)
        self.assertIn('registered_lazy_settings', stats)
    
    def test_cache_invalidation(self):
        """Test cache invalidation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'test': 'value'}, f)
            temp_file = f.name
        
        try:
            # Set and get value (should be cached)
            self.perf_manager.set_setting(temp_file, 'test_key', 'cached_value')
            value1 = self.perf_manager.get_setting(temp_file, 'test_key')
            self.assertEqual(value1, 'cached_value')
            
            # Invalidate cache
            self.perf_manager.invalidate_cache(temp_file, 'test_key')
            
            # Should return default since cache is invalidated and file doesn't have the key
            value2 = self.perf_manager.get_setting(temp_file, 'test_key', 'default')
            self.assertEqual(value2, 'default')
            
        finally:
            os.unlink(temp_file)


def run_performance_benchmarks():
    """Run performance benchmarks"""
    print("\n=== Settings Performance Benchmarks ===")
    
    # Test cache performance
    cache = SettingsCache(max_size=1000)
    
    # Benchmark cache writes
    start_time = time.time()
    for i in range(1000):
        cache.set(f'key_{i}', f'value_{i}')
    write_time = time.time() - start_time
    print(f"Cache writes (1000 items): {write_time:.3f}s ({1000/write_time:.0f} ops/sec)")
    
    # Benchmark cache reads
    start_time = time.time()
    for i in range(1000):
        cache.get(f'key_{i}')
    read_time = time.time() - start_time
    print(f"Cache reads (1000 items): {read_time:.3f}s ({1000/read_time:.0f} ops/sec)")
    
    # Test lazy loading performance
    def expensive_operation():
        time.sleep(0.01)  # Simulate 10ms operation
        return "expensive_result"
    
    proxy = LazySettingProxy('benchmark', expensive_operation)
    
    # First access (should be slow)
    start_time = time.time()
    value1 = proxy.value
    first_access = time.time() - start_time
    
    # Second access (should be fast)
    start_time = time.time()
    value2 = proxy.value
    second_access = time.time() - start_time
    
    print(f"Lazy loading first access: {first_access:.3f}s")
    print(f"Lazy loading cached access: {second_access:.3f}s")
    print(f"Speedup: {first_access/second_access:.1f}x")


if __name__ == '__main__':
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance benchmarks
    run_performance_benchmarks()
