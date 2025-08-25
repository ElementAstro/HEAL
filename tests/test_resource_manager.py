"""
Resource Manager Tests
测试资源管理器的功能和可靠性
"""

import unittest
import threading
import time
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QTimer, QObject

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.common.resource_manager import (
    ResourceManager, ResourceType, ResourceInfo, 
    register_timer, register_custom_resource, cleanup_on_exit
)


class TestResourceInfo(unittest.TestCase):
    """测试ResourceInfo类"""
    
    def test_resource_info_creation(self):
        """测试ResourceInfo创建"""
        mock_obj = Mock()
        cleanup_func = Mock()
        
        info = ResourceInfo(
            resource_id="test_resource",
            resource_type=ResourceType.CUSTOM,
            resource_obj=mock_obj,
            cleanup_func=cleanup_func,
            description="Test resource"
        )
        
        self.assertEqual(info.resource_id, "test_resource")
        self.assertEqual(info.resource_type, ResourceType.CUSTOM)
        self.assertEqual(info.description, "Test resource")
        self.assertFalse(info.is_cleaned)
        self.assertEqual(info.cleanup_func, cleanup_func)


class TestResourceManager(unittest.TestCase):
    """测试ResourceManager类"""
    
    def setUp(self):
        """测试前设置"""
        # 重置单例实例
        ResourceManager._instance = None
        self.manager = ResourceManager()
        
    def tearDown(self):
        """测试后清理"""
        # 清理所有资源
        self.manager.cleanup_all()
        ResourceManager._instance = None
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = ResourceManager()
        manager2 = ResourceManager()
        self.assertIs(manager1, manager2)
    
    def test_register_resource(self):
        """测试资源注册"""
        mock_obj = Mock()
        cleanup_func = Mock()
        
        result = self.manager.register_resource(
            "test_resource",
            ResourceType.CUSTOM,
            mock_obj,
            cleanup_func,
            "Test description"
        )
        
        self.assertTrue(result)
        self.assertIn("test_resource", self.manager.resources)
        
        resource_info = self.manager.resources["test_resource"]
        self.assertEqual(resource_info.resource_id, "test_resource")
        self.assertEqual(resource_info.resource_type, ResourceType.CUSTOM)
        self.assertEqual(resource_info.description, "Test description")
    
    def test_register_duplicate_resource(self):
        """测试重复注册资源"""
        mock_obj1 = Mock()
        mock_obj2 = Mock()
        cleanup_func1 = Mock()
        cleanup_func2 = Mock()
        
        # 第一次注册
        result1 = self.manager.register_resource(
            "duplicate_resource", ResourceType.CUSTOM, mock_obj1, cleanup_func1
        )
        self.assertTrue(result1)
        
        # 第二次注册（应该覆盖）
        result2 = self.manager.register_resource(
            "duplicate_resource", ResourceType.CUSTOM, mock_obj2, cleanup_func2
        )
        self.assertTrue(result2)
        
        # 验证资源被覆盖
        resource_info = self.manager.resources["duplicate_resource"]
        self.assertEqual(resource_info.cleanup_func, cleanup_func2)
    
    def test_unregister_resource(self):
        """测试资源注销"""
        mock_obj = Mock()
        cleanup_func = Mock()
        
        # 注册资源
        self.manager.register_resource(
            "test_resource", ResourceType.CUSTOM, mock_obj, cleanup_func
        )
        
        # 注销资源
        result = self.manager.unregister_resource("test_resource")
        self.assertTrue(result)
        self.assertNotIn("test_resource", self.manager.resources)
        
        # 注销不存在的资源
        result = self.manager.unregister_resource("nonexistent")
        self.assertFalse(result)
    
    def test_cleanup_resource(self):
        """测试单个资源清理"""
        mock_obj = Mock()
        cleanup_func = Mock()
        
        # 注册资源
        self.manager.register_resource(
            "test_resource", ResourceType.CUSTOM, mock_obj, cleanup_func
        )
        
        # 清理资源
        result = self.manager.cleanup_resource("test_resource")
        self.assertTrue(result)
        cleanup_func.assert_called_once()
        
        # 验证资源标记为已清理
        resource_info = self.manager.resources["test_resource"]
        self.assertTrue(resource_info.is_cleaned)
        
        # 再次清理已清理的资源
        cleanup_func.reset_mock()
        result = self.manager.cleanup_resource("test_resource")
        self.assertTrue(result)
        cleanup_func.assert_not_called()  # 不应该再次调用
    
    def test_cleanup_resource_with_exception(self):
        """测试清理资源时发生异常"""
        mock_obj = Mock()
        cleanup_func = Mock(side_effect=Exception("Cleanup failed"))
        
        # 注册资源
        self.manager.register_resource(
            "test_resource", ResourceType.CUSTOM, mock_obj, cleanup_func
        )
        
        # 清理资源（应该处理异常）
        result = self.manager.cleanup_resource("test_resource")
        self.assertFalse(result)
        cleanup_func.assert_called_once()
    
    def test_cleanup_by_type(self):
        """测试按类型清理资源"""
        # 注册不同类型的资源
        timer_cleanup = Mock()
        custom_cleanup1 = Mock()
        custom_cleanup2 = Mock()
        
        self.manager.register_resource(
            "timer1", ResourceType.TIMER, Mock(), timer_cleanup
        )
        self.manager.register_resource(
            "custom1", ResourceType.CUSTOM, Mock(), custom_cleanup1
        )
        self.manager.register_resource(
            "custom2", ResourceType.CUSTOM, Mock(), custom_cleanup2
        )
        
        # 按类型清理
        cleaned_count = self.manager.cleanup_by_type(ResourceType.CUSTOM)
        self.assertEqual(cleaned_count, 2)
        
        # 验证只有CUSTOM类型的资源被清理
        custom_cleanup1.assert_called_once()
        custom_cleanup2.assert_called_once()
        timer_cleanup.assert_not_called()
    
    def test_cleanup_all(self):
        """测试清理所有资源"""
        # 注册多种类型的资源
        timer_cleanup = Mock()
        thread_cleanup = Mock()
        custom_cleanup = Mock()
        
        self.manager.register_resource(
            "timer1", ResourceType.TIMER, Mock(), timer_cleanup
        )
        self.manager.register_resource(
            "thread1", ResourceType.THREAD, Mock(), thread_cleanup
        )
        self.manager.register_resource(
            "custom1", ResourceType.CUSTOM, Mock(), custom_cleanup
        )
        
        # 清理所有资源
        cleaned_count = self.manager.cleanup_all()
        self.assertEqual(cleaned_count, 3)
        
        # 验证所有清理函数都被调用
        timer_cleanup.assert_called_once()
        thread_cleanup.assert_called_once()
        custom_cleanup.assert_called_once()
    
    def test_get_resource_stats(self):
        """测试获取资源统计信息"""
        # 注册一些资源
        self.manager.register_resource(
            "timer1", ResourceType.TIMER, Mock(), Mock()
        )
        self.manager.register_resource(
            "custom1", ResourceType.CUSTOM, Mock(), Mock()
        )
        self.manager.register_resource(
            "custom2", ResourceType.CUSTOM, Mock(), Mock()
        )
        
        # 清理一个资源
        self.manager.cleanup_resource("custom1")
        
        # 获取统计信息
        stats = self.manager.get_resource_stats()
        
        self.assertEqual(stats['total_resources'], 3)
        self.assertEqual(stats['cleaned_resources'], 1)
        self.assertEqual(stats['pending_resources'], 2)
        
        # 检查类型统计
        self.assertIn(ResourceType.TIMER, stats['type_stats'])
        self.assertIn(ResourceType.CUSTOM, stats['type_stats'])
        self.assertEqual(stats['type_stats'][ResourceType.TIMER]['total'], 1)
        self.assertEqual(stats['type_stats'][ResourceType.CUSTOM]['total'], 2)
        self.assertEqual(stats['type_stats'][ResourceType.CUSTOM]['cleaned'], 1)
    
    def test_list_resources(self):
        """测试列出资源"""
        # 注册一些资源
        self.manager.register_resource(
            "timer1", ResourceType.TIMER, Mock(), Mock(), "Timer resource"
        )
        self.manager.register_resource(
            "custom1", ResourceType.CUSTOM, Mock(), Mock(), "Custom resource"
        )
        
        # 列出所有资源
        all_resources = self.manager.list_resources()
        self.assertEqual(len(all_resources), 2)
        
        # 按类型列出资源
        timer_resources = self.manager.list_resources(ResourceType.TIMER)
        self.assertEqual(len(timer_resources), 1)
        self.assertEqual(timer_resources[0]['resource_id'], "timer1")
        self.assertEqual(timer_resources[0]['description'], "Timer resource")
    
    def test_thread_safety(self):
        """测试线程安全性"""
        results = []
        
        def register_resources(start_id):
            for i in range(10):
                resource_id = f"resource_{start_id}_{i}"
                result = self.manager.register_resource(
                    resource_id, ResourceType.CUSTOM, Mock(), Mock()
                )
                results.append(result)
        
        # 创建多个线程同时注册资源
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_resources, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有注册都成功
        self.assertEqual(len(results), 50)
        self.assertTrue(all(results))
        self.assertEqual(len(self.manager.resources), 50)


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""
    
    def setUp(self):
        """测试前设置"""
        ResourceManager._instance = None
        self.manager = ResourceManager()
    
    def tearDown(self):
        """测试后清理"""
        self.manager.cleanup_all()
        ResourceManager._instance = None
    
    @patch('app.common.resource_manager.QTimer')
    def test_register_timer(self, mock_timer_class):
        """测试注册QTimer"""
        mock_timer = Mock()
        mock_timer.isActive.return_value = True
        mock_timer_class.return_value = mock_timer
        
        # 创建真实的QTimer对象用于测试
        timer = mock_timer
        
        result = register_timer("test_timer", timer, "Test timer")
        self.assertTrue(result)
        
        # 验证资源被注册
        self.assertIn("test_timer", self.manager.resources)
        resource_info = self.manager.resources["test_timer"]
        self.assertEqual(resource_info.resource_type, ResourceType.TIMER)
        
        # 测试清理
        self.manager.cleanup_resource("test_timer")
        timer.stop.assert_called_once()
    
    def test_register_custom_resource(self):
        """测试注册自定义资源"""
        mock_obj = Mock()
        cleanup_func = Mock()
        
        result = register_custom_resource(
            "custom_resource", mock_obj, cleanup_func, "Custom resource"
        )
        self.assertTrue(result)
        
        # 验证资源被注册
        self.assertIn("custom_resource", self.manager.resources)
        resource_info = self.manager.resources["custom_resource"]
        self.assertEqual(resource_info.resource_type, ResourceType.CUSTOM)
        self.assertEqual(resource_info.cleanup_func, cleanup_func)
    
    @patch('app.common.resource_manager.resource_manager')
    def test_cleanup_on_exit(self, mock_manager):
        """测试退出时清理函数"""
        cleanup_on_exit()
        mock_manager.cleanup_all.assert_called_once()


if __name__ == '__main__':
    unittest.main()
