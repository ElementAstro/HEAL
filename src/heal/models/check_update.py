import json
import os
from typing import Optional

import requests
from PySide6.QtCore import QThread, Signal

from ..common.logging_config import (
    get_logger,
    log_exception,
    log_network,
    log_performance,
)
from .config import cfg, get_json

# 使用统一日志配置
logger = get_logger("check_update")


def get_latest_version() -> Optional[str]:
    url = "https://api.github.com/repos/letheriver2007/Firefly-Launcher/releases/latest"
    headers = {"User-Agent": "Mozilla/5.0"}
    proxies = {}

    if cfg.chinaStatus.value:
        logger.debug("China status is enabled. No proxy will be used.")
    elif cfg.proxyStatus.value:
        proxies = {
            "http": f"http://127.0.0.1:{cfg.PROXY_PORT}",
            "https": f"https://127.0.0.1:{cfg.PROXY_PORT}",
        }
        logger.debug(f"Proxy is enabled: {proxies}")
    else:
        logger.debug("Proxies are not enabled.")

    try:
        logger.info(f"Fetching latest version from {url}")
        response = requests.get(url, headers=headers,
                                proxies=proxies, timeout=10)
        response.raise_for_status()
        release_info = response.json()
        latest_version = release_info.get("tag_name")
        if isinstance(latest_version, str):
            logger.info(f"Latest version fetched: {latest_version}")
            return latest_version
        else:
            logger.warning(
                "tag_name not found or not a string in release info")
            return None
    except requests.RequestException as e:
        logger.error(f"Error fetching latest version: {e}")
        return None


class UpdateThread(QThread):
    update_signal = Signal(int, str)

    def __init__(self) -> None:
        super().__init__()
        self.logger = logger.bind(thread="UpdateThread")
        self.logger.debug("UpdateThread initialized.")

    def run(self) -> None:
        self.logger.info("UpdateThread started.")
        if not os.path.exists("firefly-launcher.py"):
            self.logger.debug(
                "'firefly-launcher.py' does not exist. Proceeding with version check."
            )
            latest_version = get_latest_version()
            installed_version = get_json(
                "./config/version.json", "APP_VERSION")
            self.logger.debug(
                f"Installed version: {installed_version}, Latest version: {latest_version}"
            )

            if latest_version and installed_version:
                if latest_version > installed_version:
                    self.logger.info(
                        f"New version available: {latest_version}")
                    self.update_signal.emit(2, latest_version)
                elif latest_version == installed_version:
                    self.logger.info("Already on the latest version.")
                    self.update_signal.emit(1, latest_version)
                else:
                    self.logger.warning(
                        "Installed version is newer than the latest version available."
                    )
                    self.update_signal.emit(0, "Version information error")
            else:
                self.logger.error("Failed to retrieve version information.")
                self.update_signal.emit(0, "Network access error")
        else:
            self.logger.info("Development version detected.")
            self.update_signal.emit(0, "Current is Dev version")


def check_update() -> None:
    logger.info("Initiating update check.")
    check_thread = UpdateThread()
    check_thread.update_signal.connect(handle_update)
    check_thread.start()


def handle_update(status: int, message: str) -> None:
    if status == 2:
        logger.info(f"Update available: {message}")
        # Implement update logic here, e.g., prompt user to download
    elif status == 1:
        logger.info("No update needed. You are on the latest version.")
    else:
        logger.warning(f"Update check status: {message}")
        # Handle errors or Dev version accordingly
