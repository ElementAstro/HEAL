"""
Audio Manager
Handles media playback and audio functionality
"""

import random
from pathlib import Path
from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import QWidget

from qfluentwidgets import InfoBar, InfoBarIcon, InfoBarPosition, PrimaryPushButton
from PySide6.QtCore import Qt

from app.common.logging_config import get_logger


class AudioManager(QObject):
    """音频管理器"""
    
    # 信号
    audio_played = Signal(str)          # status
    audio_error = Signal(str)           # error_message
    download_requested = Signal()       # 请求跳转到下载页面
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.logger = get_logger('audio_manager', module='AudioManager')
        
        # 音频播放器
        self.player = None
        self.audio_output = None
    
    def play_audio(self, status: str) -> None:
        """播放音频"""
        audio_path = Path('src/audio') / status
        
        if not audio_path.exists():
            self.logger.warning(f"音频目录不存在: {audio_path}")
            self._show_audio_error()
            return
        
        audio_files = list(audio_path.glob('*.wav'))
        if not audio_files:
            self.logger.warning(f"音频目录中没有音频文件: {audio_path}")
            self._show_audio_error()
            return
        
        try:
            # 初始化播放器
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            self.audio_output.setVolume(1)
            
            # 随机选择音频文件
            selected_audio = random.choice(audio_files)
            audio_url = QUrl.fromLocalFile(str(selected_audio))
            
            self.player.setSource(audio_url)
            self.player.play()
            
            self.audio_played.emit(status)
            self.logger.info(f"音频播放: {selected_audio.name}")
            
        except Exception as e:
            self.logger.error(f"音频播放失败: {e}")
            self.audio_error.emit(str(e))
            self._show_audio_error()
    
    def _show_audio_error(self) -> None:
        """显示音频错误信息"""
        file_error = InfoBar(
            icon=InfoBarIcon.ERROR,
            title=self.main_window.tr('未找到语音!'),
            content='',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.main_window
        )
        
        file_error_button = PrimaryPushButton(self.main_window.tr('前往下载'))
        file_error_button.clicked.connect(self._handle_download_request)
        file_error.addWidget(file_error_button)
        file_error.show()
        
        self.logger.warning("音频错误信息已显示")
    
    def _handle_download_request(self):
        """处理下载请求"""
        # 切换到下载页面（索引1）
        if hasattr(self.main_window, 'stackedWidget'):
            self.main_window.stackedWidget.setCurrentIndex(1)
        
        self.download_requested.emit()
        self.logger.info("请求切换到下载页面")
    
    def stop_audio(self):
        """停止音频播放"""
        if self.player:
            self.player.stop()
            self.logger.debug("音频播放已停止")
    
    def set_volume(self, volume: float):
        """设置音量 (0.0 - 1.0)"""
        if self.audio_output:
            self.audio_output.setVolume(volume)
            self.logger.debug(f"音量已设置: {volume}")
    
    def cleanup(self):
        """清理资源"""
        if self.player:
            self.player.stop()
            self.player = None
        if self.audio_output:
            self.audio_output = None
        self.logger.debug("音频资源已清理")
