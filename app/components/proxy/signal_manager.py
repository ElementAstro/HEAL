"""
Proxy Signal Manager
Handles signal connections and event management for proxy interface
"""

from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from app.common.logging_config import get_logger
from app.model.download_process import SubDownloadCMD
from .fiddler_manager import FiddlerManager, ProxyManager
from .proxy_cards import PrimaryPushSettingCardFiddler


class ProxySignalManager(QObject):
    """代理信号管理器"""
    
    # 信号
    download_started = Signal(str)      # download_key
    
    def __init__(self, parent_widget: Optional[QWidget] = None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger('proxy_signal_manager', module='ProxySignalManager')
        
        # 初始化管理器
        self.fiddler_manager = FiddlerManager(parent_widget)
        self.proxy_manager = ProxyManager(parent_widget)
        self.sub_download_cmd = SubDownloadCMD(parent_widget)
    
    def connect_download_signals(self, download_card):
        """连接下载信号"""
        download_card.clicked.connect(
            lambda: self.handle_download_started('fiddler')
        )
        self.logger.debug("下载信号已连接")
    
    def connect_fiddler_signals(self, fiddler_card: PrimaryPushSettingCardFiddler):
        """连接Fiddler卡片信号"""
        fiddler_card.clicked_script.connect(
            lambda: self.fiddler_manager.show_fiddler_tip(fiddler_card.button_script)
        )
        fiddler_card.clicked_old.connect(self.fiddler_manager.open_fiddler)
        fiddler_card.clicked_backup.connect(self.fiddler_manager.backup_fiddler_script)
        
        self.logger.debug("Fiddler信号已连接")
    
    def connect_proxy_signals(self, proxy_card):
        """连接代理重置信号"""
        proxy_card.clicked.connect(self.proxy_manager.reset_proxy)
        self.logger.debug("代理重置信号已连接")
    
    def handle_download_started(self, download_key: str):
        """处理下载开始"""
        self.sub_download_cmd.handleDownloadStarted(download_key)
        self.download_started.emit(download_key)
        self.logger.info(f"下载已开始: {download_key}")
    
    def get_fiddler_manager(self) -> FiddlerManager:
        """获取Fiddler管理器"""
        return self.fiddler_manager
    
    def get_proxy_manager(self) -> ProxyManager:
        """获取代理管理器"""
        return self.proxy_manager
