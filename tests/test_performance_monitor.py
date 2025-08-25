"""
Performance Monitor Tests
测试性能监控组件的功能和可靠性
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from collections import deque

# 添加项目根目录到路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.heal.components.module.performance_monitor import (
    MetricType, MetricValue, PerformanceMetric, PerformanceAlert,
    SystemResourceMonitor, PerformanceMonitor, ModulePerformanceTracker
)


class TestMetricValue(unittest.TestCase):
    """测试MetricValue类"""
    
    def test_metric_value_creation(self) -> None:
        """测试MetricValue创建"""
        tags = {"module": "test", "operation": "load"}
        value = MetricValue(100.5, time.time(), tags)
        
        self.assertEqual(value.value, 100.5)
        self.assertIsInstance(value.timestamp, float)
        self.assertEqual(value.tags, tags)


class TestPerformanceMetric(unittest.TestCase):
    """测试PerformanceMetric类"""
    
    def test_metric_creation(self) -> None:
        """测试性能指标创建"""
        metric = PerformanceMetric(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test metric",
            unit="ms"
        )
        
        self.assertEqual(metric.name, "test_metric")
        self.assertEqual(metric.type, MetricType.GAUGE)
        self.assertEqual(metric.description, "Test metric")
        self.assertEqual(metric.unit, "ms")
        self.assertIsInstance(metric.values, deque)
        self.assertEqual(len(metric.values), 0)
    
    def test_add_value(self) -> None:
        """测试添加指标值"""
        metric = PerformanceMetric(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test metric",
            unit="ms"
        )
        
        tags = {"test": "value"}
        metric.add_value(50.0, tags)
        
        self.assertEqual(len(metric.values), 1)
        self.assertEqual(metric.values[0].value, 50.0)
        self.assertEqual(metric.values[0].tags, tags)
    
    def test_latest_value(self) -> None:
        """测试获取最新值"""
        metric = PerformanceMetric(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test metric",
            unit="ms"
        )
        
        # 空指标
        self.assertIsNone(metric.latest_value)
        
        # 添加值
        metric.add_value(10.0)
        metric.add_value(20.0)
        metric.add_value(30.0)
        
        self.assertEqual(metric.latest_value, 30.0)
    
    def test_average_value(self) -> None:
        """测试获取平均值"""
        metric = PerformanceMetric(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test metric",
            unit="ms"
        )
        
        # 空指标
        self.assertIsNone(metric.average_value)
        
        # 添加值
        metric.add_value(10.0)
        metric.add_value(20.0)
        metric.add_value(30.0)
        
        self.assertEqual(metric.average_value, 20.0)
    
    def test_min_max_values(self) -> None:
        """测试获取最小值和最大值"""
        metric = PerformanceMetric(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test metric",
            unit="ms"
        )
        
        # 空指标
        self.assertIsNone(metric.min_value)
        self.assertIsNone(metric.max_value)
        
        # 添加值
        metric.add_value(30.0)
        metric.add_value(10.0)
        metric.add_value(20.0)
        
        self.assertEqual(metric.min_value, 10.0)
        self.assertEqual(metric.max_value, 30.0)
    
    @patch('time.time')
    def test_cleanup_old_data(self, mock_time) -> None:
        """测试清理旧数据"""
        metric = PerformanceMetric(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test metric",
            unit="ms",
            max_age_seconds=3600  # 1小时
        )
        
        # 模拟时间
        current_time = 1000000
        mock_time.return_value = current_time
        
        # 添加一些旧数据
        old_time = current_time - 7200  # 2小时前
        metric.values.append(MetricValue(10.0, old_time, {}))
        metric.values.append(MetricValue(20.0, old_time + 1800, {}))  # 1.5小时前
        
        # 添加新数据
        metric.add_value(30.0)
        
        # 验证旧数据被清理
        self.assertEqual(len(metric.values), 1)
        self.assertEqual(metric.values[0].value, 30.0)


class TestPerformanceAlert(unittest.TestCase):
    """测试PerformanceAlert类"""
    
    def test_alert_creation(self) -> None:
        """测试告警创建"""
        condition = lambda x: x > 80
        alert = PerformanceAlert(
            name="high_cpu",
            condition=condition,
            message="CPU usage too high",
            severity="warning"
        )
        
        self.assertEqual(alert.name, "high_cpu")
        self.assertEqual(alert.condition, condition)
        self.assertEqual(alert.message, "CPU usage too high")
        self.assertEqual(alert.severity, "warning")
        self.assertFalse(alert.triggered)
        self.assertEqual(alert.trigger_count, 0)
    
    def test_alert_check(self) -> None:
        """测试告警检查"""
        alert = PerformanceAlert(
            name="high_cpu",
            condition=lambda x: x > 80,
            message="CPU usage too high"
        )
        
        # 不触发告警
        result = alert.check(70.0)
        self.assertFalse(result)
        self.assertFalse(alert.triggered)
        self.assertEqual(alert.trigger_count, 0)
        
        # 触发告警
        result = alert.check(90.0)
        self.assertTrue(result)
        self.assertTrue(alert.triggered)
        self.assertEqual(alert.trigger_count, 1)
        
        # 再次检查（已触发状态）
        result = alert.check(95.0)
        self.assertFalse(result)  # 不会重复触发
        self.assertEqual(alert.trigger_count, 1)
        
        # 恢复正常
        result = alert.check(70.0)
        self.assertFalse(result)
        self.assertFalse(alert.triggered)
        
        # 再次触发
        result = alert.check(85.0)
        self.assertTrue(result)
        self.assertEqual(alert.trigger_count, 2)


class TestSystemResourceMonitor(unittest.TestCase):
    """测试SystemResourceMonitor类"""
    
    @patch('psutil.Process')
    def test_monitor_creation(self, mock_process_class) -> None:
        """测试监控器创建"""
        mock_process = Mock()
        mock_process_class.return_value = mock_process
        
        monitor = SystemResourceMonitor()
        self.assertEqual(monitor.process, mock_process)
    
    @patch('psutil.Process')
    def test_get_cpu_usage(self, mock_process_class) -> None:
        """测试获取CPU使用率"""
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 75.5
        mock_process_class.return_value = mock_process
        
        monitor = SystemResourceMonitor()
        cpu_usage = monitor.get_cpu_usage()
        
        self.assertEqual(cpu_usage, 75.5)
        mock_process.cpu_percent.assert_called_once()
    
    @patch('psutil.Process')
    def test_get_memory_usage(self, mock_process_class) -> None:
        """测试获取内存使用情况"""
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 100  # 100MB
        mock_memory_info.vms = 1024 * 1024 * 200  # 200MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 15.5
        mock_process_class.return_value = mock_process
        
        monitor = SystemResourceMonitor()
        memory_usage = monitor.get_memory_usage()
        
        self.assertEqual(memory_usage['rss'], 100.0)  # MB
        self.assertEqual(memory_usage['vms'], 200.0)  # MB
        self.assertEqual(memory_usage['percent'], 15.5)
    
    @patch('psutil.Process')
    def test_get_thread_count(self, mock_process_class) -> None:
        """测试获取线程数"""
        mock_process = Mock()
        mock_process.num_threads.return_value = 25
        mock_process_class.return_value = mock_process
        
        monitor = SystemResourceMonitor()
        thread_count = monitor.get_thread_count()
        
        self.assertEqual(thread_count, 25)
        mock_process.num_threads.assert_called_once()


class TestPerformanceMonitor(unittest.TestCase):
    """测试PerformanceMonitor类"""
    
    def setUp(self) -> None:
        """测试前设置"""
        # 使用较短的更新间隔进行测试
        self.monitor = PerformanceMonitor(update_interval=100)
    
    def tearDown(self) -> None:
        """测试后清理"""
        if self.monitor.running:
            self.monitor.stop_monitoring()
    
    def test_monitor_initialization(self) -> None:
        """测试监控器初始化"""
        self.assertEqual(self.monitor.update_interval, 100)
        self.assertIsInstance(self.monitor.metrics, dict)
        self.assertIsInstance(self.monitor.alerts, dict)
        self.assertFalse(self.monitor.running)
        
        # 检查默认指标是否注册
        self.assertIn("cpu_usage", self.monitor.metrics)
        self.assertIn("memory_rss", self.monitor.metrics)
        self.assertIn("memory_percent", self.monitor.metrics)
        
        # 检查默认告警是否设置
        self.assertIn("high_cpu_usage", self.monitor.alerts)
        self.assertIn("high_memory_usage", self.monitor.alerts)
    
    def test_register_metric(self) -> None:
        """测试注册指标"""
        self.monitor.register_metric(
            "custom_metric",
            MetricType.COUNTER,
            "Custom test metric",
            "count"
        )
        
        self.assertIn("custom_metric", self.monitor.metrics)
        metric = self.monitor.metrics["custom_metric"]
        self.assertEqual(metric.name, "custom_metric")
        self.assertEqual(metric.type, MetricType.COUNTER)
        self.assertEqual(metric.description, "Custom test metric")
        self.assertEqual(metric.unit, "count")
    
    def test_add_alert(self) -> None:
        """测试添加告警"""
        self.monitor.add_alert(
            "custom_alert",
            lambda x: x > 100,
            "Custom alert message",
            "critical"
        )
        
        self.assertIn("custom_alert", self.monitor.alerts)
        alert = self.monitor.alerts["custom_alert"]
        self.assertEqual(alert.name, "custom_alert")
        self.assertEqual(alert.message, "Custom alert message")
        self.assertEqual(alert.severity, "critical")
    
    def test_record_metric(self) -> None:
        """测试记录指标"""
        # 注册一个测试指标
        self.monitor.register_metric(
            "test_metric",
            MetricType.GAUGE,
            "Test metric",
            "ms"
        )
        
        # 记录指标值
        tags = {"test": "value"}
        self.monitor.record_metric("test_metric", 50.0, tags)
        
        # 验证指标被记录
        metric = self.monitor.metrics["test_metric"]
        self.assertEqual(len(metric.values), 1)
        self.assertEqual(metric.values[0].value, 50.0)
        self.assertEqual(metric.values[0].tags, tags)
    
    def test_record_metric_with_alert(self) -> None:
        """测试记录指标并触发告警"""
        # 注册指标和告警
        self.monitor.register_metric(
            "test_metric",
            MetricType.GAUGE,
            "Test metric",
            "percent"
        )
        self.monitor.add_alert(
            "test_alert",
            lambda x: x > 80,
            "Test alert triggered"
        )
        
        # 记录不触发告警的值
        self.monitor.record_metric("test_metric", 70.0)
        alert = self.monitor.alerts["test_alert"]
        self.assertFalse(alert.triggered)
        
        # 记录触发告警的值
        self.monitor.record_metric("test_metric", 90.0)
        self.assertTrue(alert.triggered)
        self.assertEqual(alert.trigger_count, 1)
    
    def test_get_metric(self) -> None:
        """测试获取指标"""
        # 获取存在的指标
        metric = self.monitor.get_metric("cpu_usage")
        self.assertIsNotNone(metric)
        self.assertEqual(metric.name, "cpu_usage")
        
        # 获取不存在的指标
        metric = self.monitor.get_metric("nonexistent_metric")
        self.assertIsNone(metric)
    
    def test_get_metric_summary(self) -> None:
        """测试获取指标摘要"""
        # 添加一些数据
        self.monitor.record_metric("cpu_usage", 50.0)
        self.monitor.record_metric("cpu_usage", 60.0)
        self.monitor.record_metric("cpu_usage", 70.0)
        
        summary = self.monitor.get_metric_summary("cpu_usage")
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary['name'], "cpu_usage")
        self.assertEqual(summary['latest_value'], 70.0)
        self.assertEqual(summary['average_value'], 60.0)
        self.assertEqual(summary['min_value'], 50.0)
        self.assertEqual(summary['max_value'], 70.0)
        self.assertEqual(summary['sample_count'], 3)
    
    def test_memory_management(self) -> None:
        """测试内存管理功能"""
        # 配置较小的内存限制
        self.monitor.configure_memory_limits(1, 0.5)  # 1MB最大，0.5MB清理阈值
        
        # 获取内存统计
        stats = self.monitor.get_memory_stats()
        
        self.assertIn('total_metrics', stats)
        self.assertIn('total_values', stats)
        self.assertIn('estimated_memory_mb', stats)
        self.assertIn('memory_usage_percent', stats)
    
    def test_thread_safety(self) -> None:
        """测试线程安全性"""
        results = []
        
        def record_metrics() -> None:
            for i in range(10):
                self.monitor.record_metric("cpu_usage", float(i))
                results.append(i)
        
        # 创建多个线程同时记录指标
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=record_metrics)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有记录都成功
        self.assertEqual(len(results), 50)
        metric = self.monitor.get_metric("cpu_usage")
        self.assertEqual(len(metric.values), 50)


class TestModulePerformanceTracker(unittest.TestCase):
    """测试ModulePerformanceTracker类"""
    
    def setUp(self) -> None:
        """测试前设置"""
        self.monitor = PerformanceMonitor()
        self.tracker = ModulePerformanceTracker(self.monitor)
    
    def tearDown(self) -> None:
        """测试后清理"""
        if self.monitor.running:
            self.monitor.stop_monitoring()
    
    def test_track_module_operation(self) -> None:
        """测试跟踪模块操作"""
        self.tracker.track_module_operation("test_module", "load")
        
        # 验证统计信息被更新
        stats = self.tracker.get_module_stats("test_module")
        self.assertIsNotNone(stats)
        self.assertEqual(stats['operation_count'], 1)
    
    def test_track_module_error(self) -> None:
        """测试跟踪模块错误"""
        # 先进行一些操作
        self.tracker.track_module_operation("test_module", "load")
        self.tracker.track_module_operation("test_module", "execute")
        
        # 记录错误
        self.tracker.track_module_error("test_module", "Test error")
        
        # 验证错误统计
        stats = self.tracker.get_module_stats("test_module")
        self.assertEqual(stats['error_count'], 1)
        self.assertEqual(stats['operation_count'], 2)
    
    def test_track_module_load_context(self) -> None:
        """测试模块加载上下文"""
        with self.tracker.track_module_load("test_module"):
            time.sleep(0.01)  # 模拟加载时间
        
        # 验证加载统计
        stats = self.tracker.get_module_stats("test_module")
        self.assertEqual(stats['load_count'], 1)
        self.assertGreater(stats['last_load_time'], 0)
    
    def test_get_all_module_stats(self) -> None:
        """测试获取所有模块统计"""
        # 跟踪多个模块
        self.tracker.track_module_operation("module1", "load")
        self.tracker.track_module_operation("module2", "execute")
        
        all_stats = self.tracker.get_all_module_stats()
        
        self.assertIn("module1", all_stats)
        self.assertIn("module2", all_stats)
        self.assertEqual(len(all_stats), 2)


if __name__ == '__main__':
    unittest.main()
