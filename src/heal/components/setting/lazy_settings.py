"""
Lazy Loading Settings Components
Provides lazy initialization for expensive settings operations
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtWidgets import QWidget

from src.heal.common.logging_config import get_logger
from src.heal.models.check_update import check_update
from src.heal.components.tools.editor import JsonEditor

T = TypeVar("T")


@dataclass
class LazyLoadResult:
    """Result of lazy loading operation"""

    success: bool
    data: Any | None = None
    error: Optional[str] = None
    load_time: float = 0.0


class LazyLoadWorker(QThread):
    """Worker thread for lazy loading operations"""

    finished = Signal(str, object)  # setting_key, result
    error_occurred = Signal(str, str)  # setting_key, error

    def __init__(self, setting_key: str, loader_func: Callable, parent=None) -> None:
        super().__init__(parent)
        self.setting_key = setting_key
        self.loader_func = loader_func
        self.logger = get_logger("lazy_load_worker", module="LazyLoadWorker")

    def run(self) -> None:
        """Run the lazy loading operation"""
        try:
            start_time = time.time()
            result = self.loader_func()
            load_time = time.time() - start_time

            self.logger.debug(f"Lazy loaded {self.setting_key} in {load_time:.3f}s")
            self.finished.emit(self.setting_key, result)

        except Exception as e:
            error_msg = f"Failed to lazy load {self.setting_key}: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(self.setting_key, error_msg)


class LazySettingProxy(Generic[T]):
    """Proxy for lazy-loaded settings"""

    def __init__(
        self,
        setting_key: str,
        loader_func: Callable[[], T],
        fallback_value: Optional[T] = None,
    ) -> None:
        self.setting_key = setting_key
        self.loader_func = loader_func
        self.fallback_value = fallback_value
        self._value: Optional[T] = None
        self._loaded = False
        self._loading = False
        self._load_future: Optional[asyncio.Future[T]] = None
        self.logger = get_logger("lazy_setting_proxy", module="LazySettingProxy")

    @property
    def value(self) -> Optional[T]:
        """Get the value, loading if necessary"""
        if not self._loaded and not self._loading:
            self._load_sync()
        if self._value is not None:
            return self._value
        return self.fallback_value

    def _load_sync(self) -> None:
        """Load the setting synchronously"""
        if self._loading:
            return

        self._loading = True
        try:
            start_time = time.time()
            self._value = self.loader_func()
            self._loaded = True
            load_time = time.time() - start_time
            self.logger.debug(
                f"Synchronously loaded {self.setting_key} in {load_time:.3f}s"
            )
        except Exception as e:
            self.logger.error(f"Failed to load {self.setting_key}: {e}")
            self._value = self.fallback_value
        finally:
            self._loading = False

    async def load_async(self) -> T:
        """Load the setting asynchronously"""
        if self._loaded:
            if self._value is not None:
                return self._value
            if self.fallback_value is not None:
                return self.fallback_value
            raise ValueError(f"No value available for {self.setting_key}")

        if self._load_future is None:
            loop = asyncio.get_event_loop()
            self._load_future = loop.run_in_executor(None, self.loader_func)

        try:
            self._value = await self._load_future
            self._loaded = True
            return self._value
        except Exception as e:
            self.logger.error(f"Failed to async load {self.setting_key}: {e}")
            if self.fallback_value is not None:
                return self.fallback_value
            raise ValueError(f"No fallback value available for {self.setting_key}")

    def is_loaded(self) -> bool:
        """Check if the setting is loaded"""
        return self._loaded

    def reload(self) -> None:
        """Force reload the setting"""
        self._loaded = False
        self._loading = False
        self._load_future = None
        self._value = None


class LazySettingsManager(QObject):
    """Manager for lazy-loaded settings"""

    setting_loaded = Signal(str, object)  # setting_key, value
    loading_started = Signal(str)  # setting_key
    loading_failed = Signal(str, str)  # setting_key, error

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.proxies: Dict[str, LazySettingProxy] = {}
        self.workers: Dict[str, LazyLoadWorker] = {}
        self.executor = ThreadPoolExecutor(
            max_workers=3, thread_name_prefix="lazy_settings"
        )
        self.logger = get_logger("lazy_settings_manager", module="LazySettingsManager")

        # Preload timer for background loading
        self.preload_timer = QTimer()
        self.preload_timer.timeout.connect(self._preload_next_setting)
        self.preload_queue: list[Any] = []

        self.logger.info("Lazy settings manager initialized")

    def register_lazy_setting(
        self,
        setting_key: str,
        loader_func: Callable,
        fallback_value: Any | None = None,
        preload: bool = False,
    ) -> LazySettingProxy:
        """Register a setting for lazy loading"""
        proxy = LazySettingProxy(setting_key, loader_func, fallback_value)
        self.proxies[setting_key] = proxy

        if preload:
            self.preload_queue.append(setting_key)
            if not self.preload_timer.isActive():
                self.preload_timer.start(100)  # Start preloading after 100ms

        self.logger.debug(f"Registered lazy setting: {setting_key}")
        return proxy

    def get_setting(self, setting_key: str) -> Any:
        """Get a lazy setting value"""
        proxy = self.proxies.get(setting_key)
        if proxy:
            return proxy.value
        else:
            self.logger.warning(f"Lazy setting not found: {setting_key}")
            return None

    def load_setting_async(self, setting_key: str) -> None:
        """Load a setting asynchronously using worker thread"""
        if setting_key in self.workers:
            return  # Already loading

        proxy = self.proxies.get(setting_key)
        if not proxy:
            self.logger.warning(f"Cannot load unknown setting: {setting_key}")
            return

        if proxy.is_loaded():
            return  # Already loaded

        # Create worker thread
        worker = LazyLoadWorker(setting_key, proxy.loader_func)
        worker.finished.connect(self._on_setting_loaded)
        worker.error_occurred.connect(self._on_loading_failed)
        worker.finished.connect(lambda: self._cleanup_worker(setting_key))

        self.workers[setting_key] = worker
        self.loading_started.emit(setting_key)
        worker.start()

    def _on_setting_loaded(self, setting_key: str, value: Any) -> None:
        """Handle successful setting load"""
        proxy = self.proxies.get(setting_key)
        if proxy:
            proxy._value = value
            proxy._loaded = True
            proxy._loading = False

        self.setting_loaded.emit(setting_key, value)
        self.logger.debug(f"Successfully loaded lazy setting: {setting_key}")

    def _on_loading_failed(self, setting_key: str, error: str) -> None:
        """Handle failed setting load"""
        proxy = self.proxies.get(setting_key)
        if proxy:
            proxy._value = proxy.fallback_value
            proxy._loading = False

        self.loading_failed.emit(setting_key, error)
        self.logger.error(f"Failed to load lazy setting {setting_key}: {error}")

    def _cleanup_worker(self, setting_key: str) -> None:
        """Clean up worker thread"""
        worker = self.workers.pop(setting_key, None)
        if worker:
            worker.deleteLater()

    def _preload_next_setting(self) -> None:
        """Preload the next setting in the queue"""
        if not self.preload_queue:
            self.preload_timer.stop()
            return

        setting_key = self.preload_queue.pop(0)
        self.load_setting_async(setting_key)

        if self.preload_queue:
            # Continue preloading with delay
            self.preload_timer.start(500)  # 500ms between preloads
        else:
            self.preload_timer.stop()

    def is_loaded(self, setting_key: str) -> bool:
        """Check if a setting is loaded"""
        proxy = self.proxies.get(setting_key)
        return proxy.is_loaded() if proxy else False

    def reload_setting(self, setting_key: str) -> None:
        """Reload a specific setting"""
        proxy = self.proxies.get(setting_key)
        if proxy:
            proxy.reload()
            self.load_setting_async(setting_key)

    def get_loading_stats(self) -> Dict[str, Any]:
        """Get loading statistics"""
        total_settings = len(self.proxies)
        loaded_settings = sum(1 for proxy in self.proxies.values() if proxy.is_loaded())
        loading_settings = len(self.workers)

        return {
            "total_settings": total_settings,
            "loaded_settings": loaded_settings,
            "loading_settings": loading_settings,
            "load_percentage": (loaded_settings / max(1, total_settings)) * 100,
            "pending_preloads": len(self.preload_queue),
        }

    def cleanup(self) -> None:
        """Cleanup resources"""
        self.preload_timer.stop()

        # Stop all workers
        for worker in self.workers.values():
            worker.terminate()
            worker.wait(1000)  # Wait up to 1 second

        self.workers.clear()
        self.executor.shutdown(wait=True)
        self.logger.info("Lazy settings manager cleaned up")


# Predefined lazy settings
class LazySettings:
    """Collection of commonly used lazy settings"""

    @staticmethod
    def create_config_editor() -> JsonEditor:
        """Create JSON editor lazily"""
        return JsonEditor()

    @staticmethod
    def create_update_checker() -> Callable:
        """Create update checker lazily"""
        return check_update

    @staticmethod
    def load_theme_resources() -> Dict[str, Any]:
        """Load theme resources lazily"""
        # Simulate expensive theme resource loading
        time.sleep(0.1)  # Simulate loading time
        return {"icons": {}, "stylesheets": {}, "fonts": {}}

    @staticmethod
    def initialize_network_settings() -> Dict[str, Any]:
        """Initialize network settings lazily"""
        # Simulate network configuration loading
        return {"proxy_config": {}, "mirror_settings": {}, "timeout_values": {}}


# Global lazy settings manager
_lazy_manager: Optional[LazySettingsManager] = None


def get_lazy_manager() -> LazySettingsManager:
    """Get global lazy settings manager"""
    global _lazy_manager
    if _lazy_manager is None:
        _lazy_manager = LazySettingsManager()

        # Register common lazy settings
        _lazy_manager.register_lazy_setting(
            "config_editor", LazySettings.create_config_editor, fallback_value=None
        )

        _lazy_manager.register_lazy_setting(
            "update_checker",
            LazySettings.create_update_checker,
            fallback_value=lambda: None,
        )

        _lazy_manager.register_lazy_setting(
            "theme_resources",
            LazySettings.load_theme_resources,
            fallback_value={},
            preload=True,  # Preload theme resources
        )

        _lazy_manager.register_lazy_setting(
            "network_settings",
            LazySettings.initialize_network_settings,
            fallback_value={},
        )

    return _lazy_manager


def lazy_setting(setting_key: str, fallback_value: Any | None = None):
    """Decorator for lazy setting access"""

    def decorator(func: Any) -> Any:
        @wraps(func)
        def wrapper(*args, **kwargs: Any) -> Any:
            manager = get_lazy_manager()
            value = manager.get_setting(setting_key)
            if value is not None:
                return value
            else:
                # Fallback to original function
                return (
                    func(*args, **kwargs) if fallback_value is None else fallback_value
                )

        return wrapper

    return decorator


# Usage examples:
@lazy_setting("config_editor")
def get_config_editor() -> Any:
    """Get config editor with lazy loading"""
    return JsonEditor()


@lazy_setting("update_checker", fallback_value=lambda: None)
def get_update_checker() -> Any:
    """Get update checker with lazy loading"""
    return check_update
