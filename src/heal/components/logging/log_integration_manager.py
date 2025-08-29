"""
日志集成管理器

负责将现有的各种日志显示组件集成到统一日志面板中：
- 服务器日志对话框集成
- 进程监控日志集成
- 性能监控日志集成
- 其他模块日志集成
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget
from qfluentwidgets import InfoBar, InfoBarPosition, TextEdit

from ...common.logging_config import get_logger
from .log_panel import LogPanel

logger = get_logger(__name__)


class LogIntegrationManager(QObject):
    """日志集成管理器"""

    log_requested = Signal(str, str)  # 日志类型, 日志内容

    def __init__(self, log_panel: LogPanel) -> None:
        super().__init__()
        self.log_panel = log_panel
        self.integrated_components: dict[str, Any] = {}

        # 注册集成的日志源
        self._register_log_sources()

        logger.info("日志集成管理器初始化完成")

    def _register_log_sources(self) -> None:
        """注册日志源"""
        # 服务器日志
        self.integrated_components["server_logs"] = {
            "name": "服务器日志",
            "reader": self._read_server_log,
            "path_pattern": "./logs/{name}.log",
        }

        # 进程日志
        self.integrated_components["process_logs"] = {
            "name": "进程日志",
            "reader": self._read_process_log,
            "path_pattern": "./logs/process_manager.log",
        }

        # 性能监控日志
        self.integrated_components["performance_logs"] = {
            "name": "性能监控日志",
            "reader": self._read_performance_log,
            "path_pattern": "./logs/performance.log",
        }

        # 下载日志
        self.integrated_components["download_logs"] = {
            "name": "下载日志",
            "reader": self._read_download_log,
            "path_pattern": "./logs/downloads.log",
        }

        # 网络日志
        self.integrated_components["network_logs"] = {
            "name": "网络日志",
            "reader": self._read_network_log,
            "path_pattern": "./logs/network.log",
        }

    def show_server_log_in_panel(self, server_name: str) -> None:
        """在统一面板中显示服务器日志"""
        try:
            log_content = self._read_server_log(server_name)
            if log_content:
                # 切换到对应的日志文件标签
                self._switch_to_log_tab("application")
                # 可以添加过滤条件来只显示特定服务器的日志
                self._apply_server_filter(server_name)
            else:
                self._show_no_log_message(f"服务器 {server_name}")
        except Exception as e:
            logger.error(f"显示服务器日志失败: {e}")
            self._show_error_message(f"显示服务器 {server_name} 日志失败: {str(e)}")

    def show_process_log_in_panel(self, process_name: str) -> None:
        """在统一面板中显示进程日志"""
        try:
            # 切换到进程管理日志标签
            self._switch_to_log_tab("process_manager")
            # 应用进程过滤
            self._apply_process_filter(process_name)
        except Exception as e:
            logger.error(f"显示进程日志失败: {e}")
            self._show_error_message(f"显示进程 {process_name} 日志失败: {str(e)}")

    def show_performance_log_in_panel(self, operation_name: Optional[str] = None) -> None:
        """在统一面板中显示性能日志"""
        try:
            # 切换到性能日志标签
            self._switch_to_log_tab("performance")
            # 如果指定了操作名，应用过滤
            if operation_name:
                self._apply_performance_filter(operation_name)
        except Exception as e:
            logger.error(f"显示性能日志失败: {e}")
            self._show_error_message(f"显示性能日志失败: {str(e)}")

    def show_download_log_in_panel(self, download_id: Optional[str] = None) -> None:
        """在统一面板中显示下载日志"""
        try:
            # 切换到下载日志标签
            self._switch_to_log_tab("downloads")
            # 如果指定了下载ID，应用过滤
            if download_id:
                self._apply_download_filter(download_id)
        except Exception as e:
            logger.error(f"显示下载日志失败: {e}")
            self._show_error_message(f"显示下载日志失败: {str(e)}")

    def show_network_log_in_panel(self, request_type: Optional[str] = None) -> None:
        """在统一面板中显示网络日志"""
        try:
            # 切换到网络日志标签
            self._switch_to_log_tab("network")
            # 如果指定了请求类型，应用过滤
            if request_type:
                self._apply_network_filter(request_type)
        except Exception as e:
            logger.error(f"显示网络日志失败: {e}")
            self._show_error_message(f"显示网络日志失败: {str(e)}")

    def _read_server_log(self, server_name: str) -> str:
        """读取服务器日志文件"""
        log_path = f"./logs/{server_name}.log"
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as file:
                    return file.read()
            except Exception as e:
                logger.error(f"读取服务器日志文件失败: {e}")
                return f"读取日志文件失败: {str(e)}"
        else:
            return f"日志文件不存在: {log_path}"

    def _read_process_log(self, process_name: str) -> str:
        """读取进程日志"""
        # 从进程管理器获取日志内容
        # 这里需要根据实际的进程管理器实现来调整
        log_path = "./logs/process_manager.log"
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    # 过滤出特定进程的日志
                    lines = content.split("\n")
                    process_lines = [
                        line for line in lines if process_name in line]
                    return "\n".join(process_lines)
            except Exception as e:
                logger.error(f"读取进程日志失败: {e}")
                return f"读取进程日志失败: {str(e)}"
        return "进程日志文件不存在"

    def _read_performance_log(self, operation_name: Optional[str] = None) -> str:
        """读取性能日志"""
        log_path = "./logs/performance.log"
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    if operation_name:
                        # 过滤出特定操作的日志
                        lines = content.split("\n")
                        operation_lines = [
                            line for line in lines if operation_name in line
                        ]
                        return "\n".join(operation_lines)
                    return content
            except Exception as e:
                logger.error(f"读取性能日志失败: {e}")
                return f"读取性能日志失败: {str(e)}"
        return "性能日志文件不存在"

    def _read_download_log(self, download_id: Optional[str] = None) -> str:
        """读取下载日志"""
        log_path = "./logs/downloads.log"
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    if download_id:
                        # 过滤出特定下载的日志
                        lines = content.split("\n")
                        download_lines = [
                            line for line in lines if download_id in line]
                        return "\n".join(download_lines)
                    return content
            except Exception as e:
                logger.error(f"读取下载日志失败: {e}")
                return f"读取下载日志失败: {str(e)}"
        return "下载日志文件不存在"

    def _read_network_log(self, request_type: Optional[str] = None) -> str:
        """读取网络日志"""
        log_path = "./logs/network.log"
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    if request_type:
                        # 过滤出特定类型的网络请求日志
                        lines = content.split("\n")
                        request_lines = [
                            line for line in lines if request_type in line]
                        return "\n".join(request_lines)
                    return content
            except Exception as e:
                logger.error(f"读取网络日志失败: {e}")
                return f"读取网络日志失败: {str(e)}"
        return "网络日志文件不存在"

    def _switch_to_log_tab(self, tab_name: str) -> None:
        """切换到指定的日志标签页"""
        if hasattr(self.log_panel, "log_viewer") and self.log_panel.log_viewer:
            viewer = self.log_panel.log_viewer
            if hasattr(viewer, "tab_widget"):
                # 查找对应的标签页
                for i in range(viewer.tab_widget.count()):
                    if viewer.tab_widget.tabText(i).lower() == tab_name.lower():
                        viewer.tab_widget.setCurrentIndex(i)
                        break

    def _apply_server_filter(self, server_name: str) -> None:
        """应用服务器过滤"""
        if hasattr(self.log_panel, "log_filter") and self.log_panel.log_filter:
            # 设置关键词过滤
            filter_config = {"keywords": server_name, "case_sensitive": False}
            self.log_panel.log_filter.set_filters(filter_config)

    def _apply_process_filter(self, process_name: str) -> None:
        """应用进程过滤"""
        if hasattr(self.log_panel, "log_filter") and self.log_panel.log_filter:
            filter_config = {"keywords": process_name, "case_sensitive": False}
            self.log_panel.log_filter.set_filters(filter_config)

    def _apply_performance_filter(self, operation_name: str) -> None:
        """应用性能过滤"""
        if hasattr(self.log_panel, "log_filter") and self.log_panel.log_filter:
            filter_config = {
                "keywords": operation_name,
                "levels": {"INFO", "DEBUG"},  # 性能日志通常是INFO或DEBUG级别
                "case_sensitive": False,
            }
            self.log_panel.log_filter.set_filters(filter_config)

    def _apply_download_filter(self, download_id: str) -> None:
        """应用下载过滤"""
        if hasattr(self.log_panel, "log_filter") and self.log_panel.log_filter:
            filter_config = {"keywords": download_id, "case_sensitive": False}
            self.log_panel.log_filter.set_filters(filter_config)

    def _apply_network_filter(self, request_type: str) -> None:
        """应用网络过滤"""
        if hasattr(self.log_panel, "log_filter") and self.log_panel.log_filter:
            filter_config = {"keywords": request_type, "case_sensitive": False}
            self.log_panel.log_filter.set_filters(filter_config)

    def _show_no_log_message(self, source_name: str) -> None:
        """显示无日志消息"""
        if hasattr(self.log_panel, "parent") and self.log_panel.parent:
            InfoBar.warning(
                title="日志为空",
                content=f"{source_name} 暂无日志输出",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.log_panel.parent,
            )

    def _show_error_message(self, error_message: str) -> None:
        """显示错误消息"""
        if hasattr(self.log_panel, "parent") and self.log_panel.parent:
            InfoBar.error(
                title="日志显示失败",
                content=error_message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self.log_panel.parent,
            )

    def get_available_log_sources(self) -> Dict[str, Dict]:
        """获取可用的日志源"""
        return self.integrated_components.copy()

    def register_custom_log_source(
        self, name: str, reader: Callable[..., Any], path_pattern: str
    ) -> None:
        """注册自定义日志源"""
        self.integrated_components[name] = {
            "name": name,
            "reader": reader,
            "path_pattern": path_pattern,
        }
        logger.info(f"注册自定义日志源: {name}")


# 全局集成管理器实例
_integration_manager: Optional[LogIntegrationManager] = None


def get_log_integration_manager(
    log_panel: Optional[LogPanel] = None,
) -> Optional[LogIntegrationManager]:
    """获取日志集成管理器实例"""
    global _integration_manager
    if _integration_manager is None and log_panel is not None:
        _integration_manager = LogIntegrationManager(log_panel)
    return _integration_manager


def show_server_log(server_name: str) -> None:
    """显示服务器日志的便捷函数"""
    manager = get_log_integration_manager()
    if manager:
        manager.show_server_log_in_panel(server_name)


def show_process_log(process_name: str) -> None:
    """显示进程日志的便捷函数"""
    manager = get_log_integration_manager()
    if manager:
        manager.show_process_log_in_panel(process_name)


def show_performance_log(operation_name: Optional[str] = None) -> None:
    """显示性能日志的便捷函数"""
    manager = get_log_integration_manager()
    if manager:
        manager.show_performance_log_in_panel(operation_name)


def show_download_log(download_id: Optional[str] = None) -> None:
    """显示下载日志的便捷函数"""
    manager = get_log_integration_manager()
    if manager:
        manager.show_download_log_in_panel(download_id)


def show_network_log(request_type: Optional[str] = None) -> None:
    """显示网络日志的便捷函数"""
    manager = get_log_integration_manager()
    if manager:
        manager.show_network_log_in_panel(request_type)
