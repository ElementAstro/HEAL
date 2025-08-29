from enum import Enum
from typing import Any

from qfluentwidgets import StyleSheetBase, Theme, qconfig

from ..common.logging_config import get_logger
from ..resources import resource_manager

# 使用统一日志配置
logger = get_logger("style_sheet")


class StyleSheet(StyleSheetBase, Enum):
    LINK_CARD = "link_card"
    SAMPLE_CARD = "sample_card"
    HOME_INTERFACE = "home_interface"
    ICON_INTERFACE = "icon_interface"
    VIEW_INTERFACE = "view_interface"
    SETTING_INTERFACE = "setting_interface"
    GALLERY_INTERFACE = "gallery_interface"
    NAVIGATION_VIEW_INTERFACE = "navigation_view_interface"
    LOG_INTERFACE = "log_interface"
    ENVIRONMENT_INTERFACE = "environment_interface"

    def path(self, theme: Theme = Theme.AUTO) -> str:
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return resource_manager.load_stylesheet(
            f"{theme.value.lower()}/{self.value}.qss"
        )
