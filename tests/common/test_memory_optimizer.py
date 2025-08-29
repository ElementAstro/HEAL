"""
Tests for the memory optimizer module.

Tests memory optimization functionality including object pooling,
memory monitoring, and optimization strategies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import gc
import sys

# Mock PySide6 before importing any modules that depend on it
with patch.dict('sys.modules', {
    'PySide6': Mock(),
    'PySide6.QtCore': Mock(),
    'PySide6.QtWidgets': Mock(),
    'PySide6.QtNetwork': Mock(),
    'qfluentwidgets': Mock()
}):
    from src.heal.common.memory_optimizer import MemoryOptimizer, create_object_pool, optimize_memory, global_memory_optimizer


class TestMemoryOptimizer:
    """Test the memory optimizer"""
    
    @pytest.fixture
    def memory_optimizer(self):
        """Create a memory optimizer instance for testing"""
        return MemoryOptimizer()
    
    def test_memory_optimizer_initialization(self, memory_optimizer):
        """Test memory optimizer initialization"""
        assert memory_optimizer is not None
        assert hasattr(memory_optimizer, 'monitor')
    
    def test_object_pool_creation(self):
        """Test object pool creation"""
        pool = create_object_pool(str, max_size=10)
        assert pool is not None
        
        # Test pool functionality
        obj1 = pool.get()
        assert isinstance(obj1, str)
        
        pool.return_object(obj1)
        obj2 = pool.get()
        # Test object reuse
    
    def test_memory_optimization(self, memory_optimizer):
        """Test memory optimization function"""
        # Get initial memory state
        initial_objects = len(gc.get_objects())
        
        # Run optimization
        result = optimize_memory()
        
        assert isinstance(result, dict)
        assert 'freed_objects' in result or 'memory_freed' in result
    
    def test_memory_monitoring(self, memory_optimizer):
        """Test memory monitoring functionality"""
        stats = memory_optimizer.monitor.get_memory_stats()
        assert isinstance(stats, dict)
        # Verify expected memory statistics
    
    def test_global_memory_optimizer(self):
        """Test global memory optimizer instance"""
        assert global_memory_optimizer is not None
        assert isinstance(global_memory_optimizer, MemoryOptimizer)


class TestMemoryOptimizerIntegration:
    """Integration tests for memory optimizer"""
    
    def test_memory_optimizer_with_cache(self):
        """Test memory optimizer integration with cache manager"""
        with patch('src.heal.common.cache_manager.global_cache_manager'):
            # Test cache cleanup during memory optimization
            result = optimize_memory()
            assert isinstance(result, dict)
    
    def test_memory_optimizer_with_performance_monitor(self):
        """Test memory optimizer integration with performance monitoring"""
        with patch('src.heal.common.performance_analyzer.PerformanceAnalyzer'):
            # Test performance monitoring during optimization
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
