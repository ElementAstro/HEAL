"""
Theme Manager
Handles theme switching and configuration
"""

from PySide6.QtCore import QObject, Signal
from qfluentwidgets import Theme, setTheme

from src.heal.common.logging_config import get_logger
from src.heal.models.config import cfg


class ThemeManager(QObject):
    """主题管理器"""

    # 信号
    theme_changed = Signal(Theme)

    def __init__(self, main_window) -> None:
        super().__init__(main_window)
        self.main_window = main_window
        self.logger = get_logger("theme_manager", module="ThemeManager")

    def init_theme(self) -> None:
        """初始化主题"""
        setTheme(cfg.themeMode.value)
        self.logger.info(f"主题已初始化: {cfg.themeMode.value}")

    def toggle_theme(self) -> None:
        """切换主题"""
        current_theme = cfg.themeMode.value
        new_theme = Theme.LIGHT if current_theme == Theme.DARK else Theme.DARK

        setTheme(new_theme)
        cfg.themeMode.value = new_theme
        cfg.save()

        self.theme_changed.emit(new_theme)
        self.logger.info(f"主题已切换: {current_theme} -> {new_theme}")

    def set_theme(self, theme: Theme) -> None:
        """设置指定主题"""
        setTheme(theme)
        cfg.themeMode.value = theme
        cfg.save()

        self.theme_changed.emit(theme)
        self.logger.info(f"主题已设置: {theme}")

    def get_current_theme(self) -> Theme:
        """获取当前主题"""
        return cfg.themeMode.value
