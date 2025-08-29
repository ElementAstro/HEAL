"""
Tests for the cache manager module.

Tests caching functionality including cache creation, management,
and performance optimization.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

# Mock PySide6 before importing any modules that depend on it
with patch.dict('sys.modules', {
    'PySide6': Mock(),
    'PySide6.QtCore': Mock(),
    'PySide6.QtWidgets': Mock(),
    'PySide6.QtNetwork': Mock(),
    'qfluentwidgets': Mock()
}):
    from src.heal.common.cache_manager import CacheManager, LRUCache, global_cache_manager


class TestCacheManager:
    """Test the cache manager"""
    
    @pytest.fixture
    def cache_manager(self):
        """Create a cache manager instance for testing"""
        return CacheManager()
    
    def test_cache_manager_initialization(self, cache_manager):
        """Test cache manager initialization"""
        assert cache_manager is not None
    
    def test_register_cache(self, cache_manager):
        """Test cache registration"""
        cache_name = "test_cache"
        cache_instance = LRUCache(max_size=100)
        
        cache_manager.register_cache(cache_name, cache_instance)
        retrieved_cache = cache_manager.get_cache(cache_name)
        assert retrieved_cache is cache_instance
    
    def test_get_cache(self, cache_manager):
        """Test cache retrieval"""
        cache_name = "test_cache"
        cache_instance = LRUCache(max_size=100)
        cache_manager.register_cache(cache_name, cache_instance)
        
        retrieved_cache = cache_manager.get_cache(cache_name)
        assert retrieved_cache is cache_instance
    
    def test_remove_cache(self, cache_manager):
        """Test cache removal"""
        cache_name = "test_cache"
        cache_instance = LRUCache(max_size=100)
        cache_manager.register_cache(cache_name, cache_instance)
        
        cache_manager.remove_cache(cache_name)
        retrieved_cache = cache_manager.get_cache(cache_name)
        assert retrieved_cache is None


class TestLRUCache:
    """Test the LRU cache implementation"""
    
    @pytest.fixture
    def lru_cache(self):
        """Create an LRU cache instance for testing"""
        return LRUCache(max_size=3)
    
    def test_lru_cache_initialization(self, lru_cache):
        """Test LRU cache initialization"""
        assert lru_cache is not None
        assert lru_cache.max_size == 3
    
    def test_cache_put_and_get(self, lru_cache):
        """Test cache put and get operations"""
        lru_cache.put("key1", "value1")
        assert lru_cache.get("key1") == "value1"
    
    def test_cache_eviction(self, lru_cache):
        """Test cache eviction when max size is exceeded"""
        lru_cache.put("key1", "value1")
        lru_cache.put("key2", "value2")
        lru_cache.put("key3", "value3")
        lru_cache.put("key4", "value4")  # Should evict key1
        
        assert lru_cache.get("key1") is None
        assert lru_cache.get("key4") == "value4"
    
    def test_cache_hit_miss_stats(self, lru_cache):
        """Test cache hit/miss statistics"""
        lru_cache.put("key1", "value1")
        
        # Cache hit
        value = lru_cache.get("key1")
        assert value == "value1"
        
        # Cache miss
        value = lru_cache.get("nonexistent_key")
        assert value is None


class TestGlobalCacheManager:
    """Test the global cache manager instance"""
    
    def test_global_cache_manager_exists(self):
        """Test that global cache manager exists"""
        assert global_cache_manager is not None
        assert isinstance(global_cache_manager, CacheManager)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
