"""
Settings Performance Manager
Provides caching, lazy loading, and performance optimization for settings
"""

import asyncio
import json
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set, Union

from PySide6.QtCore import QMutex, QMutexLocker, QObject, QTimer, Signal

from src.heal.common.json_utils import JsonLoadResult, JsonUtils
from src.heal.common.logging_config import get_logger


@dataclass
class CacheEntry:
    """Cache entry with metadata"""

    value: Any
    timestamp: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    dirty: bool = False

    def is_expired(self, ttl: float) -> bool:
        """Check if cache entry is expired"""
        return time.time() - self.timestamp > ttl

    def touch(self) -> None:
        """Update access information"""
        self.access_count += 1
        self.last_access = time.time()


class SettingsCache:
    """High-performance settings cache with TTL and LRU eviction"""

    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0) -> None:
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.mutex = QMutex()
        self.logger = get_logger("settings_cache", module="SettingsCache")

    def get(self, key: str, default: Any | None = None) -> Any:
        """Get value from cache"""
        with QMutexLocker(self.mutex):
            entry = self.cache.get(key)
            if entry is None:
                return default

            if entry.is_expired(self.default_ttl):
                del self.cache[key]
                return default

            entry.touch()
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache"""
        with QMutexLocker(self.mutex):
            if len(self.cache) >= self.max_size:
                self._evict_lru()

            ttl = ttl or self.default_ttl
            self.cache[key] = CacheEntry(value=value, timestamp=time.time())

    def invalidate(self, key: str) -> None:
        """Invalidate cache entry"""
        with QMutexLocker(self.mutex):
            self.cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries"""
        with QMutexLocker(self.mutex):
            self.cache.clear()

    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return

        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_access)
        del self.cache[lru_key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with QMutexLocker(self.mutex):
            total_accesses = sum(entry.access_count for entry in self.cache.values())
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "total_accesses": total_accesses,
                "hit_rate": total_accesses / max(1, len(self.cache)),
            }


class LazyLoader:
    """Lazy loading manager for expensive settings operations"""

    def __init__(self) -> None:
        self.loaded_settings: Set[str] = set()
        self.loading_callbacks: Dict[str, Callable] = {}
        self.executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="settings_loader"
        )
        self.logger = get_logger("lazy_loader", module="LazyLoader")

    def register_lazy_setting(self, setting_key: str, loader_func: Callable) -> None:
        """Register a setting for lazy loading"""
        self.loading_callbacks[setting_key] = loader_func
        self.logger.debug(f"Registered lazy setting: {setting_key}")

    def load_setting(self, setting_key: str) -> Any:
        """Load setting lazily"""
        if setting_key in self.loaded_settings:
            return None  # Already loaded

        loader_func = self.loading_callbacks.get(setting_key)
        if not loader_func:
            self.logger.warning(f"No loader registered for setting: {setting_key}")
            return None

        try:
            # Load in background thread
            future = self.executor.submit(loader_func)
            result = future.result(timeout=5.0)  # 5 second timeout
            self.loaded_settings.add(setting_key)
            self.logger.debug(f"Lazy loaded setting: {setting_key}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to lazy load setting {setting_key}: {e}")
            return None

    def is_loaded(self, setting_key: str) -> bool:
        """Check if setting is already loaded"""
        return setting_key in self.loaded_settings


