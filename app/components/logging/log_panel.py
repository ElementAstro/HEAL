"""
统一日志面板UI组件

提供完整的日志管理界面，包括：
- 实时日志查看
- 多级别日志过滤
- 日志搜索和导出
- 日志统计和健康监控
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QTextEdit, QComboBox, QLineEdit, QPushButton, QLabel,
    QCheckBox, QSpinBox, QDateTimeEdit, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QDateTime
from PySide6.QtGui import QFont, QTextCursor, QColor, QPalette

from qfluentwidgets import (
    FluentIcon as FIF, ScrollArea, PrimaryPushButton, PushButton,
    ComboBox, LineEdit, CheckBox, SpinBox, InfoBar, InfoBarPosition,
    CardWidget, HeaderCardWidget, BodyLabel, CaptionLabel, TitleLabel
)

from app.common.logging_config import (
    get_logger, get_log_stats, health_check, get_logging_config
)
from app.common.ui_utils import UIComponentManager
from .log_viewer import LogViewer
from .log_filter import LogFilter
from .log_exporter import LogExporter

logger = get_logger(__name__)


class LogPanel(ScrollArea):
    """统一日志面板主界面"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("LogPanel")
        
        # 初始化组件
        self.log_config = get_logging_config()
        self.log_viewer = None
        self.log_filter = None
        self.log_exporter = None
        
        # 设置界面
        self._setup_ui()
        self._setup_connections()
        self._start_monitoring()
        
        logger.info("日志面板初始化完成")
    
    def _setup_ui(self):
        """设置用户界面"""
        # 创建主容器
        self.scroll_widget = QWidget()
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        
        # 主布局
        main_layout = QVBoxLayout(self.scroll_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # 标题区域
        self._create_header_section(main_layout)
        
        # 统计信息区域
        self._create_stats_section(main_layout)
        
        # 主要内容区域 - 使用分割器
        self._create_main_content(main_layout)
        
        # 控制按钮区域
        self._create_control_section(main_layout)
    
    def _create_header_section(self, parent_layout: QVBoxLayout):
        """创建标题区域"""
        header_card = HeaderCardWidget(self.scroll_widget)
        header_card.setTitle("日志管理面板")
        # Note: setContent method may not be available in current QFluentWidgets version
        # Using a subtitle label instead
        subtitle_label = CaptionLabel("实时查看、过滤和管理应用程序日志")
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); margin: 8px 16px;")

        parent_layout.addWidget(header_card)
        parent_layout.addWidget(subtitle_label)
    
    def _create_stats_section(self, parent_layout: QVBoxLayout):
        """创建统计信息区域"""
        stats_frame = QFrame()
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        # 日志统计卡片
        self.stats_card = self._create_stats_card()
        stats_layout.addWidget(self.stats_card)
        
        # 健康状态卡片
        self.health_card = self._create_health_card()
        stats_layout.addWidget(self.health_card)
        
        # 磁盘使用卡片
        self.disk_card = self._create_disk_card()
        stats_layout.addWidget(self.disk_card)
        
        parent_layout.addWidget(stats_frame)
    
    def _create_stats_card(self) -> CardWidget:
        """创建日志统计卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        
        title = TitleLabel("日志统计")
        layout.addWidget(title)
        
        self.total_logs_label = BodyLabel("总日志数: 加载中...")
        self.error_logs_label = BodyLabel("错误日志: 加载中...")
        self.warning_logs_label = BodyLabel("警告日志: 加载中...")
        
        layout.addWidget(self.total_logs_label)
        layout.addWidget(self.error_logs_label)
        layout.addWidget(self.warning_logs_label)
        
        return card
    
    def _create_health_card(self) -> CardWidget:
        """创建健康状态卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        
        title = TitleLabel("系统健康")
        layout.addWidget(title)
        
        self.health_status_label = BodyLabel("状态: 检查中...")
        self.handlers_count_label = BodyLabel("处理器数量: 0")
        self.uptime_label = BodyLabel("运行时间: 0分钟")
        
        layout.addWidget(self.health_status_label)
        layout.addWidget(self.handlers_count_label)
        layout.addWidget(self.uptime_label)
        
        return card
    
    def _create_disk_card(self) -> CardWidget:
        """创建磁盘使用卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        
        title = TitleLabel("存储使用")
        layout.addWidget(title)
        
        self.disk_usage_label = BodyLabel("日志目录大小: 计算中...")
        self.available_space_label = BodyLabel("可用空间: 计算中...")
        
        # 进度条显示磁盘使用率
        self.disk_progress = QProgressBar()
        self.disk_progress.setMaximum(100)
        
        layout.addWidget(self.disk_usage_label)
        layout.addWidget(self.available_space_label)
        layout.addWidget(self.disk_progress)
        
        return card
    
    def _create_main_content(self, parent_layout: QVBoxLayout):
        """创建主要内容区域"""
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：日志查看器
        self.log_viewer = LogViewer()
        splitter.addWidget(self.log_viewer)
        
        # 右侧：过滤和控制面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 过滤器
        self.log_filter = LogFilter()
        right_layout.addWidget(self.log_filter)
        
        # 导出器
        self.log_exporter = LogExporter()
        right_layout.addWidget(self.log_exporter)
        
        splitter.addWidget(right_panel)
        
        # 设置分割器比例 (70% : 30%)
        splitter.setSizes([700, 300])
        
        parent_layout.addWidget(splitter)
    
    def _create_control_section(self, parent_layout: QVBoxLayout):
        """创建控制按钮区域"""
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        # 刷新按钮
        self.refresh_btn = PrimaryPushButton(FIF.SYNC, "刷新日志")
        control_layout.addWidget(self.refresh_btn)
        
        # 清理按钮
        self.cleanup_btn = PushButton(FIF.DELETE, "清理旧日志")
        control_layout.addWidget(self.cleanup_btn)
        
        # 归档按钮
        self.archive_btn = PushButton(FIF.FOLDER, "归档日志")
        control_layout.addWidget(self.archive_btn)
        
        # 设置按钮
        self.settings_btn = PushButton(FIF.SETTING, "日志设置")
        control_layout.addWidget(self.settings_btn)
        
        control_layout.addStretch()
        
        parent_layout.addWidget(control_frame)
    
    def _setup_connections(self):
        """设置信号连接"""
        if self.refresh_btn:
            self.refresh_btn.clicked.connect(self.refresh_logs)
        if self.cleanup_btn:
            self.cleanup_btn.clicked.connect(self.cleanup_logs)
        if self.archive_btn:
            self.archive_btn.clicked.connect(self.archive_logs)
        if self.settings_btn:
            self.settings_btn.clicked.connect(self.show_settings)
        
        # 连接过滤器和查看器
        if self.log_filter and self.log_viewer:
            self.log_filter.filter_changed.connect(self.log_viewer.apply_filter)
        
        # 连接导出器
        if self.log_exporter and self.log_viewer:
            self.log_exporter.export_requested.connect(self.log_viewer.export_logs)
    
    def _start_monitoring(self):
        """启动监控定时器"""
        # 统计信息更新定时器
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(5000)  # 每5秒更新一次
        
        # 立即更新一次
        self.update_stats()
    
    def update_stats(self):
        """更新统计信息"""
        try:
            # 获取日志统计
            stats = get_log_stats()
            if stats:
                log_counts = stats.get('log_counts', {})
                total = sum(log_counts.values())
                errors = log_counts.get('ERROR', 0)
                warnings = log_counts.get('WARNING', 0)
                
                self.total_logs_label.setText(f"总日志数: {total:,}")
                self.error_logs_label.setText(f"错误日志: {errors:,}")
                self.warning_logs_label.setText(f"警告日志: {warnings:,}")
            
            # 获取健康状态
            health = health_check()
            if health:
                status = health.get('status', 'unknown')
                handlers = health.get('handlers_count', 0)
                uptime = health.get('uptime_minutes', 0)
                
                self.health_status_label.setText(f"状态: {status}")
                self.handlers_count_label.setText(f"处理器数量: {handlers}")
                self.uptime_label.setText(f"运行时间: {uptime}分钟")
            
            # 更新磁盘使用情况
            self._update_disk_usage()
            
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    def _update_disk_usage(self):
        """更新磁盘使用情况"""
        try:
            log_dir = Path("logs")
            if log_dir.exists():
                # 计算日志目录大小
                total_size = sum(f.stat().st_size for f in log_dir.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                
                self.disk_usage_label.setText(f"日志目录大小: {size_mb:.1f} MB")
                
                # 获取可用空间
                import shutil
                _, _, free = shutil.disk_usage(log_dir)
                free_mb = free / (1024 * 1024)
                
                self.available_space_label.setText(f"可用空间: {free_mb:.1f} MB")
                
                # 计算使用率（假设总空间为可用空间+已用空间的估算）
                usage_percent = min(int((size_mb / (size_mb + free_mb)) * 100), 100)
                self.disk_progress.setValue(usage_percent)
                
        except Exception as e:
            logger.error(f"更新磁盘使用情况失败: {e}")
    
    def refresh_logs(self):
        """刷新日志"""
        if self.log_viewer:
            self.log_viewer.refresh()
        self.update_stats()
        InfoBar.success(
            title="刷新完成",
            content="日志已刷新",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def cleanup_logs(self):
        """清理旧日志"""
        try:
            from app.common.logging_config import cleanup_logs
            cleanup_logs()
            self.update_stats()
            InfoBar.success(
                title="清理完成",
                content="旧日志已清理",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            logger.error(f"清理日志失败: {e}")
            InfoBar.error(
                title="清理失败",
                content=f"清理日志时发生错误: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def archive_logs(self):
        """归档日志"""
        try:
            from app.common.logging_config import archive_logs
            archive_logs()
            self.update_stats()
            InfoBar.success(
                title="归档完成",
                content="日志已归档",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            logger.error(f"归档日志失败: {e}")
            InfoBar.error(
                title="归档失败",
                content=f"归档日志时发生错误: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def show_settings(self):
        """显示日志设置"""
        # TODO: 实现日志设置对话框
        InfoBar.info(
            title="功能开发中",
            content="日志设置功能正在开发中",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
