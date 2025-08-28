"""
Deferred Initializer
Provides deferred initialization system for optional features until needed
"""

import time
import threading
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
from functools import wraps

from .logging_config import get_logger

logger = get_logger(__name__)


class InitializationTrigger(Enum):
    """初始化触发器类型"""
    FIRST_ACCESS = "first_access"      # 首次访问时
    USER_ACTION = "user_action"        # 用户操作时
    SYSTEM_READY = "system_ready"      # 系统就绪时
    MEMORY_AVAILABLE = "memory_available"  # 内存可用时
    MANUAL = "manual"                  # 手动触发


class FeatureState(Enum):
    """功能状态"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class DeferredFeature:
    """延迟初始化功能"""
    feature_id: str
    name: str
    initializer_func: Callable[[], Any]
    trigger: InitializationTrigger = InitializationTrigger.FIRST_ACCESS
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 30.0
    retry_count: int = 2
    optional: bool = True
    description: str = ""
    
    # Runtime state
    state: FeatureState = FeatureState.NOT_INITIALIZED
    instance: Any = None
    initialization_time: float = 0.0
    last_error: Optional[Exception] = None
    access_count: int = 0
    last_access: float = 0.0
    init_attempts: int = 0


class DeferredProxy:
    """延迟代理类 - 代理实际对象直到初始化"""
    
    def __init__(self, feature_id: str, initializer: 'DeferredInitializer'):
        self._feature_id = feature_id
        self._initializer = initializer
        self._initialized = False
        self._instance = None
    
    def __getattr__(self, name: str) -> Any:
        """属性访问时触发初始化"""
        if not self._initialized:
            self._instance = self._initializer.initialize_feature(self._feature_id)
            self._initialized = True
        
        if self._instance is None:
            raise RuntimeError(f"Feature {self._feature_id} failed to initialize")
        
        return getattr(self._instance, name)
    
    def __call__(self, *args, **kwargs) -> Any:
        """调用时触发初始化"""
        if not self._initialized:
            self._instance = self._initializer.initialize_feature(self._feature_id)
            self._initialized = True
        
        if self._instance is None:
            raise RuntimeError(f"Feature {self._feature_id} failed to initialize")
        
        return self._instance(*args, **kwargs)


def deferred_feature(feature_id: str, trigger: InitializationTrigger = InitializationTrigger.FIRST_ACCESS,
                    dependencies: Optional[List[str]] = None, timeout: float = 30.0,
                    retry_count: int = 2, optional: bool = True, description: str = ""):
    """装饰器：将函数标记为延迟初始化功能"""
    def decorator(func: Callable[[], Any]) -> Callable[[], DeferredProxy]:
        # Register the feature
        deferred_initializer.register_feature(
            feature_id=feature_id,
            name=func.__name__,
            initializer_func=func,
            trigger=trigger,
            dependencies=dependencies or [],
            timeout=timeout,
            retry_count=retry_count,
            optional=optional,
            description=description
        )
        
        @wraps(func)
        def wrapper() -> DeferredProxy:
            return deferred_initializer.get_proxy(feature_id)
        
        return wrapper
    
    return decorator


class DeferredInitializer:
    """延迟初始化管理器"""
    
    def __init__(self):
        self.logger = logger.bind(component="DeferredInitializer")
        self.features: Dict[str, DeferredFeature] = {}
        self.proxies: Dict[str, DeferredProxy] = {}
        self._lock = threading.RLock()
        
        # Initialization tracking
        self.initialization_order: List[str] = []
        self.failed_features: Set[str] = set()
        
        # Statistics
        self.stats = {
            "total_features": 0,
            "initialized_features": 0,
            "failed_features": 0,
            "total_init_time": 0.0,
            "average_init_time": 0.0,
            "proxy_accesses": 0
        }
    
    def register_feature(self, feature_id: str, name: str, initializer_func: Callable[[], Any],
                        trigger: InitializationTrigger = InitializationTrigger.FIRST_ACCESS,
                        dependencies: Optional[List[str]] = None, timeout: float = 30.0,
                        retry_count: int = 2, optional: bool = True, description: str = "") -> None:
        """注册延迟初始化功能"""
        with self._lock:
            if feature_id in self.features:
                self.logger.warning(f"Feature {feature_id} already registered, overwriting")
            
            feature = DeferredFeature(
                feature_id=feature_id,
                name=name,
                initializer_func=initializer_func,
                trigger=trigger,
                dependencies=dependencies or [],
                timeout=timeout,
                retry_count=retry_count,
                optional=optional,
                description=description
            )
            
            self.features[feature_id] = feature
            self.stats["total_features"] += 1
            
            self.logger.debug(f"Registered deferred feature: {feature_id} "
                            f"(trigger: {trigger.value}, optional: {optional})")
    
    def get_proxy(self, feature_id: str) -> DeferredProxy:
        """获取功能代理"""
        if feature_id not in self.features:
            raise ValueError(f"Feature {feature_id} not registered")
        
        if feature_id not in self.proxies:
            self.proxies[feature_id] = DeferredProxy(feature_id, self)
        
        self.stats["proxy_accesses"] += 1
        return self.proxies[feature_id]
    
    def initialize_feature(self, feature_id: str, force: bool = False) -> Any:
        """初始化指定功能"""
        if feature_id not in self.features:
            raise ValueError(f"Feature {feature_id} not registered")
        
        feature = self.features[feature_id]
        
        with self._lock:
            # Check if already initialized
            if feature.state == FeatureState.INITIALIZED and not force:
                feature.access_count += 1
                feature.last_access = time.time()
                return feature.instance
            
            # Check if currently initializing
            if feature.state == FeatureState.INITIALIZING:
                self.logger.debug(f"Feature {feature_id} is currently initializing")
                return None
            
            # Check if failed and not forcing
            if feature.state == FeatureState.FAILED and not force:
                if feature.optional:
                    self.logger.warning(f"Optional feature {feature_id} previously failed, skipping")
                    return None
                else:
                    raise RuntimeError(f"Required feature {feature_id} failed to initialize: {feature.last_error}")
            
            # Check dependencies
            if not self._check_dependencies(feature):
                if not feature.optional:
                    raise RuntimeError(f"Dependencies not met for required feature {feature_id}")
                self.logger.warning(f"Dependencies not met for optional feature {feature_id}")
                return None
            
            # Start initialization
            feature.state = FeatureState.INITIALIZING
            feature.init_attempts += 1
            
        return self._perform_initialization(feature)
    
    def _check_dependencies(self, feature: DeferredFeature) -> bool:
        """检查功能依赖"""
        for dep_id in feature.dependencies:
            if dep_id not in self.features:
                self.logger.error(f"Dependency {dep_id} not registered for feature {feature.feature_id}")
                return False
            
            dep_feature = self.features[dep_id]
            if dep_feature.state != FeatureState.INITIALIZED:
                # Try to initialize dependency
                try:
                    self.initialize_feature(dep_id)
                    if dep_feature.state != FeatureState.INITIALIZED:
                        return False
                except Exception as e:
                    self.logger.error(f"Failed to initialize dependency {dep_id}: {e}")
                    return False
        
        return True
    
    def _perform_initialization(self, feature: DeferredFeature) -> Any:
        """执行功能初始化"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"Initializing feature: {feature.feature_id}")
            
            # Call initializer function
            result = feature.initializer_func()
            
            # Update feature state
            feature.state = FeatureState.INITIALIZED
            feature.instance = result
            feature.initialization_time = time.time() - start_time
            feature.access_count = 1
            feature.last_access = time.time()
            feature.last_error = None
            
            # Update tracking
            self.initialization_order.append(feature.feature_id)
            if feature.feature_id in self.failed_features:
                self.failed_features.remove(feature.feature_id)
            
            # Update statistics
            self.stats["initialized_features"] += 1
            self.stats["total_init_time"] += feature.initialization_time
            self.stats["average_init_time"] = (
                self.stats["total_init_time"] / self.stats["initialized_features"]
            )
            
            self.logger.info(f"Feature {feature.feature_id} initialized successfully "
                           f"in {feature.initialization_time:.3f}s")
            
            return result
            
        except Exception as e:
            feature.state = FeatureState.FAILED
            feature.last_error = e
            feature.initialization_time = time.time() - start_time
            
            self.failed_features.add(feature.feature_id)
            self.stats["failed_features"] += 1
            
            self.logger.error(f"Feature {feature.feature_id} failed to initialize: {e}")
            
            # Retry if attempts remaining
            if feature.init_attempts < feature.retry_count:
                self.logger.info(f"Retrying feature {feature.feature_id} "
                               f"(attempt {feature.init_attempts + 1}/{feature.retry_count})")
                feature.state = FeatureState.NOT_INITIALIZED
                return self.initialize_feature(feature.feature_id)
            
            # Handle failure based on whether feature is optional
            if not feature.optional:
                raise RuntimeError(f"Required feature {feature.feature_id} failed to initialize: {e}")
            
            return None
    
    def initialize_by_trigger(self, trigger: InitializationTrigger) -> Dict[str, bool]:
        """根据触发器初始化功能"""
        features_to_init = [
            feature for feature in self.features.values()
            if feature.trigger == trigger and feature.state == FeatureState.NOT_INITIALIZED
        ]
        
        if not features_to_init:
            self.logger.debug(f"No features to initialize for trigger {trigger.value}")
            return {}
        
        self.logger.info(f"Initializing {len(features_to_init)} features for trigger {trigger.value}")
        
        results = {}
        for feature in features_to_init:
            try:
                result = self.initialize_feature(feature.feature_id)
                results[feature.feature_id] = result is not None
            except Exception as e:
                results[feature.feature_id] = False
                self.logger.error(f"Failed to initialize feature {feature.feature_id}: {e}")
        
        return results
    
    def is_feature_initialized(self, feature_id: str) -> bool:
        """检查功能是否已初始化"""
        if feature_id not in self.features:
            return False
        return self.features[feature_id].state == FeatureState.INITIALIZED
    
    def get_feature_state(self, feature_id: str) -> Optional[FeatureState]:
        """获取功能状态"""
        if feature_id not in self.features:
            return None
        return self.features[feature_id].state
    
    def get_initialized_feature(self, feature_id: str) -> Any:
        """获取已初始化的功能实例"""
        if feature_id not in self.features:
            raise ValueError(f"Feature {feature_id} not registered")
        
        feature = self.features[feature_id]
        if feature.state != FeatureState.INITIALIZED:
            raise RuntimeError(f"Feature {feature_id} not initialized")
        
        feature.access_count += 1
        feature.last_access = time.time()
        return feature.instance
    
    def disable_feature(self, feature_id: str) -> None:
        """禁用功能"""
        if feature_id not in self.features:
            raise ValueError(f"Feature {feature_id} not registered")
        
        feature = self.features[feature_id]
        feature.state = FeatureState.DISABLED
        feature.instance = None
        
        self.logger.info(f"Feature {feature_id} disabled")
    
    def get_initialization_stats(self) -> Dict[str, Any]:
        """获取初始化统计"""
        feature_details = []
        for feature in self.features.values():
            feature_details.append({
                "feature_id": feature.feature_id,
                "name": feature.name,
                "state": feature.state.value,
                "trigger": feature.trigger.value,
                "optional": feature.optional,
                "initialization_time": feature.initialization_time,
                "access_count": feature.access_count,
                "init_attempts": feature.init_attempts,
                "has_error": feature.last_error is not None
            })
        
        return {
            **self.stats,
            "initialization_order": self.initialization_order,
            "failed_features": list(self.failed_features),
            "feature_details": feature_details
        }
    
    def cleanup(self) -> None:
        """清理资源"""
        self.logger.info("Cleaning up deferred initializer")
        
        # Clean up initialized features that support cleanup
        for feature in self.features.values():
            if feature.state == FeatureState.INITIALIZED and feature.instance:
                if hasattr(feature.instance, 'cleanup'):
                    try:
                        feature.instance.cleanup()
                    except Exception as e:
                        self.logger.warning(f"Error cleaning up feature {feature.feature_id}: {e}")
        
        self.features.clear()
        self.proxies.clear()
        self.initialization_order.clear()
        self.failed_features.clear()


# Global deferred initializer instance
deferred_initializer = DeferredInitializer()


# Convenience functions
def register_deferred_feature(feature_id: str, name: str, initializer_func: Callable[[], Any],
                            trigger: InitializationTrigger = InitializationTrigger.FIRST_ACCESS,
                            dependencies: Optional[List[str]] = None, timeout: float = 30.0,
                            retry_count: int = 2, optional: bool = True, description: str = "") -> None:
    """注册延迟初始化功能"""
    deferred_initializer.register_feature(
        feature_id, name, initializer_func, trigger, dependencies,
        timeout, retry_count, optional, description
    )


def get_deferred_feature(feature_id: str) -> DeferredProxy:
    """获取延迟功能代理"""
    return deferred_initializer.get_proxy(feature_id)


def initialize_deferred_features(trigger: InitializationTrigger) -> Dict[str, bool]:
    """初始化指定触发器的功能"""
    return deferred_initializer.initialize_by_trigger(trigger)


def get_deferred_stats() -> Dict[str, Any]:
    """获取延迟初始化统计"""
    return deferred_initializer.get_initialization_stats()
