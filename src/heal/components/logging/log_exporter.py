"""
日志导出器组件

提供日志导出功能：
- 导出为文本文件
- 导出为CSV格式
- 导出为JSON格式
- 按条件过滤导出
- 压缩导出
"""

import csv
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    CheckBox,
    ComboBox,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PushButton,
    TitleLabel,
)

from src.heal.common.logging_config import get_logger

logger = get_logger(__name__)


class LogExportWorker(QThread):
    """日志导出工作线程"""

    progress_updated = Signal(int)  # 进度更新
    export_completed = Signal(str)  # 导出完成，返回文件路径
    export_failed = Signal(str)  # 导出失败，返回错误信息

    def __init__(self, export_config: Dict) -> None:
        super().__init__()
        self.config = export_config

    def run(self) -> None:
        """执行导出任务"""
        try:
            output_path = self._export_logs()
            self.export_completed.emit(output_path)
        except Exception as e:
            self.export_failed.emit(str(e))

    def _export_logs(self) -> str:
        """执行日志导出"""
        source_files = self.config["source_files"]
        output_path = self.config["output_path"]
        export_format = self.config["format"]
        filters = self.config.get("filters", {})
        compress = self.config.get("compress", False)

        # 读取和过滤日志
        all_logs = []
        total_files = len(source_files)

        for i, file_path in enumerate(source_files):
            self.progress_updated.emit(int((i / total_files) * 50))  # 前50%用于读取

            if Path(file_path).exists():
                logs = self._read_and_filter_logs(file_path, filters)
                all_logs.extend(logs)

        # 导出日志
        if export_format == "txt":
            final_path = self._export_as_text(all_logs, output_path)
        elif export_format == "csv":
            final_path = self._export_as_csv(all_logs, output_path)
        elif export_format == "json":
            final_path = self._export_as_json(all_logs, output_path)
        else:
            raise ValueError(f"不支持的导出格式: {export_format}")

        self.progress_updated.emit(90)

        # 压缩文件
        if compress:
            final_path = self._compress_file(final_path)

        self.progress_updated.emit(100)
        return final_path

    def _read_and_filter_logs(self, file_path: str, filters: Dict) -> List[Dict]:
        """读取并过滤日志"""
        logs = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    # 解析日志行
                    log_entry = self._parse_log_line(line, line_num)

                    # 应用过滤条件
                    if self._matches_filters(log_entry, filters):
                        logs.append(log_entry)

        except Exception as e:
            logger.error(f"读取日志文件 {file_path} 失败: {e}")

        return logs

    def _parse_log_line(self, line: str, line_num: int) -> Dict:
        """解析日志行"""
        # 简单的日志解析，可以根据实际格式调整
        import re

        # 匹配时间戳
        timestamp_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})"
        timestamp_match = re.search(timestamp_pattern, line)
        timestamp = timestamp_match.group(1) if timestamp_match else ""

        # 匹配日志级别
        level_pattern = r"\|\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\|"
        level_match = re.search(level_pattern, line)
        level = level_match.group(1) if level_match else "INFO"

        # 匹配模块信息
        module_pattern = (
            r"\|\s*([a-zA-Z_][a-zA-Z0-9_.]*):([a-zA-Z_][a-zA-Z0-9_]*):(\d+)\s*\|"
        )
        module_match = re.search(module_pattern, line)
        module = module_match.group(1) if module_match else ""
        function = module_match.group(2) if module_match else ""
        line_no = module_match.group(3) if module_match else ""

        # 提取消息内容
        message_parts = line.split("|")
        message = message_parts[-1].strip() if len(message_parts) > 1 else line

        return {
            "timestamp": timestamp,
            "level": level,
            "module": module,
            "function": function,
            "line_number": line_no,
            "message": message,
            "raw_line": line,
            "file_line_number": line_num,
        }

    def _matches_filters(self, log_entry: Dict, filters: Dict) -> bool:
        """检查日志条目是否匹配过滤条件"""
        # 日志级别过滤
        if filters.get("levels") and log_entry["level"] not in filters["levels"]:
            return False

        # 模块过滤
        if filters.get("modules") and log_entry["module"] not in filters["modules"]:
            return False

        # 关键词过滤
        keywords = filters.get("keywords", "")
        if keywords:
            case_sensitive = filters.get("case_sensitive", False)
            text_to_search = log_entry["message"]

            if not case_sensitive:
                keywords = keywords.lower()
                text_to_search = text_to_search.lower()

            if keywords not in text_to_search:
                return False

        # 时间范围过滤
        start_time = filters.get("start_time")
        end_time = filters.get("end_time")
        if start_time or end_time:
            try:
                log_time = datetime.strptime(
                    log_entry["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
                )
                if start_time and log_time < start_time:
                    return False
                if end_time and log_time > end_time:
                    return False
            except ValueError:
                # 时间解析失败，跳过时间过滤
                pass

        return True

    def _export_as_text(self, logs: List[Dict], output_path: str) -> str:
        """导出为文本格式"""
        with open(output_path, "w", encoding="utf-8") as f:
            for log in logs:
                f.write(log["raw_line"] + "\n")
        return output_path

    def _export_as_csv(self, logs: List[Dict], output_path: str) -> str:
        """导出为CSV格式"""
        if not output_path.endswith(".csv"):
            output_path += ".csv"

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if logs:
                fieldnames = [
                    "timestamp",
                    "level",
                    "module",
                    "function",
                    "line_number",
                    "message",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for log in logs:
                    writer.writerow({k: log.get(k, "") for k in fieldnames})

        return output_path

    def _export_as_json(self, logs: List[Dict], output_path: str) -> str:
        """导出为JSON格式"""
        if not output_path.endswith(".json"):
            output_path += ".json"

        export_data = {
            "export_time": datetime.now().isoformat(),
            "total_logs": len(logs),
            "logs": logs,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        return output_path

    def _compress_file(self, file_path: str) -> str:
        """压缩文件"""
        zip_path = file_path + ".zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, Path(file_path).name)

        # 删除原文件
        os.remove(file_path)

        return zip_path


class LogExporter(CardWidget):
    """日志导出器组件"""

    export_requested = Signal(dict)  # 导出请求信号

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("LogExporter")

        # 导出配置
        self.export_config = {
            "source_files": [],
            "output_path": "",
            "format": "txt",
            "filters": {},
            "compress": False,
        }

        # 工作线程
        self.export_worker: Any = None

        # 设置界面
        self._setup_ui()
        self._setup_connections()

        logger.info("日志导出器初始化完成")

    def _setup_ui(self) -> None:
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = TitleLabel("日志导出")
        layout.addWidget(title)

        # 导出格式选择
        self._create_format_selection(layout)

        # 输出路径选择
        self._create_output_selection(layout)

        # 导出选项
        self._create_export_options(layout)

        # 进度显示
        self._create_progress_section(layout)

        # 导出按钮
        self._create_export_button(layout)

    def _create_format_selection(self, parent_layout: QVBoxLayout) -> None:
        """创建格式选择"""
        group = QGroupBox("导出格式")
        layout = QFormLayout(group)

        self.format_combo = ComboBox()
        self.format_combo.addItems(
            ["文本文件 (*.txt)", "CSV文件 (*.csv)", "JSON文件 (*.json)"]
        )
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        layout.addRow("格式:", self.format_combo)

        parent_layout.addWidget(group)

    def _create_output_selection(self, parent_layout: QVBoxLayout) -> None:
        """创建输出路径选择"""
        group = QGroupBox("输出路径")
        layout = QHBoxLayout(group)

        self.output_path_input = LineEdit()
        self.output_path_input.setPlaceholderText("选择输出文件路径")
        layout.addWidget(self.output_path_input)

        self.browse_btn = PushButton(FIF.FOLDER, "浏览")
        self.browse_btn.clicked.connect(self._browse_output_path)
        layout.addWidget(self.browse_btn)

        parent_layout.addWidget(group)

    def _create_export_options(self, parent_layout: QVBoxLayout) -> None:
        """创建导出选项"""
        group = QGroupBox("导出选项")
        layout = QVBoxLayout(group)

        # 压缩选项
        self.compress_check = CheckBox("压缩导出文件")
        layout.addWidget(self.compress_check)

        # 包含过滤条件
        self.include_filters_check = CheckBox("应用当前过滤条件")
        self.include_filters_check.setChecked(True)
        layout.addWidget(self.include_filters_check)

        parent_layout.addWidget(group)

    def _create_progress_section(self, parent_layout: QVBoxLayout) -> None:
        """创建进度显示"""
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        parent_layout.addWidget(self.progress_bar)

        self.status_label = BodyLabel("")
        self.status_label.setVisible(False)
        parent_layout.addWidget(self.status_label)

    def _create_export_button(self, parent_layout: QVBoxLayout) -> None:
        """创建导出按钮"""
        self.export_btn = PushButton(FIF.DOWNLOAD, "导出日志")
        self.export_btn.clicked.connect(self._start_export)
        parent_layout.addWidget(self.export_btn)

    def _setup_connections(self) -> None:
        """设置信号连接"""
        pass

    def _on_format_changed(self, format_text: str) -> None:
        """格式选择改变"""
        if "txt" in format_text:
            self.export_config["format"] = "txt"
        elif "csv" in format_text:
            self.export_config["format"] = "csv"
        elif "json" in format_text:
            self.export_config["format"] = "json"

    def _browse_output_path(self) -> None:
        """浏览输出路径"""
        format_map = {
            "txt": "文本文件 (*.txt)",
            "csv": "CSV文件 (*.csv)",
            "json": "JSON文件 (*.json)",
        }

        file_filter = format_map.get(str(self.export_config["format"]), "所有文件 (*.*)")

        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择导出文件", "", file_filter
        )

        if file_path:
            self.output_path_input.setText(file_path)
            self.export_config["output_path"] = file_path

    def _start_export(self) -> None:
        """开始导出"""
        # 验证配置
        if not self.export_config["output_path"]:
            InfoBar.warning(
                title="路径未选择",
                content="请选择输出文件路径",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            return

        if not self.export_config["source_files"]:
            InfoBar.warning(
                title="无日志文件",
                content="没有可导出的日志文件",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            return

        # 更新配置
        self.export_config["compress"] = self.compress_check.isChecked()

        # 显示进度
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("正在导出日志...")
        self.export_btn.setEnabled(False)

        # 启动导出线程
        self.export_worker = LogExportWorker(self.export_config.copy())
        self.export_worker.progress_updated.connect(self.progress_bar.setValue)
        self.export_worker.export_completed.connect(self._on_export_completed)
        self.export_worker.export_failed.connect(self._on_export_failed)
        self.export_worker.start()

    def _on_export_completed(self, output_path: str) -> None:
        """导出完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.export_btn.setEnabled(True)

        InfoBar.success(
            title="导出完成",
            content=f"日志已导出到: {output_path}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self,
        )

        logger.info(f"日志导出完成: {output_path}")

    def _on_export_failed(self, error_message: str) -> None:
        """导出失败"""
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.export_btn.setEnabled(True)

        InfoBar.error(
            title="导出失败",
            content=f"导出日志时发生错误: {error_message}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self,
        )

        logger.error(f"日志导出失败: {error_message}")

    def set_source_files(self, file_paths: List[str]) -> None:
        """设置源文件列表"""
        self.export_config["source_files"] = file_paths

    def set_filters(self, filters: Dict) -> None:
        """设置过滤条件"""
        if self.include_filters_check.isChecked():
            self.export_config["filters"] = filters
        else:
            self.export_config["filters"] = {}
