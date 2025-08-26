"""
Cache Manager - 缓存管理器
实现智能缓存机制，减少重复计算和IO操作
"""

import hashlib
import pickle
import threading
import time
import weakref
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .logging_config import get_logger
from .performance_analyzer import profile_performance

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None  # 生存时间(秒)
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self) -> None:
        """更新访问时间"""
        self.last_accessed = time.time()
        self.access_count += 1


class CacheStats:
    """缓存统计"""

    def __init__(self) -> None:
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.size_bytes = 0
        self.entry_count = 0

    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": self.hit_rate,
            "size_bytes": self.size_bytes,
            "entry_count": self.entry_count,
        }


class LRUCache:
    """LRU缓存实现"""

    def __init__(self, max_size: int = 1000, max_memory_mb: float = 100) -> None:
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = CacheStats()
        self.lock = threading.RLock()
        self.logger = logger.bind(component="LRUCache")

    @profile_performance(threshold=0.001)  # 监控缓存操作性能
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            entry = self.cache.get(key)

            if entry is None:
                self.stats.misses += 1
                self._record_cache_stats()
                return None

            if entry.is_expired():
                self._remove_entry(key)
                self.stats.misses += 1
                self._record_cache_stats()
                return None

            entry.touch()
            self.stats.hits += 1
            self._record_cache_stats()
            return entry.value

    @profile_performance(threshold=0.001)
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """设置缓存值"""
        with self.lock:
            # 计算值的大小
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = 0

            # 检查内存限制
            if size_bytes > self.max_memory_bytes:
                self.logger.warning(f"缓存值过大，拒绝缓存: {size_bytes} bytes")
                return False

            # 如果键已存在，先移除旧条目
            if key in self.cache:
                self._remove_entry(key)

            # 确保有足够空间
            self._ensure_capacity(size_bytes)

            # 创建新条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                ttl=ttl,
                size_bytes=size_bytes,
            )

            self.cache[key] = entry
            self.stats.size_bytes += size_bytes
            self.stats.entry_count += 1

            return True

    def remove(self, key: str) -> bool:
        """移除缓存条目"""
        with self.lock:
            if key in self.cache:
                self._remove_entry(key)
                return True
            return False

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.stats = CacheStats()

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items() if entry.is_expired()
            ]

            for key in expired_keys:
                self._remove_entry(key)

            if expired_keys:
                self.logger.debug(f"清理了 {len(expired_keys)} 个过期缓存条目")

                # 记录内存优化统计
                try:
                    from .memory_optimizer import global_memory_optimizer
                    global_memory_optimizer.monitor.get_memory_stats()
                except ImportError:
                    pass

            return len(expired_keys)

    def _remove_entry(self, key: str) -> None:
        """移除条目（内部方法）"""
        entry = self.cache.pop(key, None)
        if entry:
            self.stats.size_bytes -= entry.size_bytes
            self.stats.entry_count -= 1
            self.stats.evictions += 1

    def _ensure_capacity(self, new_size: int) -> None:
        """确保有足够的容量 - 优化版本"""
        # 检查数量限制
        while len(self.cache) >= self.max_size:
            if not self._evict_lru():
                break

        # 检查内存限制
        while (self.stats.size_bytes + new_size) > self.max_memory_bytes:
            if not self._evict_lru():
                # 如果无法释放更多空间，尝试强制垃圾回收
                import gc
                collected = gc.collect()
                self.logger.debug(f"强制垃圾回收释放了 {collected} 个对象")

                # 再次尝试释放空间
                if not self._evict_lru():
                    break  # 无法释放更多空间

    def _evict_lru(self) -> bool:
        """驱逐最近最少使用的条目"""
        if not self.cache:
            return False

        # 找到最近最少使用的条目
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_accessed)

        self._remove_entry(lru_key)
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            return self.stats.to_dict()

    def _record_cache_stats(self) -> None:
        """记录缓存统计到性能分析器"""
        try:
            # 导入性能分析器（避免循环导入）
            from .performance_analyzer import global_performance_analyzer

            # 记录缓存统计
            cache_name = f"{self.__class__.__name__}_{id(self)}"
            global_performance_analyzer.record_cache_stats(
                cache_name,
                self.stats.hits,
                self.stats.misses
            )
        except ImportError:
            # 如果性能分析器不可用，静默忽略
            pass


