"""
Environment Configuration Manager
Handles loading and management of environment configuration
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from PySide6.QtCore import QObject, Signal

from app.common.logging_config import get_logger
from app.common.json_utils import JsonUtils
from app.model.setting_card import SettingCard
from .environment_cards import HyperlinkCardEnvironment, PrimaryPushSettingCardDownload


class EnvironmentConfigManager(QObject):
    """环境配置管理器"""
    
    # 信号
    config_loaded = Signal(list)        # config_items
    config_load_failed = Signal(str)    # error_message
    card_created = Signal(str)          # card_title
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger('environment_config_manager', module='EnvironmentConfigManager')
        self.config_file = Path('config') / 'download.json'
        self.config_data: List[Dict[str, Any]] = []
    
    def load_download_config(self) -> List[SettingCard]:
        """加载下载配置 - 使用统一JSON工具"""
        cards = []

        # 使用统一的JSON加载工具
        result = JsonUtils.load_json_file(
            self.config_file,
            create_if_missing=False,
            default_content=[]
        )

        if not result.success:
            error_msg = f"加载配置文件失败: {result.error}"
            self.logger.error(error_msg)
            self.config_load_failed.emit(error_msg)
            return cards

        # 处理警告
        for warning in result.warnings:
            self.logger.warning(f"配置加载警告: {warning}")

        self.config_data = result.data

        # 确保数据是列表格式
        if not isinstance(self.config_data, list):
            error_msg = "配置数据格式错误，期望列表格式"
            self.logger.error(error_msg)
            self.config_load_failed.emit(error_msg)
            return cards

        # 创建卡片
        for item in self.config_data:
            try:
                card = self.create_card_from_config(item)
                if card:
                    cards.append(card)
                    self.card_created.emit(item.get('title', 'Unknown'))
                    self.logger.info(f"Loaded card from config: {item.get('title', 'Unknown')}")
            except Exception as e:
                self.logger.error(f"创建卡片失败: {e}")

        self.config_loaded.emit(self.config_data)
        return cards
    
    def create_card_from_config(self, item: Dict[str, Any]) -> SettingCard:
        """从配置创建卡片"""
        card_type = item.get('type')
        
        if card_type == 'link':
            return HyperlinkCardEnvironment(
                title=item['title'],
                content=item.get('content') or "",
                links=item.get('links')
            )
        elif card_type == 'download':
            return PrimaryPushSettingCardDownload(
                title=item['title'],
                content=item.get('content') or "",
                options=item.get('options')
            )
        else:
            error_msg = f"未知的卡片类型: {card_type}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def get_config_data(self) -> List[Dict[str, Any]]:
        """获取配置数据"""
        return self.config_data.copy()
    
    def save_config(self, config_data: List[Dict[str, Any]]) -> bool:
        """保存配置"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with self.config_file.open('w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.config_data = config_data
            self.logger.info("环境配置已保存")
            return True
            
        except Exception as e:
            error_msg = f"保存配置失败: {e}"
            self.logger.error(error_msg)
            self.config_load_failed.emit(error_msg)
            return False
    
    def add_config_item(self, item: Dict[str, Any]) -> bool:
        """添加配置项"""
        try:
            self.config_data.append(item)
            return self.save_config(self.config_data)
        except Exception as e:
            self.logger.error(f"添加配置项失败: {e}")
            return False
    
    def remove_config_item(self, title: str) -> bool:
        """移除配置项"""
        try:
            self.config_data = [item for item in self.config_data if item.get('title') != title]
            return self.save_config(self.config_data)
        except Exception as e:
            self.logger.error(f"移除配置项失败: {e}")
            return False
