"""
Launcher Signal Manager
Handles signal connections and event management for launcher interface
"""

from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from app.common.logging_config import get_logger
from app.model.download_process import SubDownloadCMD
from app.model.config import open_file


class LauncherSignalManager(QObject):
    """启动器信号管理器"""
    
    # 信号
    download_started = Signal(str)      # download_key
    file_opened = Signal(str)           # file_path
    
    def __init__(self, parent_widget: Optional[QWidget] = None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger('launcher_signal_manager', module='LauncherSignalManager')
        
        # 初始化下载命令处理器
        self.sub_download_cmd = SubDownloadCMD(parent_widget)
    
    def connect_audio_download_signal(self, audio_download_card):
        """连接音频下载信号"""
        audio_download_card.clicked.connect(
            lambda: self.handle_download_started('audio')
        )
        self.logger.debug("音频下载信号已连接")
    
    def connect_config_signal(self, config_card):
        """连接配置文件信号"""
        config_card.clicked.connect(
            lambda: self.handle_file_open('config/config.json')
        )
        self.logger.debug("配置文件信号已连接")
    
    def handle_download_started(self, download_key: str):
        """处理下载开始"""
        self.sub_download_cmd.handleDownloadStarted(download_key)
        self.download_started.emit(download_key)
        self.logger.info(f"下载已开始: {download_key}")
    
    def handle_file_open(self, file_path: str):
        """处理文件打开"""
        open_file(self.parent_widget, file_path)
        self.file_opened.emit(file_path)
        self.logger.info(f"文件已打开: {file_path}")
