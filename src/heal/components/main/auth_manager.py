"""
Authentication Manager
Handles login functionality and password validation
"""

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from src.heal.common.logging_config import get_logger
from src.heal.models.config import Info, cfg


class AuthenticationManager(QObject):
    """认证管理器"""

    # 信号
    login_success = Signal()
    login_failed = Signal(int)  # attempt_count

    def __init__(self, main_window: QWidget) -> None:
        super().__init__(main_window)
        self.main_window = main_window
        self.logger = get_logger(
            "authentication_manager", module="AuthenticationManager"
        )
        self.attempt_count = 1
        self.login_card: Any = None

    def init_login(self) -> bool:
        """初始化登录"""
        if cfg.useLogin.value:
            from src.heal.models.login_card import MessageLogin

            self.login_card = MessageLogin()
            self.login_card.show()
            self.login_card.passwordEntered.connect(self.handle_login)
            self.logger.info("登录界面已显示")
            return True
        return False

    def handle_login(self, pwd: str) -> bool:
        """处理登录"""
        try:
            config_path = Path("config/config.json")
            with config_path.open("r", encoding="utf-8") as file:
                config = json.load(file)

            local_pwd = config.get("PASSWORD", "")

            if local_pwd == pwd:
                Info(self.main_window, "S", 1000, self.main_window.tr("登录成功!"))
                self.logger.info("登录成功")

                if self.login_card:
                    self.login_card.close()

                self.login_success.emit()
                return True
            else:
                Info(
                    self.main_window,
                    "E",
                    3000,
                    f"{self.main_window.tr('密码错误!')} {self.main_window.tr('次数: ')}{self.attempt_count}",
                )
                self.logger.warning(f"登录失败，尝试次数: {self.attempt_count}")
                self.attempt_count += 1
                self.login_failed.emit(self.attempt_count)
                return False

        except Exception as e:
            self.logger.error(f"登录处理失败: {e}")
            Info(self.main_window, "E", 3000, f"登录处理失败: {e}")
            return False

    def close_login(self) -> None:
        """关闭登录界面"""
        if self.login_card:
            self.login_card.close()
            self.logger.debug("登录界面已关闭")