class FileCache(LRUCache):
    """文件缓存 - 专门用于缓存文件内容"""

    def __init__(self, max_size: int = 500, max_memory_mb: float = 50) -> None:
        super().__init__(max_size, max_memory_mb)
        self.logger = logger.bind(component="FileCache")

    def get_file_content(
        self, file_path: Union[str, Path], encoding: str = "utf-8"
    ) -> Optional[str]:
        """获取文件内容（带缓存）"""
        file_path = Path(file_path)

        # 生成缓存键（包含文件路径和修改时间）
        try:
            mtime = file_path.stat().st_mtime
            cache_key = f"file:{file_path}:{mtime}:{encoding}"
        except OSError:
            return None

        # 尝试从缓存获取
        content = self.get(cache_key)
        if content is not None:
            return str(content)

        # 读取文件并缓存
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()

            # 缓存文件内容（1小时TTL）
            self.put(cache_key, content, ttl=3600)
            return content

        except Exception as e:
            self.logger.error(f"读取文件失败 {file_path}: {e}")
            return None

    async def get_file_content_async(
        self, file_path: Union[str, Path], encoding: str = "utf-8"
    ) -> Optional[str]:
        """异步获取文件内容（带缓存）"""
        file_path = Path(file_path)

        # 生成缓存键（包含文件路径和修改时间）
        try:
            mtime = file_path.stat().st_mtime
            cache_key = f"file:{file_path}:{mtime}:{encoding}"
        except OSError:
            return None

        # 尝试从缓存获取
        content = self.get(cache_key)
        if content is not None:
            return str(content)

        # 异步读取文件并缓存
        try:
            from .async_io_utils import global_async_file_manager
            result = await global_async_file_manager.read_file_async(file_path, encoding)

            if result.success and result.data is not None:
                content = str(result.data)
                # 缓存文件内容（1小时TTL）
                self.put(cache_key, content, ttl=3600)
                return content
            else:
                self.logger.error(f"异步读取文件失败 {file_path}: {result.error}")
                return None

        except Exception as e:
            self.logger.error(f"异步读取文件失败 {file_path}: {e}")
            return None


class FunctionCache:
    """函数结果缓存装饰器"""

    def __init__(self, cache: LRUCache, ttl: Optional[float] = None) -> None:
        self.cache = cache
        self.ttl = ttl

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 生成缓存键
            cache_key = self._generate_key(func, args, kwargs)

            # 尝试从缓存获取
            result = self.cache.get(cache_key)
            if result is not None:
                return result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            self.cache.put(cache_key, result, self.ttl)

            return result

        return wrapper

    def _generate_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        # 创建包含函数名、参数的唯一键
        key_data = {
            "func": f"{func.__module__}.{func.__qualname__}",
            "args": args,
            "kwargs": sorted(kwargs.items()),
        }

        # 使用pickle序列化并计算哈希
        try:
            serialized = pickle.dumps(key_data)
            return hashlib.md5(serialized).hexdigest()
        except:
            # 如果序列化失败，使用字符串表示
            return hashlib.md5(str(key_data).encode()).hexdigest()


class CacheManager:
    """缓存管理器 - 统一管理多种缓存"""

    def __init__(self) -> None:
        self.caches: Dict[str, LRUCache] = {}
        self.file_cache = FileCache()
        self.function_cache = LRUCache(max_size=2000, max_memory_mb=200)
        self.logger = logger.bind(component="CacheManager")

        # 注册默认缓存
        self.register_cache("file", self.file_cache)
        self.register_cache("function", self.function_cache)

        # 清理定时器
        self.cleanup_interval = 300  # 5分钟
        self.last_cleanup = time.time()

    def register_cache(self, name: str, cache: LRUCache) -> None:
        """注册缓存"""
        self.caches[name] = cache
        self.logger.debug(f"注册缓存: {name}")

    def get_cache(self, name: str) -> Optional[LRUCache]:
        """获取缓存实例"""
        return self.caches.get(name)

    def cached_function(
        self, cache_name: str = "function", ttl: Optional[float] = None
    ) -> FunctionCache:
        """函数缓存装饰器"""
        cache = self.get_cache(cache_name)
        if cache is None:
            raise ValueError(f"缓存不存在: {cache_name}")

        return FunctionCache(cache, ttl)

    def cleanup_all_caches(self) -> Dict[str, int]:
        """清理所有缓存的过期条目"""
        current_time = time.time()

        if current_time - self.last_cleanup < self.cleanup_interval:
            return {}

        cleanup_results = {}

        for name, cache in self.caches.items():
            try:
                cleaned = cache.cleanup_expired()
                cleanup_results[name] = cleaned
            except Exception as e:
                self.logger.error(f"清理缓存失败 {name}: {e}")
                cleanup_results[name] = 0

        self.last_cleanup = current_time

        total_cleaned = sum(cleanup_results.values())
        if total_cleaned > 0:
            self.logger.info(f"缓存清理完成，共清理 {total_cleaned} 个过期条目")

        return cleanup_results

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存的统计信息"""
        stats = {}

        for name, cache in self.caches.items():
            try:
                stats[name] = cache.get_stats()
            except Exception as e:
                self.logger.error(f"获取缓存统计失败 {name}: {e}")
                stats[name] = {"error": str(e)}

        return stats

    def clear_all_caches(self) -> None:
        """清空所有缓存"""
        for name, cache in self.caches.items():
            try:
                cache.clear()
                self.logger.debug(f"清空缓存: {name}")
            except Exception as e:
                self.logger.error(f"清空缓存失败 {name}: {e}")


# 全局缓存管理器实例
global_cache_manager = CacheManager()


# 便捷装饰器
def cached(cache_name: str = "function", ttl: Optional[float] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """缓存装饰器"""
    return global_cache_manager.cached_function(cache_name, ttl)


def get_file_cached(
    file_path: Union[str, Path], encoding: str = "utf-8"
) -> Optional[str]:
    """获取文件内容（带缓存）"""
    return global_cache_manager.file_cache.get_file_content(file_path, encoding)


def cleanup_caches() -> Dict[str, int]:
    """清理所有缓存"""
    return global_cache_manager.cleanup_all_caches()
