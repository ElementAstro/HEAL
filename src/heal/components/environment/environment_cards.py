"""
Environment Card Components
Custom card types for environment interface
"""

from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets import FluentIcon, HyperlinkButton, PrimaryPushButton

from ...common.logging_config import get_logger
from ...models.config import Info
from ...models.setting_card import SettingCard


class HyperlinkCardEnvironment(SettingCard):
    """环境链接卡片"""

    clicked = Signal()

    def __init__(
        self,
        title: str,
        content: Optional[str] = None,
        icon: FluentIcon = FluentIcon.LINK,
        links: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(icon, title, content or "")
        self.links = links or {}
        self.logger = get_logger(
            "environment_card", module="HyperlinkCardEnvironment")
        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI"""
        for name, url in self.links.items():
            link_button = HyperlinkButton(url, name, self)
            self.hBoxLayout.addWidget(
                link_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        copy_button = PrimaryPushButton("复制链接", self)
        copy_button.clicked.connect(
            lambda: self.copy_to_clipboard(next(iter(self.links.values()), ""))
        )
        self.hBoxLayout.addWidget(copy_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)

    def copy_to_clipboard(self, text: str) -> None:
        """复制链接到剪贴板"""
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(text)
        Info(self, "S", 1000, self.tr("链接已复制到剪贴板!"))
        self.logger.info(f"Copied URL to clipboard: {text}")


class PrimaryPushSettingCardDownload(SettingCard):
    """下载设置卡片"""

    download_signal = Signal(str)
    handle_download_started = Signal(str)

    def __init__(
        self,
        title: str,
        content: str,
        icon: FluentIcon = FluentIcon.DOWNLOAD,
        options: Optional[Any] = None,
    ) -> None:
        super().__init__(icon, title, content)
        self.options = options or []
        self.logger = get_logger(
            "environment_card", module="PrimaryPushSettingCardDownload"
        )
        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI"""
        for option in self.options:
            button = PrimaryPushButton(option["name"], self)
            button.clicked.connect(
                lambda _, key=option["key"]: self.download_signal.emit(key)
            )
            self.hBoxLayout.addWidget(button, 0, Qt.AlignmentFlag.AlignRight)
            self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addSpacing(16)

    def emit_download_signal(self, key: str) -> None:
        """发出下载信号"""
        self.download_signal.emit(key)
        self.logger.info(f"下载信号已发出: {key}")
