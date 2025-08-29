"""
Update Manager
Handles update checking and notifications
"""

from typing import Any

from PySide6.QtCore import QObject, Qt, Signal
from qfluentwidgets import HyperlinkButton, InfoBar, InfoBarIcon, InfoBarPosition

from ...common.logging_config import get_logger
from ...models.config import Info, cfg


class UpdateManager(QObject):
    """更新管理器"""

    # 信号
    update_checked = Signal(int, str)  # status, info

    def __init__(self, main_window: Any) -> None:
        super().__init__(main_window)
        self.main_window = main_window
        self.logger = get_logger("update_manager", module="UpdateManager")

    def handle_update_result(self, status: int, info: str) -> None:
        """处理更新检查结果"""
        self.update_checked.emit(status, info)

        if status == 2:
            # 有新版本可用
            self._show_update_available_notification(info)
        elif status == 1:
            # 当前是最新版本
            Info(
                self.main_window,
                "S",
                1000,
                f"{self.main_window.tr('当前是最新版本: ')}{info}",
            )
            self.logger.info(f"当前是最新版本: {info}")
        elif status == 0:
            # 检测更新失败
            Info(
                self.main_window,
                "E",
                3000,
                f"{self.main_window.tr('检测更新失败: ')}{info}",
            )
            self.logger.error(f"检测更新失败: {info}")

    def _show_update_available_notification(self, version: str) -> None:
        """显示有可用更新的通知"""
        update_info = InfoBar(
            icon=InfoBarIcon.WARNING,
            title=f"{self.main_window.tr('检测到新版本: ')}{version}",
            content="",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=self.main_window,
        )

        update_button = HyperlinkButton(
            cfg.URL_LATEST, self.main_window.tr("前往下载"))
        update_info.addWidget(update_button)
        update_info.show()

        self.logger.info(f"显示更新通知: {version}")

    def check_for_updates(self) -> None:
        """触发更新检查"""
        # 这里可以启动更新检查逻辑
        # 实际的更新检查可能在其他地方实现
        self.logger.info("更新检查已触发")
        pass
