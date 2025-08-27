"""
Memory Optimizer - 内存优化工具
提供对象池、内存监控和优化策略
"""

import gc
import threading
import time
import weakref
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Type, TypeVar

import psutil

from .logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


@dataclass
class MemoryStats:
    """内存统计信息"""
    rss_mb: float
    vms_mb: float
    percent: float
    gc_objects: int
    timestamp: float = field(default_factory=time.time)


class ObjectPool(Generic[T]):
    """对象池 - 重用对象以减少内存分配"""

    def __init__(self, factory: Callable[[], T], max_size: int = 100) -> None:
        self.factory = factory
        self.max_size = max_size
        self.pool: deque[T] = deque()
        self.lock = threading.Lock()
        self.created_count = 0
        self.reused_count = 0
        self.logger = logger.bind(component="ObjectPool")

    def acquire(self) -> T:
        """获取对象"""
        with self.lock:
            if self.pool:
                obj = self.pool.popleft()
                self.reused_count += 1
                return obj
            else:
                obj = self.factory()
                self.created_count += 1
                return obj

    def release(self, obj: T) -> None:
        """释放对象回池中"""
        with self.lock:
            if len(self.pool) < self.max_size:
                # 重置对象状态（如果有reset方法）
                if hasattr(obj, 'reset'):
                    obj.reset()
                self.pool.append(obj)

    def get_stats(self) -> Dict[str, Any]:
        """获取池统计信息"""
        with self.lock:
            return {
                "pool_size": len(self.pool),
                "max_size": self.max_size,
                "created_count": self.created_count,
                "reused_count": self.reused_count,
                "reuse_ratio": self.reused_count / max(1, self.created_count + self.reused_count)
            }


