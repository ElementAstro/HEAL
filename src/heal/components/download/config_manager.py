"""
Download Configuration Manager
Handles loading and managing download configuration from JSON
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from src.heal.common.exception_handler import ExceptionType, exception_handler
from src.heal.common.i18n import t
from src.heal.common.json_utils import JsonLoadResult, JsonUtils
from src.heal.common.logging_config import get_logger


class DownloadConfigManager(QObject):
    """下载配置管理器"""

    # 信号
    config_loaded = Signal(dict)  # interface_data
    config_load_failed = Signal(str)  # error_message

    def __init__(self, parent_widget: QWidget) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger(
            "download_config_manager", module="DownloadConfigManager"
        )

        self.interface_data: Dict[str, Any] = {}
        self.config_path = Path("./config/interface/download.json")

    @exception_handler(exc_type=ExceptionType.DOWNLOAD_ERROR)
    def load_configuration(self) -> bool:
        """从JSON文件加载界面配置 - 使用统一JSON工具"""
        # 使用统一的JSON加载工具
        result = JsonUtils.load_json_file(
            self.config_path, create_if_missing=False, default_content={}
        )

        if not result.success:
            error_msg = t("download.config_not_found", path=str(self.config_path))
            self.logger.error(f"配置加载失败: {result.error}")
            self._show_error_dialog(t("common.error"), error_msg)
            self.config_load_failed.emit(error_msg)
            return False

        # 处理警告
        for warning in result.warnings:
            self.logger.warning(f"配置加载警告: {warning}")

        self.interface_data = result.data

        self.logger.debug(
            t(
                "download.json_loaded",
                filename=self.config_path.name,
                data=str(self.interface_data),
            )
        )

        # 验证配置数据
        if self._validate_config():
            self.config_loaded.emit(self.interface_data)
            return True
        else:
            error_msg = t("download.invalid_config")
            self.config_load_failed.emit(error_msg)
            return False

    def _validate_config(self) -> bool:
        """验证配置数据"""
        if not isinstance(self.interface_data, dict):
            self.logger.error("配置数据不是有效的字典格式")
            return False

        if "sections" not in self.interface_data:
            self.logger.error("配置数据中缺少 'sections' 字段")
            return False

        sections = self.interface_data["sections"]
        if not isinstance(sections, list):
            self.logger.error("'sections' 字段不是列表格式")
            return False

        for i, section in enumerate(sections):
            if not isinstance(section, dict):
                self.logger.error(f"第 {i} 个 section 不是字典格式")
                return False

            if "title" not in section:
                self.logger.warning(f"第 {i} 个 section 缺少 'title' 字段")

            if "items" not in section:
                self.logger.warning(f"第 {i} 个 section 缺少 'items' 字段")

        return True

    def _show_error_dialog(self, title: str, message: str) -> None:
        """显示错误对话框"""
        QMessageBox.critical(self.parent_widget, title, message)

    def get_sections(self) -> List[Dict[str, Any]]:
        """获取所有部分"""
        return self.interface_data.get("sections", [])

    def get_section(self, index: int) -> Dict[str, Any]:
        """获取指定索引的部分"""
        sections = self.get_sections()
        if 0 <= index < len(sections):
            return sections[index]
        return {}

    def get_section_by_title(self, title: str) -> Dict[str, Any]:
        """根据标题获取部分"""
        for section in self.get_sections():
            if section.get("title") == title:
                return section
        return {}

    def reload_configuration(self) -> bool:
        """重新加载配置"""
        self.logger.info("重新加载下载配置")
        return self.load_configuration()

    def get_interface_data(self) -> Dict[str, Any]:
        """获取完整的接口数据"""
        return self.interface_data.copy()

    def save_configuration(self, data: Dict[str, Any]) -> bool:
        """保存配置数据"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with self.config_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.interface_data = data
            self.logger.info("下载配置已保存")
            return True

        except Exception as e:
            error_msg = f"保存配置失败: {str(e)}"
            self.logger.error(error_msg)
            self.config_load_failed.emit(error_msg)
            return False
