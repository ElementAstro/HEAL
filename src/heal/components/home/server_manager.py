import os
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QButtonGroup, QWidget
from qfluentwidgets import FluentIcon, TogglePushButton, setCustomStyleSheet

from ...resources.icons.astro import AstroIcon

from ...common.exception_handler import ExceptionHandler
from ...models.config import cfg
from ...models.process_manager import ProcessManager
from .server_button import ServerButton

# 定义常量避免重复
BUTTON_BORDER_RADIUS_STYLE = "PushButton{border-radius: 12px}"


class ServerManager:
    """Manages server buttons and their operations."""

    def __init__(self, parent_widget: QWidget) -> None:
        self.parent = parent_widget
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(False)
        self.launched_servers: List[str] = []
        self.process_manager = ProcessManager()
        self.exception_handler = ExceptionHandler()

    def create_server_buttons(self) -> List[ServerButton]:
        """创建服务器按钮"""
        buttons = []
        for name, details in cfg.SERVER.items():
            icon = self._get_server_icon(details)

            button_server = ServerButton(parent=self.parent)
            button_server.setIcon(icon)
            button_server.setText("   " + name)
            button_server.setObjectName(name)
            button_server.setFixedSize(270, 70)
            button_server.setIconSize(QSize(24, 24))
            button_server.setFont(QFont(f"{cfg.APP_FONT}", 12))
            setCustomStyleSheet(
                button_server, BUTTON_BORDER_RADIUS_STYLE, BUTTON_BORDER_RADIUS_STYLE
            )

            self.button_group.addButton(button_server)
            buttons.append(button_server)

        return buttons

    def _get_server_icon(self, details: Dict[str, Any]) -> Any:
        """获取服务器图标"""
        icon = FluentIcon.TAG
        # 修复：合并if语句
        if "ICON" in details and details["ICON"] and "ICON_TYPE" in details:
            icon_type = details["ICON_TYPE"]
            if icon_type == "PATH":
                icon = details["ICON"]
            elif icon_type == "FLUENT":
                icon = getattr(FluentIcon, details["ICON"], FluentIcon.TAG)
            elif icon_type == "ASTRO":
                icon = getattr(AstroIcon, details["ICON"], FluentIcon.TAG)
            # 移除空的 else 块，提供默认处理
        elif (
            "ICON" in details and details["ICON"]
        ):  # 处理只有 ICON 没有 ICON_TYPE 的情况
            icon = details["ICON"]
        return icon

    def get_selected_servers(self) -> List[TogglePushButton]:
        """获取选中的服务器按钮"""
        return [
            button
            for button in self.button_group.buttons()
            if isinstance(button, TogglePushButton) and button.isChecked()
        ]

    def should_launch_server(self, server: TogglePushButton) -> bool:
        """检查是否应该启动服务器"""
        return server.objectName() not in self.launched_servers

    def launch_single_server(self, server: TogglePushButton) -> bool:
        """启动单个服务器"""
        name = server.objectName()
        server_path = f"./server/{name}"

        if not os.path.exists(server_path):
            return False

        try:
            # 修复：使用这些变量，即使只是日志记录
            server_config = cfg.SERVER[name]
            command = server_config.get("COMMAND", "")
            working_dir = server_path

            # 记录启动信息
            print(
                f"Starting server {name} with command: {command} in directory: {working_dir}"
            )

            success = self.process_manager.start_process(
                name
            )  # Assuming start_process only takes process name

            if not success:
                self._handle_server_start_failure(server, name)
                return False

            return True

        except Exception as e:
            self._handle_server_start_exception(server, name, e)
            return False

    def _handle_server_start_failure(self, server: TogglePushButton, name: str) -> None:
        """处理服务器启动失败"""
        self.exception_handler.handle_known_exception(
            RuntimeError(f"Failed to start server {name}"),
            exc_type="process_error",
            severity="medium",
            user_message=f"无法启动服务器 {name}",
            parent_widget=self.parent,
        )
        server.setChecked(False)

    def _handle_server_start_exception(
        self, server: TogglePushButton, name: str, exception: Exception
    ) -> None:
        """处理服务器启动异常"""
        self.exception_handler.handle_known_exception(
            exception,
            exc_type="process_error",
            severity="medium",
            user_message=f"启动服务器 {name} 时发生错误",
            parent_widget=self.parent,
        )
        server.setChecked(False)

    def stop_server(self, server_name: str) -> None:
        """Stop a specific server using ProcessManager"""
        try:
            self.process_manager.stop_process(server_name)
        except Exception as e:
            self.exception_handler.handle_known_exception(
                e,
                exc_type="process_error",
                severity="medium",
                user_message=f"停止服务器 {server_name} 时发生错误",
                parent_widget=self.parent,
            )

    def stop_all_servers(self) -> None:
        """停止所有已启动的服务器"""
        for server_name in list(self.launched_servers):  # Iterate over a copy
            self.process_manager.stop_process(server_name)

    def restart_server(self, server_name: str) -> None:
        """Restart a server using ProcessManager"""
        try:
            self.process_manager.restart_process(server_name)
        except Exception as e:
            self.exception_handler.handle_known_exception(
                e,
                exc_type="process_error",
                severity="medium",
                user_message=f"重启服务器 {server_name} 时发生错误",
                parent_widget=self.parent,
            )

    def update_button_state(self, process_name: str, state: str) -> None:
        """更新按钮状态"""
        for button_widget in self.button_group.buttons():
            if button_widget.objectName() == process_name:
                if state == "started":
                    button_widget.setChecked(True)
                    button_widget.setStyleSheet(
                        "background-color: #4CAF50; color: white;"
                    )
                elif state == "stopped":
                    button_widget.setChecked(False)
                    button_widget.setStyleSheet("")
                elif state == "crashed":
                    button_widget.setStyleSheet(
                        "background-color: #F44336; color: white;"
                    )
                break
