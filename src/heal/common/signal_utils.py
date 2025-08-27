"""
Signal Utilities - 统一信号管理工具
消除项目中信号连接的重复代码，提供信号管理和调试功能
"""

import weakref
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from PySide6.QtCore import QMetaObject, QObject, Qt, Signal

from .logging_config import get_logger

logger = get_logger(__name__)


class ConnectionType(Enum):
    """连接类型枚举"""

    AUTO = Qt.ConnectionType.AutoConnection
    DIRECT = Qt.ConnectionType.DirectConnection
    QUEUED = Qt.ConnectionType.QueuedConnection
    BLOCKING_QUEUED = Qt.ConnectionType.BlockingQueuedConnection


@dataclass
class SignalConnection:
    """信号连接信息"""

    source_obj: weakref.ref
    signal_name: str
    target_obj: Union[weakref.ref, Callable]
    slot_name: Optional[str]
    connection_type: ConnectionType
    connection_id: str
    created_at: float = field(
        default_factory=lambda: __import__("time").time())
    is_active: bool = True
    call_count: int = 0
    last_called: Optional[float] = None

    def get_source_obj(self) -> Any:
        """获取源对象"""
        return self.source_obj()

    def get_target_obj(self) -> Any:
        """获取目标对象"""
        if isinstance(self.target_obj, weakref.ref):
            return self.target_obj()
        return self.target_obj

    def is_valid(self) -> bool:
        """检查连接是否有效"""
        source = self.get_source_obj()
        target = self.get_target_obj()

        if source is None:
            return False

        if callable(target):
            return True

        return target is not None


