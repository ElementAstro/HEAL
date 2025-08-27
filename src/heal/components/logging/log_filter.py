"""
日志过滤器组件

提供日志过滤功能：
- 按日志级别过滤
- 按时间范围过滤
- 按模块名过滤
- 关键词搜索
- 正则表达式搜索
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
    LineEdit,
    PushButton,
    TitleLabel,
)

from src.heal.common.logging_config import get_logger

logger = get_logger(__name__)


class LogFilter(CardWidget):
    """日志过滤器组件"""

    filter_changed = Signal(dict)  # 过滤条件改变信号

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("LogFilter")

        # 过滤条件
        self.current_filters: Dict[str, Any] = {
            "levels": set(),
            "modules": set(),
            "keywords": "",
            "regex": "",
            "start_time": None,
            "end_time": None,
            "case_sensitive": False,
            "use_regex": False,
        }

        # 设置界面
        self._setup_ui()
        self._setup_connections()

        logger.info("日志过滤器初始化完成")

    def _setup_ui(self) -> None:
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = TitleLabel("日志过滤")
        layout.addWidget(title)

        # 日志级别过滤
        self._create_level_filter(layout)

        # 时间范围过滤
        self._create_time_filter(layout)

        # 模块过滤
        self._create_module_filter(layout)

        # 关键词搜索
        self._create_keyword_filter(layout)

        # 控制按钮
        self._create_control_buttons(layout)

    def _create_level_filter(self, parent_layout: QVBoxLayout) -> None:
        """创建日志级别过滤"""
        group = QGroupBox("日志级别")
        layout = QVBoxLayout(group)

        # 日志级别选项
        self.level_checks: dict[str, Any] = {}
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in levels:
            check = CheckBox(level)
            check.setChecked(True)  # 默认显示所有级别
            check.toggled.connect(self._on_level_toggled)
            self.level_checks[level] = check
            layout.addWidget(check)

        # 全选/全不选按钮
        button_layout = QHBoxLayout()

        self.select_all_btn = PushButton("全选")
        self.select_all_btn.clicked.connect(self._select_all_levels)
        button_layout.addWidget(self.select_all_btn)

        self.select_none_btn = PushButton("全不选")
        self.select_none_btn.clicked.connect(self._select_no_levels)
        button_layout.addWidget(self.select_none_btn)

        layout.addLayout(button_layout)
        parent_layout.addWidget(group)

    def _create_time_filter(self, parent_layout: QVBoxLayout) -> None:
        """创建时间范围过滤"""
        group = QGroupBox("时间范围")
        layout = QFormLayout(group)

        # 启用时间过滤
        self.time_filter_enabled = CheckBox("启用时间过滤")
        self.time_filter_enabled.toggled.connect(self._on_time_filter_toggled)
        layout.addRow(self.time_filter_enabled)

        # 开始时间
        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setDateTime(
            QDateTime.currentDateTime().addDays(-1))
        self.start_time_edit.setEnabled(False)
        self.start_time_edit.dateTimeChanged.connect(self._on_time_changed)
        layout.addRow("开始时间:", self.start_time_edit)

        # 结束时间
        self.end_time_edit = QDateTimeEdit()
        self.end_time_edit.setDateTime(QDateTime.currentDateTime())
        self.end_time_edit.setEnabled(False)
        self.end_time_edit.dateTimeChanged.connect(self._on_time_changed)
        layout.addRow("结束时间:", self.end_time_edit)

        # 快速时间选择
        quick_layout = QHBoxLayout()

        self.last_hour_btn = PushButton("最近1小时")
        self.last_hour_btn.clicked.connect(
            lambda: self._set_quick_time(hours=1))
        quick_layout.addWidget(self.last_hour_btn)

        self.last_day_btn = PushButton("最近1天")
        self.last_day_btn.clicked.connect(lambda: self._set_quick_time(days=1))
        quick_layout.addWidget(self.last_day_btn)

        layout.addRow(quick_layout)
        parent_layout.addWidget(group)

    def _create_module_filter(self, parent_layout: QVBoxLayout) -> None:
        """创建模块过滤"""
        group = QGroupBox("模块过滤")
        layout = QVBoxLayout(group)

        # 模块名输入
        self.module_input = LineEdit()
        self.module_input.setPlaceholderText("输入模块名，多个用逗号分隔")
        self.module_input.textChanged.connect(self._on_module_changed)
        layout.addWidget(self.module_input)

        # 常用模块快速选择
        common_modules = [
            "main_interface",
            "download_interface",
            "module_interface",
            "proxy_interface",
            "logging_config",
            "process_monitor",
        ]

        self.module_checks: dict[str, Any] = {}
        for module in common_modules:
            check = CheckBox(module)
            check.toggled.connect(self._on_module_check_toggled)
            self.module_checks[module] = check
            layout.addWidget(check)

        parent_layout.addWidget(group)

    def _create_keyword_filter(self, parent_layout: QVBoxLayout) -> None:
        """创建关键词搜索"""
        group = QGroupBox("关键词搜索")
        layout = QVBoxLayout(group)

        # 关键词输入
        self.keyword_input = LineEdit()
        self.keyword_input.setPlaceholderText("输入搜索关键词")
        self.keyword_input.textChanged.connect(self._on_keyword_changed)
        layout.addWidget(self.keyword_input)

        # 搜索选项
        options_layout = QHBoxLayout()

        self.case_sensitive_check = CheckBox("区分大小写")
        self.case_sensitive_check.toggled.connect(
            self._on_search_option_changed)
        options_layout.addWidget(self.case_sensitive_check)

        self.regex_check = CheckBox("正则表达式")
        self.regex_check.toggled.connect(self._on_search_option_changed)
        options_layout.addWidget(self.regex_check)

        layout.addLayout(options_layout)

        # 正则表达式输入
        self.regex_input = LineEdit()
        self.regex_input.setPlaceholderText("输入正则表达式")
        self.regex_input.setEnabled(False)
        self.regex_input.textChanged.connect(self._on_regex_changed)
        layout.addWidget(self.regex_input)

        parent_layout.addWidget(group)

    def _create_control_buttons(self, parent_layout: QVBoxLayout) -> None:
        """创建控制按钮"""
        button_layout = QHBoxLayout()

        # 应用过滤按钮
        self.apply_btn = PushButton(FIF.ACCEPT, "应用过滤")
        self.apply_btn.clicked.connect(self._apply_filter)
        button_layout.addWidget(self.apply_btn)

        # 重置按钮
        self.reset_btn = PushButton(FIF.CANCEL, "重置")
        self.reset_btn.clicked.connect(self._reset_filter)
        button_layout.addWidget(self.reset_btn)

        parent_layout.addLayout(button_layout)

    def _setup_connections(self) -> None:
        """设置信号连接"""
        # 实时过滤（可选）
        pass

    def _on_level_toggled(self, checked: bool) -> None:
        """日志级别选择改变"""
        self._update_level_filter()

    def _on_time_filter_toggled(self, enabled: bool) -> None:
        """时间过滤启用状态改变"""
        self.start_time_edit.setEnabled(enabled)
        self.end_time_edit.setEnabled(enabled)
        self.last_hour_btn.setEnabled(enabled)
        self.last_day_btn.setEnabled(enabled)
        self._update_time_filter()

    def _on_time_changed(self) -> None:
        """时间范围改变"""
        self._update_time_filter()

    def _on_module_changed(self) -> None:
        """模块输入改变"""
        self._update_module_filter()

    def _on_module_check_toggled(self, checked: bool) -> None:
        """模块复选框改变"""
        self._update_module_filter_from_checks()

    def _on_keyword_changed(self) -> None:
        """关键词改变"""
        self._update_keyword_filter()

    def _on_search_option_changed(self) -> None:
        """搜索选项改变"""
        use_regex = self.regex_check.isChecked()
        self.regex_input.setEnabled(use_regex)
        self.keyword_input.setEnabled(not use_regex)

        self.current_filters["case_sensitive"] = self.case_sensitive_check.isChecked(
        )
        self.current_filters["use_regex"] = use_regex

    def _on_regex_changed(self) -> None:
        """正则表达式改变"""
        self.current_filters["regex"] = self.regex_input.text()

    def _select_all_levels(self) -> None:
        """选择所有日志级别"""
        for check in self.level_checks.values():
            check.setChecked(True)
        self._update_level_filter()

    def _select_no_levels(self) -> None:
        """取消选择所有日志级别"""
        for check in self.level_checks.values():
            check.setChecked(False)
        self._update_level_filter()

    def _set_quick_time(self, **kwargs: Any) -> None:
        """设置快速时间范围"""
        end_time = QDateTime.currentDateTime()
        start_time = end_time.addSecs(-timedelta(**kwargs).total_seconds())

        self.start_time_edit.setDateTime(start_time)
        self.end_time_edit.setDateTime(end_time)
        self.time_filter_enabled.setChecked(True)
        self._on_time_filter_toggled(True)

    def _update_level_filter(self) -> None:
        """更新日志级别过滤"""
        selected_levels = set()
        for level, check in self.level_checks.items():
            if check.isChecked():
                selected_levels.add(level)
        self.current_filters["levels"] = selected_levels

    def _update_time_filter(self) -> None:
        """更新时间过滤"""
        if self.time_filter_enabled.isChecked():
            self.current_filters["start_time"] = (
                self.start_time_edit.dateTime().toPython()
            )
            self.current_filters["end_time"] = self.end_time_edit.dateTime(
            ).toPython()
        else:
            self.current_filters["start_time"] = None
            self.current_filters["end_time"] = None

    def _update_module_filter(self) -> None:
        """更新模块过滤"""
        module_text = self.module_input.text().strip()
        if module_text:
            modules = set(m.strip()
                          for m in module_text.split(",") if m.strip())
        else:
            modules = set()
        self.current_filters["modules"] = modules

    def _update_module_filter_from_checks(self) -> None:
        """从复选框更新模块过滤"""
        selected_modules = set()
        for module, check in self.module_checks.items():
            if check.isChecked():
                selected_modules.add(module)

        # 更新输入框
        if selected_modules:
            self.module_input.setText(", ".join(sorted(selected_modules)))
        else:
            self.module_input.clear()

        self.current_filters["modules"] = selected_modules

    def _update_keyword_filter(self) -> None:
        """更新关键词过滤"""
        self.current_filters["keywords"] = self.keyword_input.text()

    def _apply_filter(self) -> None:
        """应用过滤条件"""
        # 发送过滤条件改变信号
        self.filter_changed.emit(self.current_filters.copy())
        logger.info(f"应用日志过滤条件: {self.current_filters}")

    def _reset_filter(self) -> None:
        """重置过滤条件"""
        # 重置所有控件
        for check in self.level_checks.values():
            check.setChecked(True)

        self.time_filter_enabled.setChecked(False)
        self._on_time_filter_toggled(False)

        self.module_input.clear()
        for check in self.module_checks.values():
            check.setChecked(False)

        self.keyword_input.clear()
        self.regex_input.clear()
        self.case_sensitive_check.setChecked(False)
        self.regex_check.setChecked(False)
        self._on_search_option_changed()

        # 重置过滤条件
        self.current_filters = {
            "levels": set(self.level_checks.keys()),
            "modules": set(),
            "keywords": "",
            "regex": "",
            "start_time": None,
            "end_time": None,
            "case_sensitive": False,
            "use_regex": False,
        }

        # 应用重置后的过滤条件
        self._apply_filter()

    def get_current_filters(self) -> Dict:
        """获取当前过滤条件"""
        return self.current_filters.copy()

    def set_filters(self, filters: Dict) -> None:
        """设置过滤条件"""
        # TODO: 根据传入的过滤条件更新UI控件
        self.current_filters.update(filters)
        self._apply_filter()
