"""
Font Manager
Handles font checking and installation
"""

import sys
import subprocess
import winreg
from PySide6.QtCore import QObject, Signal

from app.common.logging_config import get_logger
from app.model.config import cfg, Info


class FontManager(QObject):
    """字体管理器"""
    
    # 信号
    font_check_completed = Signal(bool)     # is_font_installed
    font_installation_started = Signal()
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.logger = get_logger('font_manager', module='FontManager')
    
    def check_font(self) -> bool:
        """检查字体是否已安装"""
        is_setup_font = False
        
        # 注册表路径
        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
            (winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows NT\CurrentVersion\Fonts")
        ]
        
        try:
            for hkey, sub_key in registry_keys:
                with winreg.ConnectRegistry(None, hkey) as reg:
                    with winreg.OpenKey(reg, sub_key) as reg_key:
                        i = 0
                        while True:
                            try:
                                name, _, _ = winreg.EnumValue(reg_key, i)
                                if cfg.APP_FONT.lower() in name.lower():
                                    is_setup_font = True
                                    break
                                i += 1
                            except OSError:
                                break
                    if is_setup_font:
                        break
        except Exception as e:
            error_msg = f'检查字体失败: {e}'
            self.logger.error(error_msg)
            Info(self.main_window, 'E', 3000, self.main_window.tr(error_msg))
            return False
        
        self.font_check_completed.emit(is_setup_font)
        
        if is_setup_font:
            self.logger.info(f"字体已安装: {cfg.APP_FONT}")
        else:
            self.logger.warning(f"字体未安装: {cfg.APP_FONT}")
            
        return is_setup_font
    
    def install_font(self) -> None:
        """安装字体"""
        try:
            # 启动字体安装程序
            subprocess.run('cd src/patch/font && start zh-cn.ttf', shell=True)
            self.font_installation_started.emit()
            self.logger.info("字体安装程序已启动")
            
            # 退出应用程序以重新加载字体
            sys.exit()
            
        except Exception as e:
            error_msg = f'字体安装失败: {e}'
            self.logger.error(error_msg)
            Info(self.main_window, 'E', 3000, self.main_window.tr(error_msg))
    
    def handle_font_check(self) -> None:
        """处理字体检查"""
        if not self.check_font():
            self.install_font()
