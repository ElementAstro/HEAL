"""
Environment Database Manager
Handles MongoDB operations and management
"""

import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import InfoBar, InfoBarIcon, InfoBarPosition, PrimaryPushButton

from src.heal.common.logging_config import get_logger
from src.heal.models.config import Info


class EnvironmentDatabaseManager(QObject):
    """环境数据库管理器"""

    # 信号
    database_started = Signal()
    database_start_failed = Signal(str)
    database_not_found = Signal()

    def __init__(self, parent_widget: QWidget) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger(
            "environment_db_manager", module="EnvironmentDatabaseManager"
        )
        self.mongo_exe = Path("tool") / "mongodb" / "mongod.exe"

    def handle_mongo_db_open(self) -> None:
        """处理MongoDB打开操作"""
        if self.mongo_exe.exists():
            try:
                subprocess.Popen(
                    [
                        "cmd",
                        "/c",
                        f'cd /d "{self.mongo_exe.parent}" && mongod --dbpath data --port 27017',
                    ],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
                Info(
                    self.parent_widget,
                    "S",
                    1000,
                    self.parent_widget.tr("数据库已开始运行!"),
                )
                self.database_started.emit()
                self.logger.info("MongoDB 已启动。")
            except Exception as e:
                error_msg = str(e)
                Info(
                    self.parent_widget,
                    "E",
                    3000,
                    self.parent_widget.tr("启动数据库失败！"),
                    error_msg,
                )
                self.database_start_failed.emit(error_msg)
                self.logger.error(f"启动 MongoDB 失败: {e}")
        else:
            self._show_database_not_found_error()

    def _show_database_not_found_error(self) -> None:
        """显示数据库未找到错误"""
        file_error = InfoBar(
            icon=InfoBarIcon.ERROR,
            title=self.parent_widget.tr("找不到数据库!"),
            content="",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.parent_widget,
        )
        file_error_button = PrimaryPushButton(
            self.parent_widget.tr("前往下载"), self.parent_widget
        )

        # 连接到下载页面的信号（需要外部连接）
        self.database_not_found.emit()

        file_error.addWidget(file_error_button)
        file_error.show()
        self.logger.warning("MongoDB 文件不存在。")

        return file_error_button

    def check_database_exists(self) -> bool:
        """检查数据库是否存在"""
        return self.mongo_exe.exists()

    def get_database_path(self) -> Path:
        """获取数据库路径"""
        return self.mongo_exe

    def get_database_status(self) -> dict:
        """获取数据库状态"""
        return {
            "exists": self.check_database_exists(),
            "path": str(self.mongo_exe),
            "executable": (
                self.mongo_exe.is_file() if self.mongo_exe.exists() else False
            ),
        }
