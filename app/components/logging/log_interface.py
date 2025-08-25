"""
日志界面接口

提供一个统一的接口来访问日志面板，可以集成到主应用程序中
"""

from typing import Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, Signal

from app.common.logging_config import get_logger
from .log_panel import LogPanel
from .log_integration_manager import LogIntegrationManager, get_log_integration_manager

logger = get_logger(__name__)


class LogInterface(QWidget):
    """日志界面接口"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("LogInterface")
        
        # 创建日志面板
        self.log_panel = LogPanel(self)
        
        # 创建集成管理器
        self.integration_manager = LogIntegrationManager(self.log_panel)
        
        # 设置全局集成管理器
        global _integration_manager
        _integration_manager = self.integration_manager
        
        # 设置布局
        from PySide6.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.log_panel)
        
        logger.info("日志界面接口初始化完成")
    
    def show_server_log(self, server_name: str):
        """显示服务器日志"""
        self.integration_manager.show_server_log_in_panel(server_name)
    
    def show_process_log(self, process_name: str):
        """显示进程日志"""
        self.integration_manager.show_process_log_in_panel(process_name)
    
    def show_performance_log(self, operation_name: Optional[str] = None):
        """显示性能日志"""
        self.integration_manager.show_performance_log_in_panel(operation_name)
    
    def show_download_log(self, download_id: Optional[str] = None):
        """显示下载日志"""
        self.integration_manager.show_download_log_in_panel(download_id)
    
    def show_network_log(self, request_type: Optional[str] = None):
        """显示网络日志"""
        self.integration_manager.show_network_log_in_panel(request_type)
    
    def refresh_logs(self):
        """刷新日志"""
        if self.log_panel and hasattr(self.log_panel, 'refresh_logs'):
            self.log_panel.refresh_logs()
    
    def get_log_panel(self) -> LogPanel:
        """获取日志面板实例"""
        return self.log_panel
    
    def get_integration_manager(self) -> LogIntegrationManager:
        """获取集成管理器实例"""
        return self.integration_manager


# 全局日志界面实例
_log_interface: Optional[LogInterface] = None


def get_log_interface() -> Optional[LogInterface]:
    """获取全局日志界面实例"""
    return _log_interface


def set_log_interface(interface: LogInterface):
    """设置全局日志界面实例"""
    global _log_interface
    _log_interface = interface


def create_log_interface(parent: Optional[QWidget] = None) -> LogInterface:
    """创建日志界面实例"""
    interface = LogInterface(parent)
    set_log_interface(interface)
    return interface


# 便捷函数
def show_server_log(server_name: str):
    """显示服务器日志的便捷函数"""
    interface = get_log_interface()
    if interface:
        interface.show_server_log(server_name)
    else:
        logger.warning("日志界面未初始化，无法显示服务器日志")


def show_process_log(process_name: str):
    """显示进程日志的便捷函数"""
    interface = get_log_interface()
    if interface:
        interface.show_process_log(process_name)
    else:
        logger.warning("日志界面未初始化，无法显示进程日志")


def show_performance_log(operation_name: Optional[str] = None):
    """显示性能日志的便捷函数"""
    interface = get_log_interface()
    if interface:
        interface.show_performance_log(operation_name)
    else:
        logger.warning("日志界面未初始化，无法显示性能日志")


def show_download_log(download_id: Optional[str] = None):
    """显示下载日志的便捷函数"""
    interface = get_log_interface()
    if interface:
        interface.show_download_log(download_id)
    else:
        logger.warning("日志界面未初始化，无法显示下载日志")


def show_network_log(request_type: Optional[str] = None):
    """显示网络日志的便捷函数"""
    interface = get_log_interface()
    if interface:
        interface.show_network_log(request_type)
    else:
        logger.warning("日志界面未初始化，无法显示网络日志")
