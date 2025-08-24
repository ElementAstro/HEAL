"""
Module Validation UI
Provides a comprehensive interface for module validation with detailed reporting.
"""

import json
from typing import Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLabel,
    QGroupBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from qfluentwidgets import (
    PushButton, ComboBox, LineEdit, FluentIcon,
    InfoBar, InfoBarPosition, CardWidget, HeaderCardWidget,
    BodyLabel, SubtitleLabel, CaptionLabel, PrimaryPushButton,
    ToolButton, ProgressRing, MessageBox
)

from app.common.logging_config import get_logger

logger = get_logger(__name__)


# 样式常量
CRITICAL_STYLE = "color: #d13438; font-weight: bold;"
ERROR_STYLE = "color: #ff8c00; font-weight: bold;"
WARNING_STYLE = "color: #ffd700; font-weight: bold;"
SUCCESS_STYLE = "color: #107c10; font-weight: bold;"
INFO_STYLE = "color: #0078d4; font-weight: bold;"


class ValidationLevel(Enum):
    """验证级别"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    SECURITY = "security"


class ValidationResult(Enum):
    """验证结果"""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """验证问题"""
    level: ValidationResult
    category: str
    message: str
    details: str = ""
    fix_suggestion: str = ""
    code: str = ""


@dataclass
class ModuleValidationReport:
    """模块验证报告"""
    module_name: str
    module_path: str
    validation_level: ValidationLevel
    overall_result: ValidationResult
    timestamp: float = field(default_factory=time.time)
    issues: list[ValidationIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def critical_issues(self) -> list[ValidationIssue]:
        """严重问题"""
        return [i for i in self.issues if i.level == ValidationResult.CRITICAL]

    @property
    def error_issues(self) -> list[ValidationIssue]:
        """错误问题"""
        return [i for i in self.issues if i.level == ValidationResult.FAILED]

    @property
    def warning_issues(self) -> list[ValidationIssue]:
        """警告问题"""
        return [i for i in self.issues if i.level == ValidationResult.WARNING]


class ModuleValidator:
    """简化的模块验证器"""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level

    def validate_module(self, module_path: str) -> ModuleValidationReport:
        """验证模块"""
        path = Path(module_path)
        module_name = path.stem

        # 基础验证逻辑
        issues = []
        overall_result = ValidationResult.PASSED

        # 检查文件是否存在
        if not path.exists():
            issues.append(ValidationIssue(
                level=ValidationResult.CRITICAL,
                category="文件系统",
                message="模块文件不存在",
                details=f"无法找到文件: {module_path}",
                fix_suggestion="检查文件路径是否正确"
            ))
            overall_result = ValidationResult.CRITICAL

        # 检查文件扩展名
        elif path.suffix.lower() not in ['.jar', '.zip', '.mod', '.py']:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="文件格式",
                message="不支持的文件格式",
                details=f"文件扩展名: {path.suffix}",
                fix_suggestion="使用支持的文件格式 (.jar, .zip, .mod, .py)"
            ))
            if overall_result == ValidationResult.PASSED:
                overall_result = ValidationResult.WARNING

        # 检查文件大小
        if path.exists() and path.stat().st_size == 0:
            issues.append(ValidationIssue(
                level=ValidationResult.FAILED,
                category="文件内容",
                message="文件为空",
                details="模块文件大小为0字节",
                fix_suggestion="确保模块文件包含有效内容"
            ))
            overall_result = ValidationResult.FAILED

        return ModuleValidationReport(
            module_name=module_name,
            module_path=module_path,
            validation_level=self.validation_level,
            overall_result=overall_result,
            issues=issues,
            metadata={"name": module_name,
                      "size": path.stat().st_size if path.exists() else 0}
        )

    def validate_batch(self, file_paths: list[str]) -> list[ModuleValidationReport]:
        """批量验证模块"""
        reports = []
        for file_path in file_paths:
            try:
                report = self.validate_module(file_path)
                reports.append(report)
            except Exception as e:
                # 创建错误报告
                error_report = ModuleValidationReport(
                    module_name=Path(file_path).stem,
                    module_path=file_path,
                    validation_level=self.validation_level,
                    overall_result=ValidationResult.CRITICAL,
                    issues=[ValidationIssue(
                        level=ValidationResult.CRITICAL,
                        category="验证错误",
                        message=f"验证过程中出错: {str(e)}",
                        fix_suggestion="检查文件是否可访问"
                    )]
                )
                reports.append(error_report)
        return reports

    def get_validation_summary(self, reports: list[ModuleValidationReport]) -> dict[str, Any]:
        """获取验证摘要"""
        total = len(reports)
        passed = sum(1 for r in reports if r.overall_result ==
                     ValidationResult.PASSED)
        warnings = sum(1 for r in reports if r.overall_result ==
                       ValidationResult.WARNING)
        failed = sum(1 for r in reports if r.overall_result ==
                     ValidationResult.FAILED)
        critical = sum(1 for r in reports if r.overall_result ==
                       ValidationResult.CRITICAL)

        return {
            'total_modules': total,
            'passed': passed,
            'warnings': warnings,
            'failed': failed,
            'critical': critical,
            'success_rate': (passed + warnings) / total * 100 if total > 0 else 0
        }


class ValidationIssueWidget(CardWidget):
    """验证问题显示组件"""

    def __init__(self, issue: ValidationIssue, parent=None):
        super().__init__(parent)
        self.issue = issue
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # 标题行
        title_layout = QHBoxLayout()

        # 问题级别图标
        level_icon = self._get_level_icon(self.issue.level)
        icon_label = QLabel()
        icon_label.setPixmap(level_icon.pixmap(16, 16))
        title_layout.addWidget(icon_label)

        # 问题消息
        message_label = SubtitleLabel(self.issue.message)
        title_layout.addWidget(message_label)

        title_layout.addStretch()

        # 问题类别
        category_label = CaptionLabel(f"类别: {self.issue.category}")
        category_label.setStyleSheet("color: gray;")
        title_layout.addWidget(category_label)

        layout.addLayout(title_layout)

        # 详细信息
        if self.issue.details:
            details_label = BodyLabel(self.issue.details)
            details_label.setWordWrap(True)
            layout.addWidget(details_label)

        # 修复建议
        if self.issue.fix_suggestion:
            fix_label = BodyLabel(f"💡 建议: {self.issue.fix_suggestion}")
            fix_label.setWordWrap(True)
            fix_label.setStyleSheet(INFO_STYLE + " font-style: italic;")
            layout.addWidget(fix_label)

        # 设置卡片样式
        self._set_card_style()

    def _get_level_icon(self, level: ValidationResult) -> QIcon:
        """获取级别图标"""
        if level == ValidationResult.CRITICAL:
            return FluentIcon.CANCEL.icon()
        elif level == ValidationResult.FAILED:
            return FluentIcon.CLOSE.icon()
        elif level == ValidationResult.WARNING:
            return FluentIcon.INFO.icon()  # 使用INFO替代WARNING
        else:
            return FluentIcon.ACCEPT.icon()

    def _set_card_style(self):
        """设置卡片样式"""
        if self.issue.level == ValidationResult.CRITICAL:
            self.setStyleSheet("border-left: 4px solid #d13438;")
        elif self.issue.level == ValidationResult.FAILED:
            self.setStyleSheet("border-left: 4px solid #ff8c00;")
        elif self.issue.level == ValidationResult.WARNING:
            self.setStyleSheet("border-left: 4px solid #ffd700;")
        else:
            self.setStyleSheet("border-left: 4px solid #0078d4;")


class ValidationReportWidget(QScrollArea):
    """验证报告显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.setWidget(self.content_widget)

        self.current_report: Optional[ModuleValidationReport] = None

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        # 报告头部
        self.header_card = HeaderCardWidget(parent=self.content_widget)
        self.header_card.setTitle("验证报告")
        self.content_layout.addWidget(self.header_card)

        # 占位符
        self.placeholder_label = BodyLabel("选择模块进行验证以查看报告")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.placeholder_label)

        self.content_layout.addStretch()

    def update_report(self, report: ModuleValidationReport):
        """更新验证报告"""
        self.current_report = report
        self._clear_content()
        self._display_report()

    def _clear_content(self):
        """清除内容"""
        # 移除除了头部卡片之外的所有组件
        for i in reversed(range(1, self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

    def _display_report(self):
        """显示报告"""
        if not self.current_report:
            return

        # 确保 current_report 不为 None
        report = self.current_report

        # 更新头部
        result_text = report.overall_result.value.upper()
        self.header_card.setTitle(f"验证报告 - {result_text}")

        # 基本信息
        info_card = self._create_info_card()
        self.content_layout.addWidget(info_card)

        # 验证问题
        if report.issues:
            issues_card = self._create_issues_card()
            self.content_layout.addWidget(issues_card)

        # 元数据信息
        if report.metadata:
            metadata_card = self._create_metadata_card()
            self.content_layout.addWidget(metadata_card)

        self.content_layout.addStretch()

    def _create_info_card(self) -> CardWidget:
        """创建基本信息卡片"""
        if not self.current_report:
            return CardWidget()

        report = self.current_report
        card = CardWidget()
        layout = QVBoxLayout(card)

        # 标题
        title_label = SubtitleLabel("基本信息")
        layout.addWidget(title_label)

        # 信息网格
        info_layout = QGridLayout()

        info_layout.addWidget(BodyLabel("模块路径:"), 0, 0)
        info_layout.addWidget(BodyLabel(report.module_path), 0, 1)

        info_layout.addWidget(BodyLabel("验证级别:"), 1, 0)
        info_layout.addWidget(
            BodyLabel(report.validation_level.value), 1, 1)

        info_layout.addWidget(BodyLabel("验证结果:"), 2, 0)
        result_label = BodyLabel(report.overall_result.value)
        result_label.setStyleSheet(self._get_result_style(
            report.overall_result))
        info_layout.addWidget(result_label, 2, 1)

        info_layout.addWidget(BodyLabel("问题数量:"), 3, 0)
        info_layout.addWidget(
            BodyLabel(str(len(report.issues))), 3, 1)

        # 验证时间
        import datetime
        timestamp = datetime.datetime.fromtimestamp(
            report.timestamp)
        info_layout.addWidget(BodyLabel("验证时间:"), 4, 0)
        info_layout.addWidget(
            BodyLabel(timestamp.strftime("%Y-%m-%d %H:%M:%S")), 4, 1)

        layout.addLayout(info_layout)

        return card

    def _create_issues_card(self) -> CardWidget:
        """创建问题卡片"""
        if not self.current_report:
            return CardWidget()

        report = self.current_report
        card = CardWidget()
        layout = QVBoxLayout(card)

        # 标题
        title_label = SubtitleLabel(
            f"验证问题 ({len(report.issues)})")
        layout.addWidget(title_label)

        # 问题统计
        stats_layout = QHBoxLayout()

        critical_count = len(report.critical_issues)
        error_count = len(report.error_issues)
        warning_count = len(report.warning_issues)

        if critical_count > 0:
            critical_label = CaptionLabel(f"严重: {critical_count}")
            critical_label.setStyleSheet(CRITICAL_STYLE)
            stats_layout.addWidget(critical_label)

        if error_count > 0:
            error_label = CaptionLabel(f"错误: {error_count}")
            error_label.setStyleSheet(ERROR_STYLE)
            stats_layout.addWidget(error_label)

        if warning_count > 0:
            warning_label = CaptionLabel(f"警告: {warning_count}")
            warning_label.setStyleSheet(WARNING_STYLE)
            stats_layout.addWidget(warning_label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # 问题列表
        issues_scroll = QScrollArea()
        issues_scroll.setWidgetResizable(True)
        issues_scroll.setMaximumHeight(300)

        issues_widget = QWidget()
        issues_layout = QVBoxLayout(issues_widget)

        for issue in report.issues:
            issue_widget = ValidationIssueWidget(issue)
            issues_layout.addWidget(issue_widget)

        issues_layout.addStretch()
        issues_scroll.setWidget(issues_widget)
        layout.addWidget(issues_scroll)

        return card

    def _create_metadata_card(self) -> CardWidget:
        """创建元数据卡片"""
        if not self.current_report:
            return CardWidget()

        report = self.current_report
        card = CardWidget()
        layout = QVBoxLayout(card)

        # 标题
        title_label = SubtitleLabel("模块元数据")
        layout.addWidget(title_label)

        # 元数据树
        tree = QTreeWidget()
        tree.setHeaderLabels(["键", "值"])
        tree.setMaximumHeight(200)

        self._populate_metadata_tree(tree, report.metadata)

        layout.addWidget(tree)

        return card

    def _populate_metadata_tree(self, tree: QTreeWidget, data: Any, parent: Optional[QTreeWidgetItem] = None):
        """填充元数据树"""
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem(parent or tree, [str(key)])
                self._populate_metadata_tree(tree, value, item)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                item = QTreeWidgetItem(parent or tree, [f"[{i}]"])
                self._populate_metadata_tree(tree, value, item)
        else:
            if parent:
                parent.setText(1, str(data))

    def _get_result_style(self, result: ValidationResult) -> str:
        """获取结果样式"""
        if result == ValidationResult.PASSED:
            return SUCCESS_STYLE
        elif result == ValidationResult.WARNING:
            return WARNING_STYLE
        elif result == ValidationResult.FAILED:
            return ERROR_STYLE
        elif result == ValidationResult.CRITICAL:
            return CRITICAL_STYLE
        else:
            return ""


class ModuleValidationUI(QWidget):
    """模块验证UI"""

    # 信号
    validation_requested = Signal(str, str)  # module_path, validation_level

    def __init__(self, validator: Optional[ModuleValidator] = None, parent=None):
        super().__init__(parent)
        self.validator = validator or ModuleValidator()
        self.current_validation_report: Optional[ModuleValidationReport] = None

        self.logger = logger.bind(component="ModuleValidationUI")
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # 控制面板
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)

        # 主要内容区域
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：模块列表和验证控制
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧：验证报告
        self.report_widget = ValidationReportWidget()
        splitter.addWidget(self.report_widget)

        # 设置分割器比例
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)

        # 状态栏
        self.status_bar = self._create_status_bar()
        layout.addWidget(self.status_bar)

    def _create_control_panel(self) -> QGroupBox:
        """创建控制面板"""
        group = QGroupBox("验证设置")
        layout = QHBoxLayout(group)

        # 验证级别选择
        layout.addWidget(BodyLabel("验证级别:"))

        self.level_combo = ComboBox()
        self.level_combo.addItems([
            "基础验证", "标准验证", "严格验证", "安全验证"
        ])
        self.level_combo.setCurrentIndex(1)  # 默认标准验证
        layout.addWidget(self.level_combo)

        layout.addStretch()

        # 批量验证按钮
        self.batch_validate_btn = PrimaryPushButton("批量验证")
        self.batch_validate_btn.setIcon(FluentIcon.CERTIFICATE)
        layout.addWidget(self.batch_validate_btn)

        # 导出报告按钮
        self.export_btn = PushButton("导出报告")
        self.export_btn.setIcon(FluentIcon.SAVE)
        layout.addWidget(self.export_btn)

        return group

    def _create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 模块选择
        module_group = QGroupBox("模块选择")
        module_layout = QVBoxLayout(module_group)

        # 文件路径输入
        path_layout = QHBoxLayout()
        path_layout.addWidget(BodyLabel("模块路径:"))

        self.path_edit = LineEdit()
        self.path_edit.setPlaceholderText("选择或输入模块文件路径...")
        path_layout.addWidget(self.path_edit)

        self.browse_btn = ToolButton()
        self.browse_btn.setIcon(FluentIcon.FOLDER)
        self.browse_btn.setToolTip("浏览文件")
        path_layout.addWidget(self.browse_btn)

        module_layout.addLayout(path_layout)

        # 验证按钮
        self.validate_btn = PrimaryPushButton("开始验证")
        self.validate_btn.setIcon(FluentIcon.PLAY)
        module_layout.addWidget(self.validate_btn)

        layout.addWidget(module_group)

        # 快速验证结果
        result_group = QGroupBox("验证结果")
        result_layout = QVBoxLayout(result_group)

        self.result_label = BodyLabel("等待验证...")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_layout.addWidget(self.result_label)

        self.progress_ring = ProgressRing()
        self.progress_ring.setVisible(False)
        result_layout.addWidget(self.progress_ring)

        layout.addWidget(result_group)

        layout.addStretch()

        return widget

    def _create_status_bar(self) -> QFrame:
        """创建状态栏"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)

        self.status_label = CaptionLabel("就绪")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # 统计信息
        self.stats_label = CaptionLabel("")
        layout.addWidget(self.stats_label)

        return frame

    def _connect_signals(self):
        """连接信号"""
        self.validate_btn.clicked.connect(self._on_validate_clicked)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        self.batch_validate_btn.clicked.connect(
            self._on_batch_validate_clicked)
        self.export_btn.clicked.connect(self._on_export_clicked)
        self.level_combo.currentTextChanged.connect(self._on_level_changed)

    def _on_validate_clicked(self):
        """验证按钮点击"""
        module_path = self.path_edit.text().strip()
        if not module_path:
            InfoBar.warning(
                title="输入错误",
                content="请输入模块文件路径",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if not Path(module_path).exists():
            InfoBar.error(
                title="文件不存在",
                content="指定的模块文件不存在",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        self._start_validation(module_path)

    def _on_browse_clicked(self):
        """浏览按钮点击"""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择模块文件",
            "",
            "模块文件 (*.jar *.zip *.mod *.py);;所有文件 (*.*)"
        )

        if file_path:
            self.path_edit.setText(file_path)

    def _on_batch_validate_clicked(self):
        """批量验证按钮点击"""
        from PySide6.QtWidgets import QFileDialog

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择模块文件",
            "",
            "模块文件 (*.jar *.zip *.mod *.py);;所有文件 (*.*)"
        )

        if file_paths:
            self._start_batch_validation(file_paths)

    def _on_export_clicked(self):
        """导出按钮点击"""
        if not self.current_validation_report:
            InfoBar.warning(
                title="无数据",
                content="没有可导出的验证报告",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出验证报告",
            "",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )

        if file_path:
            self._export_report(file_path)

    def _on_level_changed(self, text: str):
        """验证级别改变"""
        level_map = {
            "基础验证": ValidationLevel.BASIC,
            "标准验证": ValidationLevel.STANDARD,
            "严格验证": ValidationLevel.STRICT,
            "安全验证": ValidationLevel.SECURITY
        }

        new_level = level_map.get(text, ValidationLevel.STANDARD)
        self.validator.validation_level = new_level

        self.logger.info(f"验证级别已设置为: {new_level.value}")

    def _start_validation(self, module_path: str):
        """开始验证"""
        self.validate_btn.setEnabled(False)
        self.progress_ring.setVisible(True)
        self.result_label.setText("验证中...")
        self.status_label.setText(f"正在验证: {Path(module_path).name}")

        try:
            # 执行验证
            report = self.validator.validate_module(module_path)
            self.current_validation_report = report

            # 更新UI
            self._update_validation_result(report)

            # 显示报告
            self.report_widget.update_report(report)

        except Exception as e:
            self.logger.error(f"验证失败: {e}")
            InfoBar.error(
                title="验证失败",
                content=f"验证过程中发生错误: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        finally:
            self.validate_btn.setEnabled(True)
            self.progress_ring.setVisible(False)
            self.status_label.setText("就绪")

    def _start_batch_validation(self, file_paths: list[str]):
        """开始批量验证"""
        self.batch_validate_btn.setEnabled(False)
        self.status_label.setText(f"正在批量验证 {len(file_paths)} 个文件...")

        try:
            reports = self.validator.validate_batch(file_paths)

            # 显示批量验证结果
            self._show_batch_results(reports)

        except Exception as e:
            self.logger.error(f"批量验证失败: {e}")
            InfoBar.error(
                title="批量验证失败",
                content=f"批量验证过程中发生错误: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        finally:
            self.batch_validate_btn.setEnabled(True)
            self.status_label.setText("就绪")

    def _update_validation_result(self, report: ModuleValidationReport):
        """更新验证结果"""
        result_text = report.overall_result.value.upper()

        if report.overall_result == ValidationResult.PASSED:
            self.result_label.setText(f"✅ {result_text}")
            self.result_label.setStyleSheet(SUCCESS_STYLE)
        elif report.overall_result == ValidationResult.WARNING:
            self.result_label.setText(f"⚠️ {result_text}")
            self.result_label.setStyleSheet(WARNING_STYLE)
        elif report.overall_result == ValidationResult.FAILED:
            self.result_label.setText(f"❌ {result_text}")
            self.result_label.setStyleSheet(ERROR_STYLE)
        else:  # CRITICAL
            self.result_label.setText(f"🚫 {result_text}")
            self.result_label.setStyleSheet(CRITICAL_STYLE)

        # 更新统计信息
        self.stats_label.setText(
            f"问题: {len(report.issues)} | 严重: {len(report.critical_issues)} | 错误: {len(report.error_issues)}")

    def _show_batch_results(self, reports: list[ModuleValidationReport]):
        """显示批量验证结果"""
        summary = self.validator.get_validation_summary(reports)

        content = f"""批量验证完成！

总模块数: {summary['total_modules']}
通过: {summary['passed']}
警告: {summary['warnings']}
失败: {summary['failed']}
严重: {summary['critical']}
成功率: {summary['success_rate']:.1f}%"""

        # 使用简单的MessageBox替代不存在的information方法
        msg_box = MessageBox("批量验证结果", content, self)
        msg_box.exec()

    def _export_report(self, file_path: str):
        """导出报告"""
        try:
            if not self.current_validation_report:
                return

            report_data = {
                'module_path': self.current_validation_report.module_path,
                'validation_level': self.current_validation_report.validation_level.value,
                'overall_result': self.current_validation_report.overall_result.value,
                'timestamp': self.current_validation_report.timestamp,
                'issues': [
                    {
                        'level': issue.level.value,
                        'category': issue.category,
                        'message': issue.message,
                        'details': issue.details,
                        'fix_suggestion': issue.fix_suggestion
                    }
                    for issue in self.current_validation_report.issues
                ],
                'metadata': self.current_validation_report.metadata
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            InfoBar.success(
                title="导出成功",
                content=f"验证报告已导出到: {file_path}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

        except Exception as e:
            self.logger.error(f"导出报告失败: {e}")
            InfoBar.error(
                title="导出失败",
                content=f"导出报告时发生错误: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
