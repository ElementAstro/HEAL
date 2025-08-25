"""
Module Configuration Manager
Handles loading, saving, and managing module configurations
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from src.heal.common.logging_config import get_logger
from .module_models import ModuleConfig


class ModuleConfigManager:
    """模块配置管理器"""

    def __init__(self) -> None:
        self.logger = get_logger("module_config_manager", module="ModuleConfigManager")
        self.module_configs: Dict[str, ModuleConfig] = {}
        self.config_path = Path("config/module_configs.json")

    def load_configurations(self) -> Dict[str, ModuleConfig]:
        """加载模块配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                for name, config in config_data.items():
                    self.module_configs[name] = ModuleConfig(**config)

                self.logger.info(f"已加载 {len(self.module_configs)} 个模块配置")
            else:
                self.logger.info("配置文件不存在，使用默认配置")

            return self.module_configs
        except Exception as e:
            self.logger.error(f"加载模块配置失败: {e}")
            return {}

    def save_configurations(self) -> bool:
        """保存模块配置"""
        try:
            self.config_path.parent.mkdir(exist_ok=True)

            config_data = {}
            for name, config in self.module_configs.items():
                config_data[name] = {
                    "name": config.name,
                    "enabled": config.enabled,
                    "auto_refresh": config.auto_refresh,
                    "refresh_interval": config.refresh_interval,
                    "max_retries": config.max_retries,
                    "timeout": config.timeout,
                    "validation_enabled": config.validation_enabled,
                    "performance_monitoring": config.performance_monitoring,
                    "custom_settings": config.custom_settings,
                }

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.logger.info("模块配置已保存")
            return True
        except Exception as e:
            self.logger.error(f"保存模块配置失败: {e}")
            return False

    def get_config(self, module_name: str) -> Optional[ModuleConfig]:
        """获取模块配置"""
        return self.module_configs.get(module_name)

    def update_config(self, module_name: str, config: ModuleConfig) -> bool:
        """更新模块配置"""
        try:
            self.module_configs[module_name] = config
            return self.save_configurations()
        except Exception as e:
            self.logger.error(f"更新模块配置失败: {e}")
            return False

    def add_config(self, config: ModuleConfig) -> bool:
        """添加新的模块配置"""
        return self.update_config(config.name, config)

    def remove_config(self, module_name: str) -> bool:
        """移除模块配置"""
        try:
            if module_name in self.module_configs:
                del self.module_configs[module_name]
                return self.save_configurations()
            return True
        except Exception as e:
            self.logger.error(f"移除模块配置失败: {e}")
            return False

    def get_all_configs(self) -> Dict[str, ModuleConfig]:
        """获取所有模块配置"""
        return self.module_configs.copy()

    def export_configs(self, filepath: str) -> bool:
        """导出模块配置"""
        try:
            data: Dict[str, Any] = {"timestamp": time.time(), "configs": {}}

            for name, config in self.module_configs.items():
                data["configs"][name] = {
                    "name": config.name,
                    "enabled": config.enabled,
                    "auto_refresh": config.auto_refresh,
                    "refresh_interval": config.refresh_interval,
                    "max_retries": config.max_retries,
                    "timeout": config.timeout,
                    "validation_enabled": config.validation_enabled,
                    "performance_monitoring": config.performance_monitoring,
                    "custom_settings": config.custom_settings,
                }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"模块配置已导出到: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"导出模块配置失败: {e}")
            return False
