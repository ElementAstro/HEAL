import os
import json
import requests
from typing import Optional
from PySide6.QtCore import QThread, Signal
from app.model.config import cfg, get_json


def get_latest_version() -> Optional[str]:
    url = 'https://api.github.com/repos/letheriver2007/Firefly-Launcher/releases/latest'
    headers = {'User-Agent': 'Mozilla/5.0'}
    proxies = {}

    if cfg.chinaStatus.value:
        proxies = {}
    elif cfg.proxyStatus.value:
        proxies = {
            'http': f'http://127.0.0.1:{cfg.PROXY_PORT}',
            'https': f'https://127.0.0.1:{cfg.PROXY_PORT}'
        }

    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        response.raise_for_status()
        release_info = response.json()
        return release_info.get('tag_name')
    except requests.RequestException as e:
        print(f"Error fetching latest version: {e}")
        return None


def checkUpdate(self):
    self.check_thread = UpdateThread()
    self.check_thread.update_signal.connect(self.handleUpdate)
    self.check_thread.start()


class UpdateThread(QThread):
    update_signal = Signal(int, str)

    def __init__(self):
        super().__init__()

    def run(self) -> None:
        if not os.path.exists('firefly-launcher.py'):
            latest_version = get_latest_version()
            installed_version = get_json(
                './config/version.json', 'APP_VERSION')
            if latest_version and installed_version:
                if latest_version > installed_version:
                    self.update_signal.emit(2, str(latest_version))
                elif latest_version == installed_version:
                    self.update_signal.emit(1, str(latest_version))
                else:
                    self.update_signal.emit(0, self.tr('版本信息错误'))
            else:
                self.update_signal.emit(0, self.tr('网络访问错误'))
        else:
            self.update_signal.emit(0, self.tr('当前为Dev版本'))