class SettingsPerformanceManager(QObject):
    """Main performance manager for settings operations"""

    # Signals
    setting_loaded = Signal(str, object)  # setting_key, value
    setting_saved = Signal(str, bool)  # setting_key, success
    cache_stats_updated = Signal(dict)  # cache statistics
    error_occurred = Signal(str, str)  # operation, error_message

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.cache = SettingsCache()
        self.lazy_loader = LazyLoader()
        self.logger = get_logger(
            "settings_performance", module="SettingsPerformanceManager"
        )

        # Batch operations
        self.pending_saves: Dict[str, Any] = {}
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self._flush_pending_saves)
        self.save_timer.setSingleShot(True)

        # Performance monitoring
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._emit_cache_stats)
        self.stats_timer.start(30000)  # Update stats every 30 seconds

        self.logger.info("Settings performance manager initialized")

    def get_setting(self, file_path: str, key: str, default_value: Any | None = None) -> Any:
        """Get setting with caching"""
        cache_key = f"{file_path}:{key}"

        # Try cache first
        cached_value = self.cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        # Load from file
        try:
            result = JsonUtils.load_json_file(file_path)
            if result.success and result.data:
                value = result.data.get(key, default_value)
                self.cache.set(cache_key, value)
                return value
        except Exception as e:
            self.logger.error(f"Failed to get setting {key} from {file_path}: {e}")
            self.error_occurred.emit("get_setting", str(e))

        return default_value

    def set_setting(
        self, file_path: str, key: str, value: Any, immediate: bool = False
    ) -> None:
        """Set setting with batching and caching"""
        cache_key = f"{file_path}:{key}"

        # Update cache immediately
        self.cache.set(cache_key, value)

        if immediate:
            self._save_setting_immediate(file_path, key, value)
        else:
            # Batch the save operation
            batch_key = f"{file_path}:{key}"
            self.pending_saves[batch_key] = (file_path, key, value)

            # Start/restart the save timer
            self.save_timer.start(1000)  # Save after 1 second of inactivity

    def _save_setting_immediate(self, file_path: str, key: str, value: Any) -> bool:
        """Save setting immediately"""
        try:
            # Load current data
            result = JsonUtils.load_json_file(
                file_path, create_if_missing=True, default_content={}
            )
            if not result.success:
                self.logger.error(f"Failed to load file for saving: {file_path}")
                return False

            # Update data
            data = result.data or {}
            data[key] = value

            # Save data
            success = JsonUtils.save_json_file(file_path, data)
            if success:
                self.setting_saved.emit(f"{file_path}:{key}", True)
                self.logger.debug(f"Saved setting {key} to {file_path}")
            else:
                self.setting_saved.emit(f"{file_path}:{key}", False)
                self.logger.error(f"Failed to save setting {key} to {file_path}")

            return success

        except Exception as e:
            self.logger.error(f"Error saving setting {key} to {file_path}: {e}")
            self.error_occurred.emit("save_setting", str(e))
            self.setting_saved.emit(f"{file_path}:{key}", False)
            return False

    def _flush_pending_saves(self) -> None:
        """Flush all pending save operations"""
        if not self.pending_saves:
            return

        # Group saves by file
        files_to_save: Dict[str, Dict[str, Any]] = defaultdict(dict)

        for batch_key, (file_path, key, value) in self.pending_saves.items():
            files_to_save[file_path][key] = value

        # Save each file
        for file_path, updates in files_to_save.items():
            self._batch_save_file(file_path, updates)

        # Clear pending saves
        self.pending_saves.clear()
        self.logger.debug(f"Flushed {len(files_to_save)} files with batched saves")

    def _batch_save_file(self, file_path: str, updates: Dict[str, Any]) -> None:
        """Save multiple updates to a single file"""
        try:
            # Load current data
            result = JsonUtils.load_json_file(
                file_path, create_if_missing=True, default_content={}
            )
            if not result.success:
                self.logger.error(f"Failed to load file for batch saving: {file_path}")
                return

            # Apply all updates
            data = result.data or {}
            data.update(updates)

            # Save data
            success = JsonUtils.save_json_file(file_path, data)

            # Emit signals for each setting
            for key in updates.keys():
                self.setting_saved.emit(f"{file_path}:{key}", success)

            if success:
                self.logger.debug(f"Batch saved {len(updates)} settings to {file_path}")
            else:
                self.logger.error(f"Failed to batch save settings to {file_path}")

        except Exception as e:
            self.logger.error(f"Error in batch save to {file_path}: {e}")
            self.error_occurred.emit("batch_save", str(e))

    def invalidate_cache(self, file_path: str, key: Optional[str] = None) -> None:
        """Invalidate cache entries"""
        if key:
            cache_key = f"{file_path}:{key}"
            self.cache.invalidate(cache_key)
        else:
            # Invalidate all entries for the file
            keys_to_remove = [
                k for k in self.cache.cache.keys() if k.startswith(f"{file_path}:")
            ]
            for cache_key in keys_to_remove:
                self.cache.invalidate(cache_key)

    def register_lazy_setting(self, setting_key: str, loader_func: Callable) -> None:
        """Register a setting for lazy loading"""
        self.lazy_loader.register_lazy_setting(setting_key, loader_func)

    def load_lazy_setting(self, setting_key: str) -> Any:
        """Load a lazy setting"""
        return self.lazy_loader.load_setting(setting_key)

    def _emit_cache_stats(self) -> None:
        """Emit cache statistics"""
        stats = self.cache.get_stats()
        self.cache_stats_updated.emit(stats)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        cache_stats = self.cache.get_stats()
        return {
            "cache": cache_stats,
            "pending_saves": len(self.pending_saves),
            "lazy_loaded_settings": len(self.lazy_loader.loaded_settings),
            "registered_lazy_settings": len(self.lazy_loader.loading_callbacks),
        }

    def cleanup(self) -> None:
        """Cleanup resources"""
        self.save_timer.stop()
        self.stats_timer.stop()
        self._flush_pending_saves()
        self.lazy_loader.executor.shutdown(wait=True)
        self.cache.clear()
        self.logger.info("Settings performance manager cleaned up")


# Global instance
_performance_manager: Optional[SettingsPerformanceManager] = None


def get_performance_manager() -> SettingsPerformanceManager:
    """Get global performance manager instance"""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = SettingsPerformanceManager()
    return _performance_manager


def performance_optimized(func: Any) -> None:
    """Decorator to add performance optimization to setting operations"""

    @wraps(func)
    def wrapper(*args, **kwargs: Any) -> None:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            if duration > 0.1:  # Log slow operations
                logger = get_logger("performance_decorator")
                logger.warning(
                    f"Slow setting operation {func.__name__}: {duration:.3f}s"
                )
            return result
        except Exception as e:
            logger = get_logger("performance_decorator")
            logger.error(f"Error in {func.__name__}: {e}")
            raise

    return wrapper
