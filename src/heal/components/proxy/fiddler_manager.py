"""
Fiddler Manager
Handles Fiddler operations and proxy management
"""

import os
import subprocess
import time
from typing import Any, Optional

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import (
    InfoBar,
    InfoBarIcon,
    InfoBarPosition,
    PopupTeachingTip,
    PrimaryPushButton,
    TeachingTipTailPosition,
)

from src.heal.common.logging_config import get_logger
from src.heal.models.config import Info, cfg, get_json
from .proxy_cards import CustomFlyoutViewFiddler


class FiddlerManager(QObject):
    """Fiddler管理器"""

    # 信号
    fiddler_opened = Signal(bool)  # success
    backup_completed = Signal(bool, str)  # success, backup_path
    proxy_changed = Signal(bool)  # success

    def __init__(self, parent_widget: Optional[QWidget] = None) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger("fiddler_manager", module="FiddlerManager")
        self.fiddler_path = "tool/Fiddler/Fiddler.exe"

    def open_fiddler(self) -> bool:
        """打开Fiddler"""
        if os.path.exists(self.fiddler_path):
            try:
                subprocess.run(["start", self.fiddler_path], shell=True, check=True)
                Info(self.parent_widget, "S", 1000, "文件已打开!")
                self.logger.info("Fiddler 已成功打开。")
                self.fiddler_opened.emit(True)
                return True
            except subprocess.CalledProcessError as e:
                Info(self.parent_widget, "E", 3000, "打开文件失败！", str(e))
                self.logger.error(f"打开 Fiddler 失败: {e}")
                self.fiddler_opened.emit(False)
                return False
        else:
            self._show_file_not_found_error()
            self.fiddler_opened.emit(False)
            return False

    def _show_file_not_found_error(self) -> None:
        """显示文件未找到错误"""
        file_error = InfoBar(
            icon=InfoBarIcon.ERROR,
            title="找不到文件!",
            content="",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.parent_widget,
        )
        file_error_button = PrimaryPushButton("前往下载")
        file_error_button.clicked.connect(self._navigate_to_download)
        file_error.addWidget(file_error_button)
        file_error.show()
        self.logger.warning("Fiddler 文件不存在。")

    def _navigate_to_download(self) -> None:
        """导航到下载页面"""
        # 这里可以发出信号通知主界面切换到下载页面
        self.logger.info("请求导航到下载页面。")

    def show_fiddler_tip(self, target_button: Any) -> None:
        """显示Fiddler提示"""
        PopupTeachingTip.make(
            target=target_button,
            view=CustomFlyoutViewFiddler(parent=self.parent_widget),
            tailPosition=TeachingTipTailPosition.RIGHT,
            duration=-1,
            parent=self.parent_widget,
        )
        self.logger.info("Fiddler 提示已显示。")

    def backup_fiddler_script(self) -> None:
        """备份Fiddler脚本"""
        now_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
        backup_path = f"CustomRules-{now_time}.js"

        try:
            subprocess.run(
                f'copy /y "%userprofile%\\Documents\\Fiddler2\\Scripts\\CustomRules.js" "{backup_path}"',
                shell=True,
                check=True,
            )
            Info(self.parent_widget, "S", 1000, "备份成功!")
            self.logger.info(f"脚本已备份到 {backup_path}。")
            self.backup_completed.emit(True, backup_path)
        except subprocess.CalledProcessError as e:
            Info(self.parent_widget, "E", 3000, "备份失败！", str(e))
            self.logger.error(f"备份失败: {e}")
            self.backup_completed.emit(False, "")


class ProxyManager(QObject):
    """代理管理器"""

    # 信号
    proxy_status_changed = Signal(bool)  # success

    def __init__(self, parent_widget: Optional[QWidget] = None) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger("proxy_manager", module="ProxyManager")

    def reset_proxy(self) -> None:
        """重置代理设置"""
        try:
            port = get_json("./config/config.json", "PROXY_PORT")

            if cfg.proxyStatus.value:
                # 启用代理
                subprocess.run(
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f',
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=True,
                )
                subprocess.run(
                    f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer /d "127.0.0.1:{port}" /f',
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=True,
                )
                self.logger.info(f"代理已启用: 127.0.0.1:{port}")
            else:
                # 禁用代理
                subprocess.run(
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f',
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=True,
                )
                subprocess.run(
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer /d "" /f',
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=True,
                )
                self.logger.info("代理已禁用")

            Info(self.parent_widget, "S", 1000, "全局代理已更改！")
            self.logger.info("全局代理设置已更新。")
            self.proxy_status_changed.emit(True)

        except subprocess.CalledProcessError as e:
            Info(self.parent_widget, "E", 3000, "全局代理更改失败！", str(e))
            self.logger.error(f"更改全局代理失败: {e}")
            self.proxy_status_changed.emit(False)
