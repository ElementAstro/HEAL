"""
Proxy Card Components
Custom card types for proxy interface
"""

from typing import Optional, Union

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, FlyoutViewBase, PrimaryPushButton

from ...common.logging_config import get_logger
from ...models.setting_card import SettingCard


class PrimaryPushSettingCardFiddler(SettingCard):
    """Fiddler设置卡片"""

    clicked_script = Signal()
    clicked_old = Signal()
    clicked_backup = Signal()

    def __init__(self, title: str, content: Optional[str] = None, icon: Union[FluentIcon, str] = FluentIcon.VPN) -> None:
        super().__init__(icon, title, content)
        self.logger = get_logger(
            "proxy_card", module="PrimaryPushSettingCardFiddler")
        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI"""
        self.button_script = PrimaryPushButton(self.tr("脚本打开"), self)
        self.button_old = PrimaryPushButton(self.tr("原版打开"), self)
        self.button_backup = PrimaryPushButton(self.tr("备份"), self)

        self.hBoxLayout.addWidget(self.button_script, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.button_old, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.button_backup, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        # 连接信号
        self.button_script.clicked.connect(self.clicked_script)
        self.button_old.clicked.connect(self.clicked_old)
        self.button_backup.clicked.connect(self.clicked_backup)


class CustomFlyoutViewFiddler(FlyoutViewBase):
    """Fiddler自定义浮窗视图"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.parent = parent
        self.logger = get_logger(
            "proxy_card", module="CustomFlyoutViewFiddler")
        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI"""
        self.gc_button = PrimaryPushButton("Grasscutter")
        self.ht_button = PrimaryPushButton("Hutao-GS")

        self.addWidget(self.gc_button)
        self.addWidget(self.ht_button)

        # 连接信号
        self.gc_button.clicked.connect(
            lambda: self.handle_fiddler_button("grasscutter")
        )
        self.ht_button.clicked.connect(
            lambda: self.handle_fiddler_button("hutao"))

    def handle_fiddler_button(self, mode: str) -> None:
        """处理Fiddler按钮点击"""
        try:
            # 导入必要的模块
            import subprocess

            import requests

            from ...models.config import Info

            url_mapping = {
                "grasscutter": "https://raw.githubusercontent.com/letheriver2007/Firefly-Launcher/master/resource/gc_scripts.js",
                "hutao": "https://raw.githubusercontent.com/letheriver2007/Firefly-Launcher/master/resource/ht_scripts.js",
            }

            url = url_mapping.get(mode)
            if not url:
                self.logger.error(f"未知模式: {mode}")
                return

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # 写入脚本文件
            script_path = f"%userprofile%\\Documents\\Fiddler2\\Scripts\\CustomRules.js"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            Info(self.parent, "S", 1000, f"{mode.title()} 脚本更新成功!")
            self.logger.info(f"{mode} 脚本已更新")

        except Exception as e:
            Info(self.parent, "E", 3000, self.tr("脚本更新失败！"), str(e))
            self.logger.error(f"脚本更新失败: {e}")
