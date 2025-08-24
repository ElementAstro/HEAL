"""
Main Window Manager
Handles main window initialization, configuration and display
"""

import sys
from pathlib import Path
from PySide6.QtCore import QObject, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from qfluentwidgets import SplashScreen
from app.common.logging_config import get_logger
from app.model.config import cfg


class WindowManager(QObject):
    """主窗口管理器"""
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.logger = get_logger('window_manager', module='WindowManager')
        self.splash_screen = None
    
    def init_main_window(self) -> None:
        """初始化主窗口"""
        # 设置标题栏
        self.main_window.titleBar.maxBtn.setHidden(True)
        self.main_window.titleBar.maxBtn.setDisabled(True)
        self.main_window.titleBar.setDoubleClickEnabled(False)
        self.main_window.setResizeEnabled(False)
        self.main_window.setWindowFlags(
            self.main_window.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint
        )

        # 设置窗口属性
        self.main_window.setWindowTitle(cfg.APP_NAME)
        self.main_window.setFixedSize(1280, 768)
        self.main_window.setWindowIcon(QIcon('./src/image/icon.ico'))

        # 创建启动画面
        self.splash_screen = SplashScreen(self.main_window.windowIcon(), self.main_window)
        self.splash_screen.setIconSize(QSize(200, 200))
        self.splash_screen.raise_()

        # 居中显示
        self._center_window()

        # 显示窗口
        self.main_window.show()
        QApplication.processEvents()
        
        self.logger.info("主窗口已初始化")
    
    def _center_window(self):
        """居中显示窗口"""
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.main_window.move(
            w // 2 - self.main_window.width() // 2,
            h // 2 - self.main_window.height() // 2
        )
        self.logger.debug("窗口已居中")
    
    def finish_splash(self):
        """完成启动画面"""
        if self.splash_screen:
            self.splash_screen.finish()
            self.logger.debug("启动画面已完成")
    
    def toggle_window_visibility(self) -> None:
        """切换窗口可见性"""
        if self.main_window.isVisible():
            self.main_window.hide()
            self.logger.debug("窗口已隐藏")
        else:
            self.main_window.show()
            self.logger.debug("窗口已显示")
    
    def get_splash_screen(self):
        """获取启动画面"""
        return self.splash_screen
