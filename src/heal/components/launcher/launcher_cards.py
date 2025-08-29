"""
Launcher Card Components
Custom card types for launcher interface
"""

from typing import Optional, Union

from PySide6.QtCore import Qt
from qfluentwidgets import FluentIcon, HyperlinkButton

from ...common.logging_config import get_logger
from ...models.setting_card import SettingCard


class HyperlinkCardLauncher(SettingCard):
    """启动器链接卡片"""

    def __init__(self, title: str, content: Optional[str] = None, icon: Union[FluentIcon, str] = FluentIcon.LINK) -> None:
        super().__init__(icon, title, content)
        self.logger = get_logger(
            "launcher_card", module="HyperlinkCardLauncher")
        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI"""
        self.linkButton_launcher = HyperlinkButton(
            "https://github.com/letheriver2007/Firefly-Launcher",
            "Firefly-Launcher",
            self,
        )
        self.linkButton_audio = HyperlinkButton(
            "https://github.com/letheriver2007/Firefly-Launcher-Res",
            "Firefly-Launcher-Res",
            self,
        )

        self.hBoxLayout.addWidget(
            self.linkButton_launcher, 0, Qt.AlignmentFlag.AlignRight
        )
        self.hBoxLayout.addWidget(
            self.linkButton_audio, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
