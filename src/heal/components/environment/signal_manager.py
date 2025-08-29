"""
Environment Signal Manager
Handles signal connections and event management for environment interface
"""

from typing import Any, TYPE_CHECKING

from PySide6.QtCore import QObject, Qt, Signal
from qfluentwidgets import InfoBar, InfoBarIcon, InfoBarPosition, PrimaryPushButton

from ...common.logging_config import get_logger
from ...models.download_process import SubDownloadCMD
from .environment_cards import HyperlinkCardEnvironment, PrimaryPushSettingCardDownload

if TYPE_CHECKING:
    from ...interfaces.setting_interface import Setting


class EnvironmentSignalManager(QObject):
    """环境信号管理器"""

    # 信号
    restart_requested = Signal()
    download_to_page_requested = Signal(int)  # page_index

    def __init__(self, parent_widget: Any, download_interface_widget: Any) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.download_interface_widget = download_interface_widget
        self.logger = get_logger(
            "environment_signal_manager", module="EnvironmentSignalManager"
        )

        # 初始化下载命令处理器
        self.sub_download_cmd = SubDownloadCMD(parent_widget)

    def connect_card_signals(self, cards_container: Any) -> None:
        """连接卡片信号"""
        for i in range(cards_container.cardLayout.count()):
            item = cards_container.cardLayout.itemAt(i)
            if item is not None:
                card = item.widget()
                if isinstance(card, PrimaryPushSettingCardDownload):
                    card.download_signal.connect(
                        self.sub_download_cmd.handle_download_started
                    )
                    self.logger.debug(f"已连接下载信号: {card.titleLabel.text()}")
                elif isinstance(card, HyperlinkCardEnvironment) and "git" in card.links:
                    card.clicked.connect(self.handle_restart_info)
                    self.logger.debug(f"已连接重启信号: {card.titleLabel.text()}")

        self.logger.info("卡片信号已连接完成。")

    def connect_database_signals(self, database_manager: Any) -> None:
        """连接数据库管理器信号"""
        database_manager.database_not_found.connect(
            lambda: self.download_to_page_requested.emit(1)
        )
        self.logger.debug("数据库信号已连接。")

    def handle_restart_info(self) -> None:
        """处理重启信息显示"""
        restart_info = InfoBar(
            icon=InfoBarIcon.WARNING,
            title=self.parent_widget.tr("重启应用以使用Git命令!"),
            content="",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=self.parent_widget,
        )
        restart_button = PrimaryPushButton(self.parent_widget.tr("重启"))
        restart_button.clicked.connect(self._restart_application)
        restart_info.addWidget(restart_button)
        restart_info.show()
        self.logger.info("显示重启应用信息。")

    def _restart_application(self) -> None:
        """重启应用程序"""
        try:
            # 动态导入避免循环依赖
            from ...interfaces.setting_interface import Setting

            Setting.restart_application()
            self.restart_requested.emit()
        except Exception as e:
            self.logger.error(f"重启应用失败: {e}")

    def handle_download_started(self, download_key: str) -> None:
        """处理下载开始"""
        self.sub_download_cmd.handle_download_started(download_key)
        self.logger.info(f"下载已开始: {download_key}")

    def navigate_to_download_page(self) -> None:
        """导航到下载页面"""
        self.download_to_page_requested.emit(1)
        self.logger.info("导航到下载页面请求已发出。")
