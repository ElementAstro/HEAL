"""
日志查看器组件

提供实时日志显示功能：
- 多文件日志查看
- 实时日志更新
- 语法高亮
- 自动滚动
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QTabWidget,
    QComboBox, QCheckBox, QLabel, QFrame
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat, QSyntaxHighlighter, QTextDocument

from qfluentwidgets import (
    FluentIcon as FIF, ComboBox, CheckBox, BodyLabel, CardWidget
)

from app.common.logging_config import get_logger

logger = get_logger(__name__)


class LogHighlighter(QSyntaxHighlighter):
    """日志语法高亮器"""
    
    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        self._setup_formats()
    
    def _setup_formats(self):
        """设置高亮格式"""
        self.formats = {}
        
        # 时间戳格式
        timestamp_format = QTextCharFormat()
        timestamp_format.setForeground(QColor(128, 128, 128))
        self.formats['timestamp'] = timestamp_format
        
        # 日志级别格式
        debug_format = QTextCharFormat()
        debug_format.setForeground(QColor(128, 128, 128))
        self.formats['DEBUG'] = debug_format
        
        info_format = QTextCharFormat()
        info_format.setForeground(QColor(0, 128, 255))
        self.formats['INFO'] = info_format
        
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(255, 165, 0))
        warning_format.setFontWeight(QFont.Weight.Bold)
        self.formats['WARNING'] = warning_format
        
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(255, 0, 0))
        error_format.setFontWeight(QFont.Weight.Bold)
        self.formats['ERROR'] = error_format
        
        critical_format = QTextCharFormat()
        critical_format.setForeground(QColor(255, 255, 255))
        critical_format.setBackground(QColor(255, 0, 0))
        critical_format.setFontWeight(QFont.Weight.Bold)
        self.formats['CRITICAL'] = critical_format
        
        # 模块名格式
        module_format = QTextCharFormat()
        module_format.setForeground(QColor(0, 128, 0))
        self.formats['module'] = module_format
    
    def highlightBlock(self, text: str):
        """高亮文本块"""
        # 时间戳高亮 (YYYY-MM-DD HH:mm:ss.SSS)
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}'
        for match in re.finditer(timestamp_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['timestamp'])
        
        # 日志级别高亮
        level_pattern = r'\|\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\|'
        for match in re.finditer(level_pattern, text):
            level = match.group(1)
            if level in self.formats:
                self.setFormat(match.start(), match.end() - match.start(), self.formats[level])
        
        # 模块名高亮
        module_pattern = r'\|\s*([a-zA-Z_][a-zA-Z0-9_.]*):([a-zA-Z_][a-zA-Z0-9_]*):(\d+)\s*\|'
        for match in re.finditer(module_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['module'])


class LogFileWatcher(QThread):
    """日志文件监控线程"""

    new_lines = Signal(str, list)  # 文件名, 新行列表
    
    def __init__(self, log_files: Dict[str, Path]):
        super().__init__()
        self.log_files = log_files
        self.file_positions = {}
        self.running = True
        
        # 初始化文件位置
        for name, path in log_files.items():
            if path.exists():
                self.file_positions[name] = path.stat().st_size
            else:
                self.file_positions[name] = 0
    
    def run(self):
        """运行监控循环"""
        while self.running:
            for name, path in self.log_files.items():
                if path.exists():
                    current_size = path.stat().st_size
                    last_position = self.file_positions.get(name, 0)
                    
                    if current_size > last_position:
                        # 读取新内容
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                f.seek(last_position)
                                new_content = f.read()
                                if new_content:
                                    new_lines = new_content.strip().split('\n')
                                    self.new_lines.emit(name, new_lines)
                                self.file_positions[name] = current_size
                        except Exception as e:
                            logger.error(f"读取日志文件 {path} 失败: {e}")
            
            self.msleep(1000)  # 每秒检查一次
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.wait()


class LogViewer(CardWidget):
    """日志查看器主组件"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("LogViewer")
        
        # 日志文件配置
        self.log_files = self._get_log_files()
        self.current_filters = {}
        self.auto_scroll = True
        self.max_lines = 10000  # 最大显示行数
        
        # 设置界面
        self._setup_ui()
        self._setup_watcher()
        
        logger.info("日志查看器初始化完成")
    
    def _get_log_files(self) -> Dict[str, Path]:
        """获取日志文件列表"""
        log_dir = Path("logs")
        files = {}
        
        if log_dir.exists():
            # 主要日志文件
            main_files = [
                "application.log",
                "errors.log", 
                "exceptions.log",
                "performance.log",
                "downloads.log",
                "network.log"
            ]
            
            for file_name in main_files:
                file_path = log_dir / file_name
                if file_path.exists():
                    files[file_name.replace('.log', '')] = file_path
            
            # 动态发现其他日志文件
            for log_file in log_dir.glob("*.log"):
                if log_file.name not in main_files:
                    name = log_file.stem
                    files[name] = log_file
        
        return files
    
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 控制栏
        self._create_control_bar(layout)
        
        # 日志显示区域
        self._create_log_display(layout)
    
    def _create_control_bar(self, parent_layout: QVBoxLayout):
        """创建控制栏"""
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # 文件选择
        file_label = BodyLabel("日志文件:")
        control_layout.addWidget(file_label)
        
        self.file_combo = ComboBox()
        self.file_combo.addItems(list(self.log_files.keys()))
        self.file_combo.currentTextChanged.connect(self._on_file_changed)
        control_layout.addWidget(self.file_combo)
        
        control_layout.addStretch()
        
        # 自动滚动选项
        self.auto_scroll_check = CheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.toggled.connect(self._on_auto_scroll_toggled)
        control_layout.addWidget(self.auto_scroll_check)
        
        parent_layout.addWidget(control_frame)
    
    def _create_log_display(self, parent_layout: QVBoxLayout):
        """创建日志显示区域"""
        # 使用标签页显示不同日志文件
        self.tab_widget = QTabWidget()
        
        # 为每个日志文件创建标签页
        self.text_widgets = {}
        for name, path in self.log_files.items():
            text_widget = QTextEdit()
            text_widget.setReadOnly(True)
            text_widget.setFont(QFont("Consolas", 9))
            
            # 添加语法高亮
            highlighter = LogHighlighter(text_widget.document())
            
            self.text_widgets[name] = text_widget
            self.tab_widget.addTab(text_widget, name.title())
            
            # 加载初始内容
            self._load_initial_content(name, path, text_widget)
        
        parent_layout.addWidget(self.tab_widget)
    
    def _load_initial_content(self, name: str, path: Path, text_widget: QTextEdit):
        """加载初始日志内容"""
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    # 只读取最后的部分内容，避免加载过大文件
                    f.seek(0, 2)  # 移到文件末尾
                    file_size = f.tell()
                    
                    # 读取最后100KB或整个文件
                    read_size = min(100 * 1024, file_size)
                    f.seek(max(0, file_size - read_size))
                    
                    content = f.read()
                    
                    # 如果不是从文件开头读取，跳过第一行（可能不完整）
                    if file_size > read_size:
                        lines = content.split('\n')[1:]
                        content = '\n'.join(lines)
                    
                    text_widget.setPlainText(content)
                    
                    # 滚动到底部
                    if self.auto_scroll:
                        cursor = text_widget.textCursor()
                        cursor.movePosition(QTextCursor.MoveOperation.End)
                        text_widget.setTextCursor(cursor)
                        
        except Exception as e:
            logger.error(f"加载日志文件 {path} 失败: {e}")
            text_widget.setPlainText(f"加载日志文件失败: {e}")
    
    def _setup_watcher(self):
        """设置文件监控"""
        self.watcher = LogFileWatcher(self.log_files)
        self.watcher.new_lines.connect(self._on_new_lines)
        self.watcher.start()
    
    def _on_file_changed(self, file_name: str):
        """文件选择改变"""
        # 切换到对应的标签页
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i).lower() == file_name.lower():
                self.tab_widget.setCurrentIndex(i)
                break
    
    def _on_auto_scroll_toggled(self, checked: bool):
        """自动滚动选项切换"""
        self.auto_scroll = checked
    
    def _on_new_lines(self, file_name: str, new_lines: List[str]):
        """处理新的日志行"""
        if file_name in self.text_widgets:
            text_widget = self.text_widgets[file_name]
            
            # 添加新行
            for line in new_lines:
                if line.strip():  # 跳过空行
                    # 检查是否符合过滤条件
                    if self._line_matches_filter(line):
                        text_widget.append(line)
            
            # 限制最大行数
            self._limit_text_lines(text_widget)
            
            # 自动滚动到底部
            if self.auto_scroll:
                cursor = text_widget.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                text_widget.setTextCursor(cursor)
    
    def _line_matches_filter(self, line: str) -> bool:
        """检查行是否匹配过滤条件"""
        # TODO: 实现过滤逻辑
        return True
    
    def _limit_text_lines(self, text_widget: QTextEdit):
        """限制文本行数"""
        document = text_widget.document()
        if document.blockCount() > self.max_lines:
            # 删除前面的行
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            
            # 删除超出的行数
            lines_to_remove = document.blockCount() - self.max_lines
            for _ in range(lines_to_remove):
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # 删除换行符
    
    def apply_filter(self, filters: Dict):
        """应用过滤条件"""
        self.current_filters = filters
        # TODO: 重新加载并过滤日志内容
    
    def export_logs(self, export_config: Dict):
        """导出日志"""
        # TODO: 实现日志导出功能
        pass
    
    def refresh(self):
        """刷新日志显示"""
        # 重新加载所有日志文件
        for name, path in self.log_files.items():
            if name in self.text_widgets:
                text_widget = self.text_widgets[name]
                text_widget.clear()
                self._load_initial_content(name, path, text_widget)
    
    def closeEvent(self, event):
        """关闭事件"""
        if hasattr(self, 'watcher'):
            self.watcher.stop()
        super().closeEvent(event)
