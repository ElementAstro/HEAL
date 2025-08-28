"""
Resource Preloader
Provides preloading system for essential resources needed during startup
"""

import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Set
from concurrent.futures import ThreadPoolExecutor, Future, as_completed

from .logging_config import get_logger
from .lazy_resource_loader import (
    lazy_resource_loader, ResourcePriority, LoadingStrategy, 
    register_lazy_resource
)

logger = get_logger(__name__)


class PreloadCategory(Enum):
    """预加载资源类别"""
    FONTS = "fonts"
    IMAGES = "images"
    TRANSLATIONS = "translations"
    STYLES = "styles"
    AUDIO = "audio"
    CONFIGURATIONS = "configurations"
    TEMPLATES = "templates"
    ICONS = "icons"


@dataclass
class PreloadTask:
    """预加载任务"""
    resource_id: str
    category: PreloadCategory
    loader_func: Callable[[], Any]
    priority: int = 1  # 1 = highest priority
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 30.0
    description: str = ""
    
    # Runtime state
    is_completed: bool = False
    is_failed: bool = False
    load_time: float = 0.0
    error: Optional[Exception] = None
    result: Any = None


class ResourcePreloader:
    """资源预加载器"""
    
    def __init__(self, max_workers: int = 3):
        self.logger = logger.bind(component="ResourcePreloader")
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Preload tasks registry
        self.preload_tasks: Dict[str, PreloadTask] = {}
        self.category_tasks: Dict[PreloadCategory, List[str]] = {}
        
        # Execution state
        self.is_preloading = False
        self.preload_futures: Dict[str, Future] = {}
        self._lock = threading.RLock()
        
        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_preload_time": 0.0,
            "categories_loaded": set(),
            "last_preload_time": None
        }
        
        # Register default critical resources
        self._register_default_resources()
    
    def _register_default_resources(self) -> None:
        """注册默认关键资源"""
        # Font resources
        self.register_preload_task(
            "system_fonts",
            PreloadCategory.FONTS,
            self._load_system_fonts,
            priority=1,
            description="Load system fonts for UI rendering"
        )
        
        # Critical images
        self.register_preload_task(
            "app_icons",
            PreloadCategory.ICONS,
            self._load_app_icons,
            priority=1,
            description="Load application icons"
        )
        
        # Base translations
        self.register_preload_task(
            "base_translations",
            PreloadCategory.TRANSLATIONS,
            self._load_base_translations,
            priority=2,
            description="Load base translation files"
        )
        
        # Critical styles
        self.register_preload_task(
            "base_styles",
            PreloadCategory.STYLES,
            self._load_base_styles,
            priority=2,
            description="Load base stylesheet files"
        )
    
    def register_preload_task(self, resource_id: str, category: PreloadCategory,
                            loader_func: Callable[[], Any], priority: int = 3,
                            dependencies: Optional[List[str]] = None,
                            timeout: float = 30.0, description: str = "") -> None:
        """注册预加载任务"""
        with self._lock:
            if resource_id in self.preload_tasks:
                self.logger.warning(f"Preload task {resource_id} already registered, overwriting")
            
            task = PreloadTask(
                resource_id=resource_id,
                category=category,
                loader_func=loader_func,
                priority=priority,
                dependencies=dependencies or [],
                timeout=timeout,
                description=description
            )
            
            self.preload_tasks[resource_id] = task
            
            # Update category mapping
            if category not in self.category_tasks:
                self.category_tasks[category] = []
            self.category_tasks[category].append(resource_id)
            
            self.stats["total_tasks"] += 1
            
            # Also register with lazy resource loader for on-demand access
            register_lazy_resource(
                resource_id,
                loader_func,
                ResourcePriority.HIGH if priority <= 2 else ResourcePriority.MEDIUM,
                LoadingStrategy.DEFERRED,
                description
            )
            
            self.logger.debug(f"Registered preload task: {resource_id} "
                            f"(category: {category.value}, priority: {priority})")
    
    def preload_by_priority(self, max_priority: int = 2) -> Dict[str, bool]:
        """按优先级预加载资源"""
        if self.is_preloading:
            self.logger.warning("Preloading already in progress")
            return {}
        
        # Get tasks to preload
        tasks_to_load = [
            task for task in self.preload_tasks.values()
            if task.priority <= max_priority and not task.is_completed
        ]
        
        if not tasks_to_load:
            self.logger.info("No tasks to preload")
            return {}
        
        # Sort by priority
        tasks_to_load.sort(key=lambda t: t.priority)
        
        self.logger.info(f"Starting preload of {len(tasks_to_load)} tasks with priority <= {max_priority}")
        
        return self._execute_preload_tasks(tasks_to_load)
    
    def preload_category(self, category: PreloadCategory) -> Dict[str, bool]:
        """预加载指定类别的资源"""
        if category not in self.category_tasks:
            self.logger.warning(f"No tasks registered for category {category.value}")
            return {}
        
        task_ids = self.category_tasks[category]
        tasks_to_load = [
            self.preload_tasks[task_id] for task_id in task_ids
            if not self.preload_tasks[task_id].is_completed
        ]
        
        if not tasks_to_load:
            self.logger.info(f"All tasks in category {category.value} already completed")
            return {}
        
        self.logger.info(f"Starting preload of {len(tasks_to_load)} tasks in category {category.value}")
        
        results = self._execute_preload_tasks(tasks_to_load)
        
        if all(results.values()):
            self.stats["categories_loaded"].add(category)
        
        return results
    
    def preload_all(self) -> Dict[str, bool]:
        """预加载所有注册的资源"""
        tasks_to_load = [
            task for task in self.preload_tasks.values()
            if not task.is_completed
        ]
        
        if not tasks_to_load:
            self.logger.info("All tasks already completed")
            return {}
        
        # Sort by priority
        tasks_to_load.sort(key=lambda t: t.priority)
        
        self.logger.info(f"Starting preload of all {len(tasks_to_load)} tasks")
        
        return self._execute_preload_tasks(tasks_to_load)
    
    def _execute_preload_tasks(self, tasks: List[PreloadTask]) -> Dict[str, bool]:
        """执行预加载任务"""
        with self._lock:
            if self.is_preloading:
                raise RuntimeError("Preloading already in progress")
            self.is_preloading = True
        
        start_time = time.time()
        results = {}
        
        try:
            # Submit tasks to executor
            for task in tasks:
                if self._check_dependencies(task):
                    future = self.executor.submit(self._execute_single_task, task)
                    self.preload_futures[task.resource_id] = future
                else:
                    self.logger.warning(f"Dependencies not met for task {task.resource_id}")
                    results[task.resource_id] = False
            
            # Wait for completion
            for task_id, future in self.preload_futures.items():
                try:
                    success = future.result(timeout=self.preload_tasks[task_id].timeout)
                    results[task_id] = success
                except Exception as e:
                    self.logger.error(f"Preload task {task_id} failed: {e}")
                    results[task_id] = False
            
            # Update statistics
            total_time = time.time() - start_time
            self.stats["total_preload_time"] += total_time
            self.stats["last_preload_time"] = time.time()
            
            successful_tasks = sum(1 for success in results.values() if success)
            self.logger.info(f"Preload completed: {successful_tasks}/{len(results)} tasks successful "
                           f"in {total_time:.2f}s")
            
            return results
            
        finally:
            self.preload_futures.clear()
            self.is_preloading = False
    
    def _check_dependencies(self, task: PreloadTask) -> bool:
        """检查任务依赖是否满足"""
        for dep_id in task.dependencies:
            if dep_id not in self.preload_tasks:
                self.logger.error(f"Dependency {dep_id} not registered for task {task.resource_id}")
                return False
            
            dep_task = self.preload_tasks[dep_id]
            if not dep_task.is_completed:
                self.logger.debug(f"Dependency {dep_id} not completed for task {task.resource_id}")
                return False
        
        return True
    
    def _execute_single_task(self, task: PreloadTask) -> bool:
        """执行单个预加载任务"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"Executing preload task: {task.resource_id}")
            
            result = task.loader_func()
            
            # Update task state
            task.is_completed = True
            task.is_failed = False
            task.result = result
            task.load_time = time.time() - start_time
            
            self.stats["completed_tasks"] += 1
            
            self.logger.debug(f"Preload task {task.resource_id} completed in {task.load_time:.3f}s")
            return True
            
        except Exception as e:
            task.is_failed = True
            task.error = e
            task.load_time = time.time() - start_time
            
            self.stats["failed_tasks"] += 1
            
            self.logger.error(f"Preload task {task.resource_id} failed: {e}")
            return False
    
    def get_preload_status(self) -> Dict[str, Any]:
        """获取预加载状态"""
        with self._lock:
            task_details = []
            for task in self.preload_tasks.values():
                task_details.append({
                    "resource_id": task.resource_id,
                    "category": task.category.value,
                    "priority": task.priority,
                    "is_completed": task.is_completed,
                    "is_failed": task.is_failed,
                    "load_time": task.load_time,
                    "description": task.description
                })
            
            return {
                **self.stats,
                "is_preloading": self.is_preloading,
                "active_futures": len(self.preload_futures),
                "task_details": task_details
            }
    
    def is_resource_preloaded(self, resource_id: str) -> bool:
        """检查资源是否已预加载"""
        if resource_id not in self.preload_tasks:
            return False
        return self.preload_tasks[resource_id].is_completed
    
    def get_preloaded_resource(self, resource_id: str) -> Any:
        """获取已预加载的资源"""
        if resource_id not in self.preload_tasks:
            raise ValueError(f"Resource {resource_id} not registered")
        
        task = self.preload_tasks[resource_id]
        if not task.is_completed:
            raise RuntimeError(f"Resource {resource_id} not preloaded")
        
        if task.is_failed:
            raise RuntimeError(f"Resource {resource_id} failed to load: {task.error}")
        
        return task.result
    
    def shutdown(self) -> None:
        """关闭预加载器"""
        self.logger.info("Shutting down resource preloader")
        
        # Cancel pending futures
        for future in self.preload_futures.values():
            future.cancel()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.preload_tasks.clear()
        self.category_tasks.clear()
        self.preload_futures.clear()
    
    # Default resource loaders
    def _load_system_fonts(self) -> Dict[str, Any]:
        """加载系统字体"""
        # This would normally load and cache system fonts
        # For now, return a placeholder
        time.sleep(0.1)  # Simulate loading time
        return {"fonts_loaded": ["Arial", "Times New Roman", "Courier New"]}
    
    def _load_app_icons(self) -> Dict[str, Any]:
        """加载应用图标"""
        # This would normally load application icons
        time.sleep(0.05)  # Simulate loading time
        return {"icons_loaded": ["app_icon", "tray_icon", "window_icon"]}
    
    def _load_base_translations(self) -> Dict[str, Any]:
        """加载基础翻译"""
        # This would normally load translation files
        time.sleep(0.2)  # Simulate loading time
        return {"translations_loaded": ["en_US", "zh_CN"]}
    
    def _load_base_styles(self) -> Dict[str, Any]:
        """加载基础样式"""
        # This would normally load CSS/QSS files
        time.sleep(0.15)  # Simulate loading time
        return {"styles_loaded": ["base.qss", "dark.qss", "light.qss"]}


# Global resource preloader instance
resource_preloader = ResourcePreloader()


# Convenience functions
def register_critical_resource(resource_id: str, category: PreloadCategory,
                             loader_func: Callable[[], Any], description: str = "") -> None:
    """注册关键资源"""
    resource_preloader.register_preload_task(
        resource_id, category, loader_func, priority=1, description=description
    )


def preload_critical_resources() -> Dict[str, bool]:
    """预加载关键资源"""
    return resource_preloader.preload_by_priority(max_priority=2)


def preload_category_resources(category: PreloadCategory) -> Dict[str, bool]:
    """预加载指定类别资源"""
    return resource_preloader.preload_category(category)


def get_preload_status() -> Dict[str, Any]:
    """获取预加载状态"""
    return resource_preloader.get_preload_status()


def is_resource_preloaded(resource_id: str) -> bool:
    """检查资源是否已预加载"""
    return resource_preloader.is_resource_preloaded(resource_id)
