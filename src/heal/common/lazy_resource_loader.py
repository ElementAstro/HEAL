"""
Lazy Resource Loader
Provides lazy loading mechanisms for non-critical resources during startup
"""

import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union
from concurrent.futures import ThreadPoolExecutor, Future

from .logging_config import get_logger
from .resource_manager import ResourceManager, ResourceType

logger = get_logger(__name__)


class ResourcePriority(Enum):
    """资源加载优先级"""
    CRITICAL = 1      # 启动时必须加载
    HIGH = 2          # 启动后立即加载
    MEDIUM = 3        # 需要时加载
    LOW = 4           # 后台加载
    ON_DEMAND = 5     # 仅在请求时加载


class LoadingStrategy(Enum):
    """加载策略"""
    IMMEDIATE = "immediate"        # 立即加载
    DEFERRED = "deferred"         # 延迟加载
    LAZY = "lazy"                 # 懒加载
    BACKGROUND = "background"     # 后台加载
    ON_FIRST_ACCESS = "on_first_access"  # 首次访问时加载


@dataclass
class ResourceDescriptor:
    """资源描述符"""
    resource_id: str
    resource_type: str
    loader_func: Callable[[], Any]
    priority: ResourcePriority = ResourcePriority.MEDIUM
    strategy: LoadingStrategy = LoadingStrategy.LAZY
    dependencies: List[str] = field(default_factory=list)
    max_load_time: float = 30.0  # seconds
    cache_result: bool = True
    description: str = ""
    
    # Runtime state
    is_loaded: bool = False
    is_loading: bool = False
    load_error: Optional[Exception] = None
    cached_result: Any = None
    load_time: float = 0.0
    access_count: int = 0
    last_access: float = 0.0


