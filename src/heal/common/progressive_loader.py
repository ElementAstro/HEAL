"""
Progressive Loader
Provides progressive loading architecture for non-critical components after main startup
"""

import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from concurrent.futures import ThreadPoolExecutor, Future
from queue import PriorityQueue, Queue

from PySide6.QtCore import QObject, QTimer, Signal

from .logging_config import get_logger

logger = get_logger(__name__)


class LoadingPhase(Enum):
    """加载阶段"""
    IMMEDIATE = 1      # 立即加载（启动时）
    POST_STARTUP = 2   # 启动后加载
    USER_IDLE = 3      # 用户空闲时加载
    ON_DEMAND = 4      # 按需加载
    BACKGROUND = 5     # 后台加载


class ComponentState(Enum):
    """组件状态"""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class LoadingTrigger:
    """加载触发器"""
    trigger_type: str  # "time", "user_action", "system_idle", "memory_available"
    condition: Any     # Specific condition for the trigger
    description: str = ""


@dataclass
class ProgressiveComponent:
    """渐进式加载组件"""
    component_id: str
    name: str
    loader_func: Callable[[], Any]
    phase: LoadingPhase = LoadingPhase.POST_STARTUP
    priority: int = 5  # 1 = highest priority
    dependencies: List[str] = field(default_factory=list)
    triggers: List[LoadingTrigger] = field(default_factory=list)
    timeout: float = 60.0
    retry_count: int = 2
    essential: bool = False  # If True, failure affects app functionality
    description: str = ""
    
    # Runtime state
    state: ComponentState = ComponentState.NOT_LOADED
    load_attempts: int = 0
    load_time: float = 0.0
    last_error: Optional[Exception] = None
    loaded_result: Any = None
    load_timestamp: Optional[float] = None


