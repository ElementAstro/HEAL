"""
日志界面 - 统一日志管理界面

提供完整的日志查看、过滤、导出和管理功能
"""

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import ScrollArea

from ..common.logging_config import get_logger, log_performance, with_correlation_id

# Import logging components
from ..components.logging import LogInterface, create_log_interface
from ..models.style_sheet import StyleSheet

# 使用统一日志配置
logger = get_logger(__name__)


class LogManagement(ScrollArea):
    """日志管理界面"""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName(text)
        self._parent_widget = parent

        logger.info(f"初始化日志管理界面: {text}")

        # 创建滚动区域
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        # 初始化日志界面
        self._init_log_interface()

        # 设置样式
        self._setup_style()

        # 设置滚动区域
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        logger.debug("日志管理界面初始化完成")

    def _init_log_interface(self) -> None:
        """初始化日志界面组件"""
        try:
            # 创建统一日志界面
            self.log_interface = create_log_interface(self.scrollWidget)

            # 添加到布局
            self.vBoxLayout.addWidget(self.log_interface)
            self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

            logger.info("日志界面组件创建成功")

        except Exception as e:
            logger.error(f"创建日志界面失败: {e}")
            # 创建错误提示
            from qfluentwidgets import InfoBar, InfoBarPosition

            InfoBar.error(
                title="日志界面初始化失败",
                content=f"无法创建日志界面: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self,
            )

    def _setup_style(self) -> None:
        """设置样式"""
        try:
            # 应用样式表
            StyleSheet.LOG_INTERFACE.apply(self)
        except Exception as e:
            logger.warning(f"应用样式表失败: {e}")

    @log_performance("refresh_log_interface")
    def refresh_logs(self) -> None:
        """刷新日志"""
        if hasattr(self, "log_interface") and self.log_interface:
            self.log_interface.refresh_logs()
            logger.info("日志界面已刷新")

    def show_server_log(self, server_name: str) -> None:
        """显示服务器日志"""
        if hasattr(self, "log_interface") and self.log_interface:
            self.log_interface.show_server_log(server_name)

    def show_process_log(self, process_name: str) -> None:
        """显示进程日志"""
        if hasattr(self, "log_interface") and self.log_interface:
            self.log_interface.show_process_log(process_name)

    def show_performance_log(self, operation_name: Optional[str] = None) -> None:
        """显示性能日志"""
        if hasattr(self, "log_interface") and self.log_interface:
            self.log_interface.show_performance_log(operation_name)

    def show_download_log(self, download_id: Optional[str] = None) -> None:
        """显示下载日志"""
        if hasattr(self, "log_interface") and self.log_interface:
            self.log_interface.show_download_log(download_id)

    def show_network_log(self, request_type: Optional[str] = None) -> None:
        """显示网络日志"""
        if hasattr(self, "log_interface") and self.log_interface:
            self.log_interface.show_network_log(request_type)

    def get_log_panel(self) -> Any:
        """获取日志面板实例"""
        if hasattr(self, "log_interface") and self.log_interface:
            return self.log_interface.get_log_panel()
        return None

    def get_integration_manager(self) -> Any:
        """获取集成管理器实例"""
        if hasattr(self, "log_interface") and self.log_interface:
            return self.log_interface.get_integration_manager()
        return None


# 为了向后兼容，创建别名
Logs = LogManagement