class LazyResourceLoader:
    """懒加载资源管理器"""
    
    def __init__(self, max_workers: int = 4):
        self.logger = logger.bind(component="LazyResourceLoader")
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Resource registry
        self.resources: Dict[str, ResourceDescriptor] = {}
        self.loading_futures: Dict[str, Future] = {}
        self.load_order: List[str] = []
        
        # Synchronization
        self._lock = threading.RLock()
        self._loading_events: Dict[str, threading.Event] = {}
        
        # Statistics
        self.stats = {
            "total_resources": 0,
            "loaded_resources": 0,
            "failed_resources": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_load_time": 0.0,
            "background_loads": 0
        }
        
        # Resource manager integration
        self.resource_manager = ResourceManager()
        
    def register_resource(self, descriptor: ResourceDescriptor) -> None:
        """注册资源"""
        with self._lock:
            if descriptor.resource_id in self.resources:
                self.logger.warning(f"Resource {descriptor.resource_id} already registered, overwriting")
            
            self.resources[descriptor.resource_id] = descriptor
            self._loading_events[descriptor.resource_id] = threading.Event()
            self.stats["total_resources"] += 1
            
            self.logger.debug(f"Registered resource: {descriptor.resource_id} "
                            f"(priority: {descriptor.priority.name}, strategy: {descriptor.strategy.value})")
    
    def register_simple_resource(self, resource_id: str, loader_func: Callable[[], Any],
                                priority: ResourcePriority = ResourcePriority.MEDIUM,
                                strategy: LoadingStrategy = LoadingStrategy.LAZY,
                                description: str = "") -> None:
        """注册简单资源"""
        descriptor = ResourceDescriptor(
            resource_id=resource_id,
            resource_type="generic",
            loader_func=loader_func,
            priority=priority,
            strategy=strategy,
            description=description
        )
        self.register_resource(descriptor)
    
    def get_resource(self, resource_id: str, timeout: Optional[float] = None) -> Any:
        """获取资源（触发加载如果需要）"""
        if resource_id not in self.resources:
            raise ValueError(f"Resource {resource_id} not registered")
        
        descriptor = self.resources[resource_id]
        descriptor.access_count += 1
        descriptor.last_access = time.time()
        
        # Check if already loaded and cached
        if descriptor.is_loaded and descriptor.cache_result and descriptor.cached_result is not None:
            self.stats["cache_hits"] += 1
            self.logger.debug(f"Cache hit for resource: {resource_id}")
            return descriptor.cached_result
        
        self.stats["cache_misses"] += 1
        
        # Check if currently loading
        if descriptor.is_loading:
            self.logger.debug(f"Resource {resource_id} is currently loading, waiting...")
            event = self._loading_events[resource_id]
            if timeout:
                if not event.wait(timeout):
                    raise TimeoutError(f"Timeout waiting for resource {resource_id}")
            else:
                event.wait()
            
            # Check if loading succeeded
            if descriptor.load_error:
                raise descriptor.load_error
            
            return descriptor.cached_result if descriptor.cache_result else None
        
        # Load the resource
        return self._load_resource_sync(resource_id, timeout)
    
    def _load_resource_sync(self, resource_id: str, timeout: Optional[float] = None) -> Any:
        """同步加载资源"""
        descriptor = self.resources[resource_id]
        
        with self._lock:
            # Double-check if already loaded
            if descriptor.is_loaded and descriptor.cache_result and descriptor.cached_result is not None:
                return descriptor.cached_result
            
            if descriptor.is_loading:
                # Another thread is loading, wait for it
                event = self._loading_events[resource_id]
                event.wait(timeout)
                if descriptor.load_error:
                    raise descriptor.load_error
                return descriptor.cached_result if descriptor.cache_result else None
            
            # Mark as loading
            descriptor.is_loading = True
            self._loading_events[resource_id].clear()
        
        try:
            self.logger.debug(f"Loading resource: {resource_id}")
            start_time = time.time()
            
            # Check dependencies
            self._ensure_dependencies_loaded(descriptor)
            
            # Load the resource
            result = descriptor.loader_func()
            
            # Update descriptor
            load_time = time.time() - start_time
            descriptor.load_time = load_time
            descriptor.is_loaded = True
            descriptor.load_error = None
            
            if descriptor.cache_result:
                descriptor.cached_result = result
            
            # Update statistics
            self.stats["loaded_resources"] += 1
            self.stats["total_load_time"] += load_time
            
            self.logger.info(f"Successfully loaded resource: {resource_id} in {load_time:.3f}s")
            
            return result
            
        except Exception as e:
            descriptor.load_error = e
            self.stats["failed_resources"] += 1
            self.logger.error(f"Failed to load resource {resource_id}: {e}")
            raise
        
        finally:
            descriptor.is_loading = False
            self._loading_events[resource_id].set()
    
    def _ensure_dependencies_loaded(self, descriptor: ResourceDescriptor) -> None:
        """确保依赖资源已加载"""
        for dep_id in descriptor.dependencies:
            if dep_id not in self.resources:
                raise ValueError(f"Dependency {dep_id} not registered for resource {descriptor.resource_id}")
            
            dep_descriptor = self.resources[dep_id]
            if not dep_descriptor.is_loaded:
                self.logger.debug(f"Loading dependency {dep_id} for {descriptor.resource_id}")
                self.get_resource(dep_id)
    
    def load_by_priority(self, max_priority: ResourcePriority = ResourcePriority.HIGH) -> Dict[str, bool]:
        """按优先级加载资源"""
        results = {}
        
        # Get resources to load
        resources_to_load = [
            (resource_id, descriptor) for resource_id, descriptor in self.resources.items()
            if descriptor.priority.value <= max_priority.value and not descriptor.is_loaded
        ]
        
        # Sort by priority
        resources_to_load.sort(key=lambda x: x[1].priority.value)
        
        self.logger.info(f"Loading {len(resources_to_load)} resources with priority <= {max_priority.name}")
        
        for resource_id, descriptor in resources_to_load:
            try:
                if descriptor.strategy in [LoadingStrategy.IMMEDIATE, LoadingStrategy.DEFERRED]:
                    self.get_resource(resource_id)
                    results[resource_id] = True
                elif descriptor.strategy == LoadingStrategy.BACKGROUND:
                    self.load_resource_async(resource_id)
                    results[resource_id] = True  # Assume success for async
                else:
                    # Skip lazy and on-demand resources
                    results[resource_id] = None
            except Exception as e:
                results[resource_id] = False
                self.logger.error(f"Failed to load resource {resource_id}: {e}")
        
        return results
    
    def load_resource_async(self, resource_id: str) -> Future:
        """异步加载资源"""
        if resource_id not in self.resources:
            raise ValueError(f"Resource {resource_id} not registered")
        
        descriptor = self.resources[resource_id]
        
        if descriptor.is_loaded and descriptor.cache_result:
            # Already loaded, return completed future
            future = Future()
            future.set_result(descriptor.cached_result)
            return future
        
        if resource_id in self.loading_futures:
            # Already loading
            return self.loading_futures[resource_id]
        
        # Submit to thread pool
        future = self.executor.submit(self._load_resource_sync, resource_id)
        self.loading_futures[resource_id] = future
        self.stats["background_loads"] += 1
        
        # Clean up future when done
        def cleanup(fut):
            if resource_id in self.loading_futures:
                del self.loading_futures[resource_id]
        
        future.add_done_callback(cleanup)
        
        self.logger.debug(f"Started async loading for resource: {resource_id}")
        return future
    
    def preload_critical_resources(self) -> Dict[str, bool]:
        """预加载关键资源"""
        return self.load_by_priority(ResourcePriority.CRITICAL)
    
    def start_background_loading(self) -> None:
        """开始后台加载"""
        background_resources = [
            resource_id for resource_id, descriptor in self.resources.items()
            if descriptor.strategy == LoadingStrategy.BACKGROUND and not descriptor.is_loaded
        ]
        
        self.logger.info(f"Starting background loading for {len(background_resources)} resources")
        
        for resource_id in background_resources:
            self.load_resource_async(resource_id)
    
    def is_resource_loaded(self, resource_id: str) -> bool:
        """检查资源是否已加载"""
        if resource_id not in self.resources:
            return False
        return self.resources[resource_id].is_loaded
    
    def get_loading_stats(self) -> Dict[str, Any]:
        """获取加载统计信息"""
        with self._lock:
            resource_stats = []
            for resource_id, descriptor in self.resources.items():
                resource_stats.append({
                    "resource_id": resource_id,
                    "priority": descriptor.priority.name,
                    "strategy": descriptor.strategy.value,
                    "is_loaded": descriptor.is_loaded,
                    "is_loading": descriptor.is_loading,
                    "load_time": descriptor.load_time,
                    "access_count": descriptor.access_count,
                    "has_error": descriptor.load_error is not None
                })
            
            return {
                **self.stats,
                "resource_details": resource_stats,
                "active_futures": len(self.loading_futures)
            }
    
    def clear_cache(self, resource_id: Optional[str] = None) -> None:
        """清除缓存"""
        with self._lock:
            if resource_id:
                if resource_id in self.resources:
                    descriptor = self.resources[resource_id]
                    descriptor.cached_result = None
                    descriptor.is_loaded = False
                    self.logger.debug(f"Cleared cache for resource: {resource_id}")
            else:
                for descriptor in self.resources.values():
                    descriptor.cached_result = None
                    descriptor.is_loaded = False
                self.logger.debug("Cleared all resource caches")
    
    def shutdown(self) -> None:
        """关闭资源加载器"""
        self.logger.info("Shutting down lazy resource loader")
        
        # Cancel pending futures
        for future in self.loading_futures.values():
            future.cancel()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Clear resources
        self.resources.clear()
        self.loading_futures.clear()
        self._loading_events.clear()


# Global lazy resource loader instance
lazy_resource_loader = LazyResourceLoader()


# Convenience functions
def register_lazy_resource(resource_id: str, loader_func: Callable[[], Any],
                          priority: ResourcePriority = ResourcePriority.MEDIUM,
                          strategy: LoadingStrategy = LoadingStrategy.LAZY,
                          description: str = "") -> None:
    """注册懒加载资源"""
    lazy_resource_loader.register_simple_resource(
        resource_id, loader_func, priority, strategy, description
    )


def get_lazy_resource(resource_id: str, timeout: Optional[float] = None) -> Any:
    """获取懒加载资源"""
    return lazy_resource_loader.get_resource(resource_id, timeout)


def preload_critical_resources() -> Dict[str, bool]:
    """预加载关键资源"""
    return lazy_resource_loader.preload_critical_resources()


def start_background_loading() -> None:
    """开始后台加载"""
    lazy_resource_loader.start_background_loading()


def get_resource_loading_stats() -> Dict[str, Any]:
    """获取资源加载统计"""
    return lazy_resource_loader.get_loading_stats()