class ProgressiveLoadingManager(QObject):
    """渐进式加载管理器"""
    
    # Signals
    component_loaded = Signal(str, object)  # component_id, result
    component_failed = Signal(str, str)     # component_id, error_message
    loading_progress = Signal(int, int)     # loaded_count, total_count
    phase_completed = Signal(str)           # phase_name
    
    def __init__(self, max_workers: int = 2):
        super().__init__()
        self.logger = logger.bind(component="ProgressiveLoadingManager")
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Component registry
        self.components: Dict[str, ProgressiveComponent] = {}
        self.phase_components: Dict[LoadingPhase, List[str]] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # Loading state
        self.current_phase = LoadingPhase.IMMEDIATE
        self.is_loading = False
        self.loading_queue = PriorityQueue()
        self.active_futures: Dict[str, Future] = {}
        
        # Timers for different phases
        self.post_startup_timer = QTimer()
        self.idle_timer = QTimer()
        self.background_timer = QTimer()
        
        # Statistics
        self.stats = {
            "total_components": 0,
            "loaded_components": 0,
            "failed_components": 0,
            "phases_completed": set(),
            "total_load_time": 0.0,
            "average_load_time": 0.0
        }
        
        self._setup_timers()
        self._lock = threading.RLock()
    
    def _setup_timers(self) -> None:
        """设置定时器"""
        # Post-startup loading (2 seconds after startup)
        self.post_startup_timer.setSingleShot(True)
        self.post_startup_timer.timeout.connect(
            lambda: self.start_phase_loading(LoadingPhase.POST_STARTUP)
        )
        
        # Idle loading (check every 5 seconds)
        self.idle_timer.timeout.connect(self._check_idle_loading)
        
        # Background loading (every 30 seconds)
        self.background_timer.timeout.connect(
            lambda: self.start_phase_loading(LoadingPhase.BACKGROUND)
        )
    
    def register_component(self, component: ProgressiveComponent) -> None:
        """注册组件"""
        with self._lock:
            if component.component_id in self.components:
                self.logger.warning(f"Component {component.component_id} already registered")
                return
            
            self.components[component.component_id] = component
            
            # Update phase mapping
            if component.phase not in self.phase_components:
                self.phase_components[component.phase] = []
            self.phase_components[component.phase].append(component.component_id)
            
            # Update dependency graph
            self.dependency_graph[component.component_id] = set(component.dependencies)
            
            self.stats["total_components"] += 1
            
            self.logger.debug(f"Registered component: {component.component_id} "
                            f"(phase: {component.phase.name}, priority: {component.priority})")
    
    def register_simple_component(self, component_id: str, name: str, 
                                loader_func: Callable[[], Any],
                                phase: LoadingPhase = LoadingPhase.POST_STARTUP,
                                priority: int = 5, essential: bool = False,
                                description: str = "") -> None:
        """注册简单组件"""
        component = ProgressiveComponent(
            component_id=component_id,
            name=name,
            loader_func=loader_func,
            phase=phase,
            priority=priority,
            essential=essential,
            description=description
        )
        self.register_component(component)
    
    def start_progressive_loading(self) -> None:
        """开始渐进式加载"""
        self.logger.info("Starting progressive loading system")
        
        # Start immediate loading
        self.start_phase_loading(LoadingPhase.IMMEDIATE)
        
        # Schedule post-startup loading
        self.post_startup_timer.start(2000)  # 2 seconds
        
        # Start idle monitoring
        self.idle_timer.start(5000)  # 5 seconds
        
        # Start background loading timer
        self.background_timer.start(30000)  # 30 seconds
    
    def start_phase_loading(self, phase: LoadingPhase) -> None:
        """开始指定阶段的加载"""
        if phase not in self.phase_components:
            self.logger.debug(f"No components registered for phase {phase.name}")
            return
        
        component_ids = self.phase_components[phase]
        components_to_load = [
            self.components[comp_id] for comp_id in component_ids
            if self.components[comp_id].state == ComponentState.NOT_LOADED
        ]
        
        if not components_to_load:
            self.logger.debug(f"All components in phase {phase.name} already processed")
            return
        
        self.logger.info(f"Starting phase {phase.name} loading: {len(components_to_load)} components")
        self.current_phase = phase
        
        # Sort by priority
        components_to_load.sort(key=lambda c: c.priority)
        
        # Add to loading queue
        for component in components_to_load:
            if self._check_dependencies(component):
                self.loading_queue.put((component.priority, component.component_id))
            else:
                self.logger.debug(f"Dependencies not met for {component.component_id}")
        
        # Start loading
        self._process_loading_queue()
    
    def _check_dependencies(self, component: ProgressiveComponent) -> bool:
        """检查组件依赖"""
        for dep_id in component.dependencies:
            if dep_id not in self.components:
                self.logger.error(f"Dependency {dep_id} not registered for {component.component_id}")
                return False
            
            dep_component = self.components[dep_id]
            if dep_component.state != ComponentState.LOADED:
                return False
        
        return True
    
    def _process_loading_queue(self) -> None:
        """处理加载队列"""
        while not self.loading_queue.empty() and len(self.active_futures) < self.max_workers:
            try:
                priority, component_id = self.loading_queue.get_nowait()
                component = self.components[component_id]
                
                if component.state != ComponentState.NOT_LOADED:
                    continue
                
                # Start loading
                component.state = ComponentState.LOADING
                future = self.executor.submit(self._load_component, component)
                self.active_futures[component_id] = future
                
                # Add completion callback
                future.add_done_callback(
                    lambda f, comp_id=component_id: self._on_component_loaded(comp_id, f)
                )
                
                self.logger.debug(f"Started loading component: {component_id}")
                
            except Exception as e:
                self.logger.error(f"Error processing loading queue: {e}")
                break
    
    def _load_component(self, component: ProgressiveComponent) -> Any:
        """加载单个组件"""
        start_time = time.time()
        component.load_attempts += 1
        
        try:
            self.logger.debug(f"Loading component: {component.component_id}")
            
            result = component.loader_func()
            
            # Update component state
            component.state = ComponentState.LOADED
            component.loaded_result = result
            component.load_time = time.time() - start_time
            component.load_timestamp = time.time()
            
            self.logger.info(f"Component {component.component_id} loaded successfully "
                           f"in {component.load_time:.3f}s")
            
            return result
            
        except Exception as e:
            component.state = ComponentState.FAILED
            component.last_error = e
            component.load_time = time.time() - start_time
            
            self.logger.error(f"Component {component.component_id} failed to load: {e}")
            
            # Retry if attempts remaining
            if component.load_attempts < component.retry_count:
                self.logger.info(f"Retrying component {component.component_id} "
                               f"(attempt {component.load_attempts + 1}/{component.retry_count})")
                component.state = ComponentState.NOT_LOADED
                # Re-queue for retry
                self.loading_queue.put((component.priority, component.component_id))
            
            raise
    
    def _on_component_loaded(self, component_id: str, future: Future) -> None:
        """组件加载完成回调"""
        component = self.components[component_id]
        
        # Remove from active futures
        if component_id in self.active_futures:
            del self.active_futures[component_id]
        
        try:
            result = future.result()
            
            # Update statistics
            self.stats["loaded_components"] += 1
            self.stats["total_load_time"] += component.load_time
            self.stats["average_load_time"] = (
                self.stats["total_load_time"] / self.stats["loaded_components"]
            )
            
            # Emit signals
            self.component_loaded.emit(component_id, result)
            self.loading_progress.emit(
                self.stats["loaded_components"], 
                self.stats["total_components"]
            )
            
            # Check if phase is complete
            self._check_phase_completion()
            
            # Process more components from queue
            self._process_loading_queue()
            
        except Exception as e:
            self.stats["failed_components"] += 1
            self.component_failed.emit(component_id, str(e))
            
            # Continue processing queue even if one component fails
            self._process_loading_queue()
    
    def _check_phase_completion(self) -> None:
        """检查阶段是否完成"""
        if self.current_phase not in self.phase_components:
            return
        
        phase_component_ids = self.phase_components[self.current_phase]
        all_processed = all(
            self.components[comp_id].state in [ComponentState.LOADED, ComponentState.FAILED]
            for comp_id in phase_component_ids
        )
        
        if all_processed and self.current_phase not in self.stats["phases_completed"]:
            self.stats["phases_completed"].add(self.current_phase)
            self.phase_completed.emit(self.current_phase.name)
            self.logger.info(f"Phase {self.current_phase.name} completed")
    
    def _check_idle_loading(self) -> None:
        """检查空闲时加载"""
        # Simple idle detection - in a real implementation, this would check
        # user activity, CPU usage, etc.
        if not self.is_loading and len(self.active_futures) == 0:
            self.start_phase_loading(LoadingPhase.USER_IDLE)
    
    def load_component_now(self, component_id: str) -> bool:
        """立即加载指定组件"""
        if component_id not in self.components:
            self.logger.error(f"Component {component_id} not registered")
            return False
        
        component = self.components[component_id]
        
        if component.state == ComponentState.LOADED:
            self.logger.debug(f"Component {component_id} already loaded")
            return True
        
        if component.state == ComponentState.LOADING:
            self.logger.debug(f"Component {component_id} already loading")
            return True
        
        if not self._check_dependencies(component):
            self.logger.error(f"Dependencies not met for {component_id}")
            return False
        
        try:
            # Load synchronously
            result = self._load_component(component)
            self.component_loaded.emit(component_id, result)
            return True
        except Exception as e:
            self.component_failed.emit(component_id, str(e))
            return False
    
    def get_component_state(self, component_id: str) -> Optional[ComponentState]:
        """获取组件状态"""
        if component_id not in self.components:
            return None
        return self.components[component_id].state
    
    def get_loaded_component(self, component_id: str) -> Any:
        """获取已加载的组件"""
        if component_id not in self.components:
            raise ValueError(f"Component {component_id} not registered")
        
        component = self.components[component_id]
        if component.state != ComponentState.LOADED:
            raise RuntimeError(f"Component {component_id} not loaded")
        
        return component.loaded_result
    
    def get_loading_stats(self) -> Dict[str, Any]:
        """获取加载统计"""
        component_details = []
        for component in self.components.values():
            component_details.append({
                "component_id": component.component_id,
                "name": component.name,
                "phase": component.phase.name,
                "state": component.state.value,
                "priority": component.priority,
                "load_time": component.load_time,
                "load_attempts": component.load_attempts,
                "essential": component.essential
            })
        
        return {
            **self.stats,
            "current_phase": self.current_phase.name,
            "active_loads": len(self.active_futures),
            "queue_size": self.loading_queue.qsize(),
            "component_details": component_details
        }
    
    def shutdown(self) -> None:
        """关闭渐进式加载管理器"""
        self.logger.info("Shutting down progressive loading manager")
        
        # Stop timers
        self.post_startup_timer.stop()
        self.idle_timer.stop()
        self.background_timer.stop()
        
        # Cancel active futures
        for future in self.active_futures.values():
            future.cancel()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Clear data
        self.components.clear()
        self.phase_components.clear()
        self.active_futures.clear()


# Global progressive loading manager
progressive_loading_manager = ProgressiveLoadingManager()


# Convenience functions
def register_progressive_component(component_id: str, name: str, 
                                 loader_func: Callable[[], Any],
                                 phase: LoadingPhase = LoadingPhase.POST_STARTUP,
                                 priority: int = 5, essential: bool = False,
                                 description: str = "") -> None:
    """注册渐进式加载组件"""
    progressive_loading_manager.register_simple_component(
        component_id, name, loader_func, phase, priority, essential, description
    )


def start_progressive_loading() -> None:
    """开始渐进式加载"""
    progressive_loading_manager.start_progressive_loading()


def load_component_immediately(component_id: str) -> bool:
    """立即加载组件"""
    return progressive_loading_manager.load_component_now(component_id)


def get_progressive_loading_stats() -> Dict[str, Any]:
    """获取渐进式加载统计"""
    return progressive_loading_manager.get_loading_stats()
