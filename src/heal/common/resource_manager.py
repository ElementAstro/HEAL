"""
Resource Manager - 统一资源管理和清理
确保应用退出时所有资源得到正确释放
"""

import atexit
import threading
import time
import weakref
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from .logging_config import get_logger

logger = get_logger(__name__)


class ResourceType:
    """资源类型常量"""

    TIMER = "timer"
    THREAD = "thread"
    PROCESS = "process"
    FILE_HANDLE = "file_handle"
    NETWORK_CONNECTION = "network_connection"
    DATABASE_CONNECTION = "database_connection"
    CUSTOM = "custom"


class ResourceInfo:
    """资源信息"""

    def __init__(
        self,
        resource_id: str,
        resource_type: str,
        resource_obj: Any,
        cleanup_func: Callable[[], None],
        description: str = "",
    ) -> None:
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.resource_obj = (
            weakref.ref(resource_obj)
            if hasattr(resource_obj, "__weakref__")
            else resource_obj
        )
        self.cleanup_func = cleanup_func
        self.description = description
        self.created_at = threading.current_thread().name
        self.is_cleaned = False


class ResourceManager(QObject):
    """统一资源管理器"""

    # 信号
    resource_registered = Signal(str, str)  # resource_id, resource_type
    resource_cleaned = Signal(str, str)  # resource_id, resource_type
    cleanup_completed = Signal(int)  # cleaned_count

    _instance: Optional["ResourceManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ResourceManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return

        super().__init__()
        self._initialized = True

        self.resources: Dict[str, ResourceInfo] = {}
        self._instance_lock: threading.RLock = threading.RLock()
        self.logger = logger.bind(component="ResourceManager")

        # 注册退出时的清理函数
        atexit.register(self.cleanup_all)

        self.logger.info("资源管理器已初始化")

    def register_resource(
        self,
        resource_id: str,
        resource_type: str,
        resource_obj: Any,
        cleanup_func: Callable[[], None],
        description: str = "",
    ) -> bool:
        """注册资源"""
        try:
            with self._instance_lock:
                if resource_id in self.resources:
                    self.logger.warning(f"资源 {resource_id} 已存在，将被覆盖")

                resource_info = ResourceInfo(
                    resource_id=resource_id,
                    resource_type=resource_type,
                    resource_obj=resource_obj,
                    cleanup_func=cleanup_func,
                    description=description,
                )

                self.resources[resource_id] = resource_info
                self.logger.debug(f"注册资源: {resource_id} ({resource_type})")
                self.resource_registered.emit(resource_id, resource_type)

                return True

        except Exception as e:
            self.logger.error(f"注册资源失败 {resource_id}: {e}")
            return False

    def unregister_resource(self, resource_id: str) -> bool:
        """注销资源（不执行清理）"""
        try:
            with self._instance_lock:
                if resource_id in self.resources:
                    del self.resources[resource_id]
                    self.logger.debug(f"注销资源: {resource_id}")
                    return True
                else:
                    self.logger.warning(f"资源 {resource_id} 不存在")
                    return False

        except Exception as e:
            self.logger.error(f"注销资源失败 {resource_id}: {e}")
            return False

    def cleanup_resource(self, resource_id: str) -> bool:
        """清理单个资源"""
        try:
            with self._instance_lock:
                if resource_id not in self.resources:
                    self.logger.warning(f"资源 {resource_id} 不存在")
                    return False

                resource_info = self.resources[resource_id]

                if resource_info.is_cleaned:
                    self.logger.debug(f"资源 {resource_id} 已经被清理")
                    return True

                # 执行清理函数
                try:
                    resource_info.cleanup_func()
                    resource_info.is_cleaned = True
                    self.logger.debug(
                        f"清理资源: {resource_id} ({resource_info.resource_type})"
                    )
                    self.resource_cleaned.emit(resource_id, resource_info.resource_type)
                    return True

                except Exception as cleanup_error:
                    self.logger.error(
                        f"清理资源 {resource_id} 时发生错误: {cleanup_error}"
                    )
                    return False

        except Exception as e:
            self.logger.error(f"清理资源失败 {resource_id}: {e}")
            return False

    def cleanup_by_type(self, resource_type: str) -> int:
        """按类型清理资源"""
        cleaned_count = 0

        try:
            with self._instance_lock:
                resource_ids = [
                    rid
                    for rid, info in self.resources.items()
                    if info.resource_type == resource_type and not info.is_cleaned
                ]

            for resource_id in resource_ids:
                if self.cleanup_resource(resource_id):
                    cleaned_count += 1

            self.logger.info(f"按类型清理完成 {resource_type}: {cleaned_count} 个资源")

        except Exception as e:
            self.logger.error(f"按类型清理资源失败 {resource_type}: {e}")

        return cleaned_count

    def cleanup_all(self) -> int:
        """清理所有资源"""
        cleaned_count = 0

        try:
            self.logger.info("开始清理所有资源...")

            # 按优先级清理（定时器 -> 线程 -> 进程 -> 其他）
            cleanup_order = [
                ResourceType.TIMER,
                ResourceType.THREAD,
                ResourceType.PROCESS,
                ResourceType.NETWORK_CONNECTION,
                ResourceType.DATABASE_CONNECTION,
                ResourceType.FILE_HANDLE,
                ResourceType.CUSTOM,
            ]

            for resource_type in cleanup_order:
                type_cleaned = self.cleanup_by_type(resource_type)
                cleaned_count += type_cleaned

            # 清理剩余的资源
            with self._instance_lock:
                remaining_ids = [
                    rid for rid, info in self.resources.items() if not info.is_cleaned
                ]

            for resource_id in remaining_ids:
                if self.cleanup_resource(resource_id):
                    cleaned_count += 1

            self.logger.info(f"资源清理完成，共清理 {cleaned_count} 个资源")
            self.cleanup_completed.emit(cleaned_count)

        except Exception as e:
            self.logger.error(f"清理所有资源时发生错误: {e}")

        return cleaned_count

    def get_resource_stats(self) -> Dict[str, Any]:
        """获取资源统计信息"""
        try:
            with self._instance_lock:
                total_resources = len(self.resources)
                cleaned_resources = sum(
                    1 for info in self.resources.values() if info.is_cleaned
                )

                type_stats = {}
                for info in self.resources.values():
                    resource_type = info.resource_type
                    if resource_type not in type_stats:
                        type_stats[resource_type] = {"total": 0, "cleaned": 0}
                    type_stats[resource_type]["total"] += 1
                    if info.is_cleaned:
                        type_stats[resource_type]["cleaned"] += 1

                return {
                    "total_resources": total_resources,
                    "cleaned_resources": cleaned_resources,
                    "pending_resources": total_resources - cleaned_resources,
                    "type_stats": type_stats,
                }

        except Exception as e:
            self.logger.error(f"获取资源统计信息失败: {e}")
            return {}

    def list_resources(
        self, resource_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出资源"""
        try:
            with self._instance_lock:
                resources = []
                for resource_id, info in self.resources.items():
                    if resource_type is None or info.resource_type == resource_type:
                        # 检查弱引用是否还有效
                        obj_status = "alive"
                        if hasattr(info.resource_obj, "__call__"):
                            try:
                                obj = info.resource_obj()
                                if obj is None:
                                    obj_status = "dead"
                            except:
                                obj_status = "dead"

                        resources.append(
                            {
                                "resource_id": resource_id,
                                "resource_type": info.resource_type,
                                "description": info.description,
                                "created_at": info.created_at,
                                "is_cleaned": info.is_cleaned,
                                "object_status": obj_status,
                            }
                        )

                return resources

        except Exception as e:
            self.logger.error(f"列出资源失败: {e}")
            return []

    def optimize_cleanup(self) -> Dict[str, Any]:
        """优化资源清理过程"""
        start_time = time.time()
        cleanup_stats = {
            "cleaned_count": 0,
            "failed_count": 0,
            "execution_time": 0.0,
            "memory_freed": 0.0,
        }

        try:
            # 记录清理前的内存使用
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            with self._instance_lock:
                # 批量清理已失效的弱引用
                dead_resources = []
                for resource_id, info in self.resources.items():
                    if hasattr(info.resource_obj, "__call__"):
                        try:
                            obj = info.resource_obj()
                            if obj is None:
                                dead_resources.append(resource_id)
                        except:
                            dead_resources.append(resource_id)

                # 移除失效资源
                for resource_id in dead_resources:
                    try:
                        del self.resources[resource_id]
                        cleanup_stats["cleaned_count"] += 1
                    except:
                        cleanup_stats["failed_count"] += 1

            # 记录清理后的内存使用
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            cleanup_stats["memory_freed"] = memory_before - memory_after
            cleanup_stats["execution_time"] = time.time() - start_time

            self.logger.info(f"资源清理完成: {cleanup_stats}")
            return cleanup_stats

        except Exception as e:
            self.logger.error(f"优化清理失败: {e}")
            cleanup_stats["execution_time"] = time.time() - start_time
            return cleanup_stats


# 全局资源管理器实例
resource_manager = ResourceManager()


# 便捷函数
def register_timer(timer_id: str, timer: QTimer, description: str = "") -> bool:
    """注册QTimer资源"""

    def cleanup() -> None:
        if timer and timer.isActive():
            timer.stop()

    return resource_manager.register_resource(
        timer_id, ResourceType.TIMER, timer, cleanup, description
    )


def register_custom_resource(
    resource_id: str,
    resource_obj: Any,
    cleanup_func: Callable[[], None],
    description: str = "",
) -> bool:
    """注册自定义资源"""
    return resource_manager.register_resource(
        resource_id, ResourceType.CUSTOM, resource_obj, cleanup_func, description
    )


def cleanup_on_exit() -> None:
    """应用退出时的清理函数"""
    resource_manager.cleanup_all()
