"""
Download Handler
Manages download operations and execution
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets import InfoBar, InfoBarPosition

from src.heal.common.i18n import t
from src.heal.common.logging_config import get_logger
from src.heal.models.config import cfg
from src.heal.models.message_download import (
    MessageDownload,
    MessageFiddler,
    MessageGit,
    MessageJava,
    MessageLauncher,
    MessageLunarCore,
    MessageLunarCoreRes,
    MessageMitmdump,
    MessageMongoDB,
    MessageNINA,
    MessagePHD2,
    MessagePython,
    MessageSharpCap,
)


class DownloadHandler(QObject):
    """下载处理器"""

    # 信号
    download_started = Signal(str, str)  # name, command
    download_completed = Signal(str, bool)  # name, success
    file_exists = Signal(str)  # file_path

    def __init__(self, parent_widget: QWidget) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger("download_handler", module="DownloadHandler")

        # 初始化下载映射
        self._init_download_mapping()

    def _init_download_mapping(self) -> None:
        """初始化下载映射"""
        # 使用默认的下载配置，避免访问不存在的配置属性
        default_url = "https://example.com/default"
        default_mirror = "https://mirror.example.com/default"

        self.download_mapping: Dict[
            str, Tuple[Any, str, str, Optional[str], Optional[str]]
        ] = {
            "launcher": (
                MessageLauncher,
                "url",
                getattr(cfg, "DOWNLOAD_COMMANDS_LAUNCHER", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_LAUNCHER_MIRROR", default_mirror),
                None,
            ),
            "python": (
                MessagePython,
                "url",
                getattr(cfg, "DOWNLOAD_COMMANDS_PYTHON", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_PYTHON_MIRROR", default_mirror),
                None,
            ),
            "git": (
                MessageGit,
                "url",
                getattr(cfg, "DOWNLOAD_COMMANDS_GIT", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_GIT_MIRROR", default_mirror),
                None,
            ),
            "java": (
                MessageJava,
                "url",
                getattr(cfg, "DOWNLOAD_COMMANDS_JAVA", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_JAVA_MIRROR", default_mirror),
                None,
            ),
            "mongodb": (
                MessageMongoDB,
                "url",
                getattr(cfg, "DOWNLOAD_COMMANDS_MONGODB", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_MONGODB_MIRROR", default_mirror),
                None,
            ),
            "nina": (
                MessageNINA,
                "git",
                getattr(cfg, "DOWNLOAD_COMMANDS_NINA", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_NINA_MIRROR", default_mirror),
                "--branch nina",
            ),
            "phd2": (
                MessagePHD2,
                "git",
                getattr(cfg, "DOWNLOAD_COMMANDS_PHD2", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_PHD2_MIRROR", default_mirror),
                "--branch phd2",
            ),
            "sharpcap": (
                MessageSharpCap,
                "git",
                getattr(cfg, "DOWNLOAD_COMMANDS_SHARPCAP", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_SHARPCAP_MIRROR", default_mirror),
                "--branch sharpcap",
            ),
            "lunarcore": (
                MessageLunarCore,
                "git",
                getattr(cfg, "DOWNLOAD_COMMANDS_LUNARCORE", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_LUNARCORE_MIRROR",
                        default_mirror),
                "--branch lunarcore",
            ),
            "lunarcoreres": (
                MessageLunarCoreRes,
                "git",
                getattr(cfg, "DOWNLOAD_COMMANDS_LUNARCORE_RES", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_LUNARCORE_RES_MIRROR",
                        default_mirror),
                "--branch lunarcoreres",
            ),
            "fiddler": (
                MessageFiddler,
                "git",
                getattr(cfg, "DOWNLOAD_COMMANDS_FIDDLER", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_FIDDLER_MIRROR", default_mirror),
                "--branch fiddler",
            ),
            "mitmdump": (
                MessageMitmdump,
                "git",
                getattr(cfg, "DOWNLOAD_COMMANDS_MITMDUMP", default_url),
                getattr(cfg, "DOWNLOAD_COMMANDS_MITMDUMP_MIRROR", default_mirror),
                "--branch mitmdump",
            ),
        }

    def generate_download_url(
        self,
        types: str,
        repo_url: str,
        mirror_url: Optional[str],
        mirror_branch: Optional[str] = None,
        is_add: bool = True,
    ) -> str:
        """生成下载URL"""
        from pathlib import Path

        from src.heal.models.config import cfg

        file = Path("temp") / Path(repo_url).name
        url_cfg = f"curl -o {file} -L "

        if types == "url":
            if cfg.chinaStatus.value and mirror_url:
                return f"{url_cfg}{mirror_url}"
            elif cfg.proxyStatus.value:
                url_cfg = f"curl -x http://127.0.0.1:7890 -o {file} -L "
            return f"{url_cfg}{repo_url}"

        git_cfg = "git clone --progress "
        if not is_add:
            if cfg.chinaStatus.value and mirror_url:
                branch = f" --branch {mirror_branch}" if mirror_branch else ""
                return f"{git_cfg}{branch} {mirror_url}"
            elif cfg.proxyStatus.value:
                git_cfg = "git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone --progress "
            return f"{git_cfg}{repo_url}"

        if cfg.chinaStatus.value:
            return ""
        elif cfg.proxyStatus.value:
            git_cfg = "git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone --progress "
        return f" && {git_cfg}{repo_url}"

    def handle_download(self, name: str) -> None:
        """处理下载请求"""
        mapping = self.download_mapping.get(name)
        if not mapping:
            self.logger.error(t("download.unknown_download_type", name=name))
            return

        message_class, types, repo_url, mirror_url, mirror_branch = mapping
        w = message_class(self.parent_widget)
        file_path = Path("temp") / Path(repo_url).name
        command = self.generate_download_url(
            types, repo_url, mirror_url, mirror_branch, is_add=False
        )

        self.download_started.emit(name, command)

        if w.exec():
            if not file_path.exists():
                self._execute_download(name, types, command, str(file_path))
            else:
                self._handle_existing_file(str(file_path))

    def _execute_download(self, name: str, types: str, command: str, file_path: str) -> None:
        """执行下载"""
        x = MessageDownload(self.parent_widget)
        x.show()
        x.start_download(types, command, file_path, False)

        if x.exec():
            self._show_success_message()
            self.download_completed.emit(name, True)
            self.logger.info(t("download.download_success", path=file_path))
        else:
            self._show_error_message()
            self.download_completed.emit(name, False)
            self.logger.error(t("download.download_failed", name=name))

    def _handle_existing_file(self, file_path: str) -> None:
        """处理已存在的文件"""
        self._show_file_exists_message()
        subprocess.Popen(["start", file_path], shell=True)
        self.file_exists.emit(file_path)
        self.logger.warning(t("download.file_exists_open", path=file_path))

    def _show_success_message(self) -> None:
        """显示成功消息"""
        InfoBar.success(
            title=t("download.success"),
            content="",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self.parent_widget,
        )

    def _show_error_message(self) -> None:
        """显示错误消息"""
        InfoBar.error(
            title=t("download.failed"),
            content="",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.parent_widget,
        )

    def _show_file_exists_message(self) -> None:
        """显示文件已存在消息"""
        InfoBar.error(
            title=t("download.file_exists"),
            content="",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.parent_widget,
        )

    def copy_to_clipboard(self, text: str) -> None:
        """复制到剪贴板"""
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(text)
        InfoBar.success(
            title=t("download.copied"),
            content=text,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self.parent_widget,
        )
        self.logger.info(t("download.copied_to_clipboard", text=text))
