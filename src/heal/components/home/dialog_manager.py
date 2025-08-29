import os
from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDialog, QFormLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import (
    InfoBar,
    InfoBarIcon,
    InfoBarPosition,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    TextEdit,
)

from ...models.config import Info


class DialogManager:
    """Manages dialogs for logs, configuration, and error messages."""

    def __init__(self, parent_widget: QWidget) -> None:
        self.parent = parent_widget
        self.config_fields: Dict[str, LineEdit] = {}

    def show_log_dialog(self, server_name: str) -> None:
        """显示服务器日志对话框 - 现在使用统一日志面板"""
        try:
            # 尝试使用统一日志面板
            from ..logging import show_server_log

            show_server_log(server_name)
        except ImportError:
            # 如果统一日志面板不可用，回退到传统对话框
            self._show_legacy_log_dialog(server_name)

    def _show_legacy_log_dialog(self, server_name: str) -> None:
        """显示传统的日志对话框（备用方案）"""
        log_dialog = QDialog(self.parent)
        log_dialog.setWindowTitle(f"{server_name} 日志")
        log_layout = QVBoxLayout(log_dialog)
        log_text = TextEdit(log_dialog)
        log_text.setReadOnly(True)
        log_text.setText(self.read_log(server_name))
        log_layout.addWidget(log_text)
        log_dialog.setLayout(log_layout)
        log_dialog.exec()

    def read_log(self, server_name: str) -> str:
        """读取服务器日志文件"""
        log_path = f"./logs/{server_name}.log"
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as file:
                    return file.read()
            except Exception as e:
                return f"读取日志文件失败: {str(e)}"
        else:
            return "日志文件不存在"

    def show_config_dialog(self, server_name: str) -> None:
        """显示服务器配置对话框"""
        config_dialog = QDialog(self.parent)
        config_dialog.setWindowTitle(f"{server_name} 配置")
        config_layout = QVBoxLayout(config_dialog)

        form_layout = QFormLayout()
        config_path = f"./config/{server_name}.cfg"
        # Note: config_fields already defined in __init__, reusing it here

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    lines = file.readlines()
                    for line in lines:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            line_edit = LineEdit(value)
                            self.config_fields[key] = line_edit
                            form_layout.addRow(QLabel(key), line_edit)
            except Exception as e:
                Info(self.parent, "E", 3000, f"读取配置文件失败: {e}")
        else:
            Info(self.parent, "W", 3000, f"配置文件 {config_path} 不存在")

        save_button = PushButton("保存")
        save_button.clicked.connect(
            lambda: self.save_config(server_name, config_path, config_dialog)
        )

        config_layout.addLayout(form_layout)
        config_layout.addWidget(save_button)
        config_dialog.setLayout(config_layout)
        config_dialog.exec()

    def save_config(self, server_name: str, config_path: str, dialog_to_close: QDialog) -> None:
        """保存服务器配置"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as file:
                for key, line_edit in self.config_fields.items():
                    file.write(f"{key}={line_edit.text()}\n")
            Info(self.parent, "S", 1000, f"{server_name} 配置已保存!")
            if dialog_to_close:
                dialog_to_close.accept()
        except Exception as e:
            Info(self.parent, "E", 3000, f"保存配置失败: {e}")

    def show_error_info_bar(self, name: str, parent_stackedwidget: QStackedWidget | None = None) -> None:
        """显示错误信息栏"""
        server_error = InfoBar(
            icon=InfoBarIcon.ERROR,
            title=f"找不到服务端{name}!",
            content="",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.parent,
        )

        server_page = {"LunarCore": 3}  # Example, adjust as needed
        # 修复：添加完整的类型检查
        if (
            name in server_page
            and parent_stackedwidget is not None
            and hasattr(parent_stackedwidget, "setCurrentIndex")
        ):

            page_index = server_page[name]
            server_error_button = PrimaryPushButton("前往下载")
            server_error_button.clicked.connect(
                lambda: (
                    parent_stackedwidget.setCurrentIndex(page_index)
                    if parent_stackedwidget
                    else None
                )
            )
            server_error.addWidget(server_error_button)

        server_error.show()