class SignalManager(QObject):
    """信号管理器 - 统一管理信号连接和调试"""

    # 管理器信号
    connection_created = Signal(str)  # connection_id
    connection_removed = Signal(str)  # connection_id
    signal_emitted = Signal(str, str, object)  # source, signal_name, args

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.logger = logger.bind(component="SignalManager")

        # 连接注册表
        self.connections: Dict[str, SignalConnection] = {}
        self.connection_counter = 0

        # 调试选项
        self.debug_mode = False
        self.track_calls = False

        self.logger.debug("信号管理器已初始化")

    def enable_debug(self, track_calls: bool = True) -> None:
        """启用调试模式"""
        self.debug_mode = True
        self.track_calls = track_calls
        self.logger.info("信号调试模式已启用")

    def disable_debug(self) -> None:
        """禁用调试模式"""
        self.debug_mode = False
        self.track_calls = False
        self.logger.info("信号调试模式已禁用")

    def connect_signal(
        self,
        source_obj: QObject,
        signal_name: str,
        target: Union[QObject, Callable],
        slot_name: Optional[str] = None,
        connection_type: ConnectionType = ConnectionType.AUTO,
        connection_id: Optional[str] = None,
    ) -> str:
        """
        连接信号和槽

        Args:
            source_obj: 信号源对象
            signal_name: 信号名称
            target: 目标对象或回调函数
            slot_name: 槽名称（如果target是对象）
            connection_type: 连接类型
            connection_id: 连接ID（可选）

        Returns:
            str: 连接ID
        """
        try:
            # 生成连接ID
            if connection_id is None:
                self.connection_counter += 1
                connection_id = f"conn_{self.connection_counter}"

            # 验证信号存在
            signal = getattr(source_obj, signal_name, None)
            if signal is None or not isinstance(signal, Signal):
                raise AttributeError(f"对象 {source_obj} 没有信号 {signal_name}")

            # 准备目标
            if callable(target) and not isinstance(target, QObject):
                # 直接连接到函数
                target_callable = target
                target_ref = target  # 函数不使用弱引用
                slot_name = getattr(target, "__name__", "anonymous_function")
            else:
                # 连接到对象的槽
                if slot_name is None:
                    raise ValueError("连接到对象时必须指定槽名称")

                slot = getattr(target, slot_name, None)
                if slot is None:
                    raise AttributeError(f"对象 {target} 没有槽 {slot_name}")

                target_callable = slot
                target_ref = weakref.ref(target)

            # 如果启用调试模式，包装目标函数
            if self.debug_mode:
                original_callable = target_callable

                def debug_wrapper(*args: Any, **kwargs: Any) -> Any:
                    if self.track_calls:
                        conn = self.connections.get(connection_id)
                        if conn:
                            conn.call_count += 1
                            conn.last_called = __import__("time").time()

                    if self.debug_mode:
                        self.signal_emitted.emit(
                            str(source_obj),
                            signal_name,
                            {"args": args, "kwargs": kwargs},
                        )
                        self.logger.debug(
                            f"信号触发: {source_obj}.{signal_name} -> {target}.{slot_name}"
                        )

                    return original_callable(*args, **kwargs)

                target_callable = debug_wrapper

            # 执行连接
            signal.connect(target_callable, connection_type.value)

            # 记录连接信息
            connection = SignalConnection(
                source_obj=weakref.ref(source_obj),
                signal_name=signal_name,
                target_obj=target_ref,
                slot_name=slot_name,
                connection_type=connection_type,
                connection_id=connection_id,
            )

            self.connections[connection_id] = connection
            self.connection_created.emit(connection_id)

            self.logger.debug(
                f"信号连接成功: {connection_id} ({source_obj}.{signal_name} -> {target}.{slot_name})"
            )
            return connection_id

        except Exception as e:
            self.logger.error(f"信号连接失败: {e}")
            raise

    def disconnect_signal(self, connection_id: str) -> bool:
        """
        断开信号连接

        Args:
            connection_id: 连接ID

        Returns:
            bool: 是否断开成功
        """
        try:
            if connection_id not in self.connections:
                self.logger.warning(f"连接不存在: {connection_id}")
                return False

            connection = self.connections[connection_id]
            source_obj = connection.get_source_obj()

            if source_obj is None:
                self.logger.warning(f"源对象已被销毁: {connection_id}")
                del self.connections[connection_id]
                return False

            # 获取信号
            signal = getattr(source_obj, connection.signal_name, None)
            if signal is None:
                self.logger.warning(f"信号不存在: {connection.signal_name}")
                del self.connections[connection_id]
                return False

            # 断开连接
            target = connection.get_target_obj()
            if target is not None:
                if callable(target):
                    signal.disconnect(target)
                else:
                    if connection.slot_name:
                        slot = getattr(target, connection.slot_name, None)
                        if slot:
                            signal.disconnect(slot)

            # 移除记录
            connection.is_active = False
            del self.connections[connection_id]
            self.connection_removed.emit(connection_id)

            self.logger.debug(f"信号连接已断开: {connection_id}")
            return True

        except Exception as e:
            self.logger.error(f"断开信号连接失败 {connection_id}: {e}")
            return False

    def batch_connect(self, connections: List[Dict[str, Any]]) -> List[str]:
        """
        批量连接信号

        Args:
            connections: 连接配置列表

        Returns:
            List[str]: 成功创建的连接ID列表
        """
        connection_ids = []

        for i, conn_config in enumerate(connections):
            try:
                connection_id = self.connect_signal(
                    source_obj=conn_config["source"],
                    signal_name=conn_config["signal"],
                    target=conn_config["target"],
                    slot_name=conn_config.get("slot"),
                    connection_type=conn_config.get(
                        "type", ConnectionType.AUTO),
                    connection_id=conn_config.get("id", f"batch_conn_{i}"),
                )
                connection_ids.append(connection_id)

            except Exception as e:
                self.logger.error(f"批量连接失败 (索引 {i}): {e}")

        self.logger.info(
            f"批量信号连接完成: {len(connection_ids)}/{len(connections)} 成功"
        )
        return connection_ids

    def cleanup_invalid_connections(self) -> int:
        """
        清理无效连接

        Returns:
            int: 清理的连接数量
        """
        invalid_ids = []

        for connection_id, connection in self.connections.items():
            if not connection.is_valid():
                invalid_ids.append(connection_id)

        for connection_id in invalid_ids:
            del self.connections[connection_id]
            self.connection_removed.emit(connection_id)

        if invalid_ids:
            self.logger.info(f"清理了 {len(invalid_ids)} 个无效连接")

        return len(invalid_ids)

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """获取连接信息"""
        if connection_id not in self.connections:
            return None

        connection = self.connections[connection_id]
        source_obj = connection.get_source_obj()
        target_obj = connection.get_target_obj()

        return {
            "connection_id": connection_id,
            "source_obj": str(source_obj) if source_obj else "None",
            "signal_name": connection.signal_name,
            "target_obj": str(target_obj) if target_obj else "None",
            "slot_name": connection.slot_name,
            "connection_type": connection.connection_type.name,
            "created_at": connection.created_at,
            "is_active": connection.is_active,
            "is_valid": connection.is_valid(),
            "call_count": connection.call_count,
            "last_called": connection.last_called,
        }

    def get_all_connections(self) -> List[Dict[str, Any]]:
        """获取所有连接信息"""
        connections = []
        for connection_id in self.connections.keys():
            info = self.get_connection_info(connection_id)
            if info is not None:
                connections.append(info)
        return connections

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_connections = len(self.connections)
        valid_connections = sum(
            1 for conn in self.connections.values() if conn.is_valid()
        )
        total_calls = sum(
            conn.call_count for conn in self.connections.values())

        return {
            "total_connections": total_connections,
            "valid_connections": valid_connections,
            "invalid_connections": total_connections - valid_connections,
            "total_signal_calls": total_calls,
            "debug_mode": self.debug_mode,
            "track_calls": self.track_calls,
        }

    def disconnect_all(self) -> int:
        """断开所有连接"""
        connection_ids = list(self.connections.keys())
        success_count = 0

        for connection_id in connection_ids:
            if self.disconnect_signal(connection_id):
                success_count += 1

        self.logger.info(
            f"断开所有连接完成: {success_count}/{len(connection_ids)} 成功"
        )
        return success_count


# 全局信号管理器实例
global_signal_manager = SignalManager()


# 便捷函数
def connect_signal(
    source_obj: QObject,
    signal_name: str,
    target: Union[QObject, Callable],
    slot_name: Optional[str] = None,
    connection_type: ConnectionType = ConnectionType.AUTO,
) -> str:
    """连接信号的便捷函数"""
    return global_signal_manager.connect_signal(
        source_obj, signal_name, target, slot_name, connection_type
    )


def disconnect_signal(connection_id: str) -> bool:
    """断开信号的便捷函数"""
    return global_signal_manager.disconnect_signal(connection_id)


def batch_connect_signals(connections: List[Dict[str, Any]]) -> List[str]:
    """批量连接信号的便捷函数"""
    return global_signal_manager.batch_connect(connections)


def enable_signal_debug() -> None:
    """启用信号调试"""
    global_signal_manager.enable_debug()


def disable_signal_debug() -> None:
    """禁用信号调试"""
    global_signal_manager.disable_debug()


def cleanup_signals() -> int:
    """清理信号连接"""
    return global_signal_manager.cleanup_invalid_connections()
