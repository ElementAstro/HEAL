"""
Launcher Card Components
Custom card types for launcher interface
"""

from typing import Optional
from PySide6.QtCore import Qt
from qfluentwidgets import FluentIcon, HyperlinkButton
from app.model.setting_card import SettingCard
from app.common.logging_config import get_logger


class HyperlinkCardLauncher(SettingCard):
    """启动器链接卡片"""
    
    def __init__(self, title: str, content: Optional[str] = None, icon=FluentIcon.LINK):
        super().__init__(icon, title, content)
        self.logger = get_logger('launcher_card', module='HyperlinkCardLauncher')
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.linkButton_launcher = HyperlinkButton(
            'https://github.com/letheriver2007/Firefly-Launcher',
            'Firefly-Launcher', self
        )
        self.linkButton_audio = HyperlinkButton(
            'https://github.com/letheriver2007/Firefly-Launcher-Res',
            'Firefly-Launcher-Res', self
        )
        
        self.hBoxLayout.addWidget(
            self.linkButton_launcher, 0, Qt.AlignmentFlag.AlignRight
        )
        self.hBoxLayout.addWidget(
            self.linkButton_audio, 0, Qt.AlignmentFlag.AlignRight
        )
        self.hBoxLayout.addSpacing(16)