class MemoryMonitor:
    """内存监控器"""

    def __init__(self, check_interval: float = 60.0) -> None:
        self.check_interval = check_interval
        self.memory_history: deque = deque(maxlen=100)
        self.weak_refs: Set[weakref.ref] = set()
        self.object_counts: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
        self.logger = logger.bind(component="MemoryMonitor")

        # 内存阈值
        self.warning_threshold_mb = 500  # 500MB
        self.critical_threshold_mb = 1000  # 1GB

        self.last_check = time.time()

    def track_object(self, obj: Any) -> None:
        """跟踪对象"""
        with self.lock:
            obj_type = type(obj).__name__
            self.object_counts[obj_type] += 1

            # 创建弱引用
            def cleanup_callback(ref: Any) -> None:
                with self.lock:
                    self.weak_refs.discard(ref)
                    self.object_counts[obj_type] -= 1

            weak_ref = weakref.ref(obj, cleanup_callback)
            self.weak_refs.add(weak_ref)

    def get_memory_stats(self) -> MemoryStats:
        """获取当前内存统计"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            stats = MemoryStats(
                rss_mb=memory_info.rss / 1024 / 1024,
                vms_mb=memory_info.vms / 1024 / 1024,
                percent=process.memory_percent(),
                gc_objects=len(gc.get_objects())
            )

            with self.lock:
                self.memory_history.append(stats)

            return stats

        except Exception as e:
            self.logger.error(f"获取内存统计失败: {e}")
            return MemoryStats(0, 0, 0, 0)

    def check_memory_pressure(self) -> bool:
        """检查内存压力"""
        current_time = time.time()
        if current_time - self.last_check < self.check_interval:
            return False

        stats = self.get_memory_stats()
        self.last_check = current_time

        if stats.rss_mb > self.critical_threshold_mb:
            self.logger.critical(f"内存使用严重过高: {stats.rss_mb:.1f}MB")
            return True
        elif stats.rss_mb > self.warning_threshold_mb:
            self.logger.warning(f"内存使用过高: {stats.rss_mb:.1f}MB")
            return True

        return False

    def get_object_counts(self) -> Dict[str, int]:
        """获取对象计数"""
        with self.lock:
            return dict(self.object_counts)

    def force_gc(self) -> Dict[str, int]:
        """强制垃圾回收"""
        before_objects = len(gc.get_objects())

        # 执行垃圾回收
        collected = gc.collect()

        after_objects = len(gc.get_objects())

        result = {
            "collected": collected,
            "before_objects": before_objects,
            "after_objects": after_objects,
            "freed_objects": before_objects - after_objects
        }

        self.logger.info(f"强制垃圾回收完成: {result}")
        return result


class MemoryOptimizer:
    """内存优化器 - 统一内存优化管理"""

    def __init__(self) -> None:
        self.monitor = MemoryMonitor()
        self.object_pools: Dict[str, ObjectPool] = {}
        self.optimization_strategies: List[Callable] = []
        self.lock = threading.Lock()
        self.logger = logger.bind(component="MemoryOptimizer")

        # 注册默认优化策略
        self._register_default_strategies()

    def create_object_pool(self, name: str, factory: Callable[[], T], max_size: int = 100) -> ObjectPool:
        """创建对象池"""
        with self.lock:
            if name in self.object_pools:
                self.logger.warning(f"对象池 {name} 已存在")
                return self.object_pools[name]

            pool = ObjectPool(factory, max_size)
            self.object_pools[name] = pool
            self.logger.info(f"创建对象池: {name}, 最大大小: {max_size}")
            return pool

    def get_object_pool(self, name: str) -> Optional[ObjectPool]:
        """获取对象池"""
        with self.lock:
            return self.object_pools.get(name)

    def register_optimization_strategy(self, strategy: Callable) -> None:
        """注册优化策略"""
        self.optimization_strategies.append(strategy)
        self.logger.debug(f"注册优化策略: {strategy.__name__}")

    def optimize_memory(self) -> Dict[str, Any]:
        """执行内存优化"""
        optimization_results: Dict[str, Any] = {
            "strategies_executed": 0,
            "memory_before": 0,
            "memory_after": 0,
            "memory_freed": 0,
            "gc_result": {},
            "pool_stats": {}
        }

        try:
            # 记录优化前内存
            before_stats = self.monitor.get_memory_stats()
            optimization_results["memory_before"] = before_stats.rss_mb

            # 执行优化策略
            for strategy in self.optimization_strategies:
                try:
                    strategy()
                    optimization_results["strategies_executed"] += 1
                except Exception as e:
                    self.logger.error(f"执行优化策略失败 {strategy.__name__}: {e}")

            # 强制垃圾回收
            optimization_results["gc_result"] = self.monitor.force_gc()

            # 记录优化后内存
            after_stats = self.monitor.get_memory_stats()
            optimization_results["memory_after"] = after_stats.rss_mb
            optimization_results["memory_freed"] = before_stats.rss_mb - \
                after_stats.rss_mb

            # 获取对象池统计
            with self.lock:
                optimization_results["pool_stats"] = {
                    name: pool.get_stats()
                    for name, pool in self.object_pools.items()
                }

            self.logger.info(f"内存优化完成: {optimization_results}")
            return optimization_results

        except Exception as e:
            self.logger.error(f"内存优化失败: {e}")
            return optimization_results

    def _register_default_strategies(self) -> None:
        """注册默认优化策略"""
        def clear_weak_refs() -> None:
            """清理失效的弱引用"""
            dead_refs = []
            with self.monitor.lock:
                for ref in self.monitor.weak_refs:
                    if ref() is None:
                        dead_refs.append(ref)

                for ref in dead_refs:
                    self.monitor.weak_refs.discard(ref)

        def optimize_caches() -> None:
            """优化缓存"""
            try:
                from .cache_manager import global_cache_manager
                # 清理过期缓存
                for cache in global_cache_manager.caches.values():
                    cache.cleanup_expired()
            except ImportError:
                pass

        self.register_optimization_strategy(clear_weak_refs)
        self.register_optimization_strategy(optimize_caches)


# 全局内存优化器实例
global_memory_optimizer = MemoryOptimizer()


# 便捷函数
def create_object_pool(name: str, factory: Callable[[], T], max_size: int = 100) -> ObjectPool:
    """创建对象池的便捷函数"""
    return global_memory_optimizer.create_object_pool(name, factory, max_size)


def get_object_pool(name: str) -> Optional[ObjectPool]:
    """获取对象池的便捷函数"""
    return global_memory_optimizer.get_object_pool(name)


def optimize_memory() -> Dict[str, Any]:
    """执行内存优化的便捷函数"""
    return global_memory_optimizer.optimize_memory()


def track_object(obj: Any) -> None:
    """跟踪对象的便捷函数"""
    global_memory_optimizer.monitor.track_object(obj)
