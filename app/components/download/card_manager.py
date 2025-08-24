"""
Download Card Manager
Handles creation and management of download cards
"""

from typing import Dict, List, Any
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon as FIF, HyperlinkCard, PrimaryPushSettingCard

from app.common.logging_config import get_logger
from app.common.i18n import t
from app.common.exception_handler import exception_handler, ExceptionType
from src.icon.astro import AstroIcon
from app.model.setting_card import SettingCardGroup


class DownloadCardManager:
    """下载卡片管理器"""
    
    def __init__(self):
        self.logger = get_logger('download_card_manager', module='DownloadCardManager')
    
    @exception_handler(exc_type=ExceptionType.UNKNOWN_ERROR, user_message="Failed to create download card")
    def add_items_to_section(self, section_interface: SettingCardGroup, items: List[Dict[str, Any]]):
        """向部分添加项目"""
        for item in items:
            item_type = item.get('type')
            if not item_type:
                self.logger.warning(t('download.missing_item_type'))
                continue

            required_fields = {
                'hyperlink': ['url', 'text', 'icon', 'title', 'content'],
                'primary_push_setting': ['text', 'icon', 'title', 'content']
            }.get(item_type)

            if not required_fields or not all(field in item for field in required_fields):
                self.logger.error(t('download.missing_required_fields', item_type=item_type))
                continue

            item['icon'] = self.resolve_icon(item['icon'])
            try:
                card = self.create_card(item_type, item, required_fields)
                section_interface.addSettingCard(card)
                self.logger.debug(t('download.card_added', title=item.get("title", t('download.untitled'))))
            except ValueError as e:
                self.logger.error(t('download.card_creation_failed', error=str(e)))

    def resolve_icon(self, icon_name: str) -> Any:
        """解析图标"""
        if icon_name.startswith('FIF.'):
            return getattr(FIF, icon_name[4:], FIF.DOWNLOAD)
        elif icon_name.startswith('Astro.'):
            return getattr(AstroIcon, icon_name[6:], FIF.DOWNLOAD)
        self.logger.error(t('download.unknown_icon', icon=icon_name))
        return FIF.DOWNLOAD

    def create_card(self, item_type: str, item: Dict[str, Any], required_fields: List[str]) -> QWidget:
        """创建卡片"""
        card_args = {field: item[field] for field in required_fields}
        if item_type == 'hyperlink':
            return HyperlinkCard(**card_args)
        elif item_type == 'primary_push_setting':
            return PrimaryPushSettingCard(**card_args)
        raise ValueError(t('download.unknown_item_type', item_type=item_type))

    def create_section_cards(self, parent_widget: QWidget, sections: List[Dict[str, Any]]) -> List[SettingCardGroup]:
        """创建所有部分的卡片"""
        section_widgets = []
        
        for section in sections:
            section_widget = SettingCardGroup(parent_widget)
            self.add_items_to_section(section_widget, section.get('items', []))
            section_widgets.append(section_widget)
            
        return section_widgets
