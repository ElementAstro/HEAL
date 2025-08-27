"""
Download Management Panel
Provides a comprehensive download management interface
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    Pivot,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    ScrollArea,
    SegmentedWidget,
    StrongBodyLabel,
    ToolButton,
)

from src.heal.common.i18n import t
from src.heal.common.logging_config import get_logger
from src.heal.models.download_manager import DownloadItem, DownloadManager, DownloadStatus
from src.heal.components.monitoring.download_monitor import DownloadItemCard, DownloadManagerWidget


class DownloadStatsCard(CardWidget):
    """下载统计卡片"""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI"""
        self.setFixedHeight(120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # 标题
        title_label = StrongBodyLabel("下载统计")
        layout.addWidget(title_label)

        # 统计信息布局
        stats_layout = QHBoxLayout()

        # 总下载数
        self.total_label = BodyLabel("总计: 0")
        stats_layout.addWidget(self.total_label)

        # 进行中
        self.active_label = BodyLabel("进行中: 0")
        stats_layout.addWidget(self.active_label)

        # 已完成
        self.completed_label = BodyLabel("已完成: 0")
        stats_layout.addWidget(self.completed_label)

        # 失败
        self.failed_label = BodyLabel("失败: 0")
        stats_layout.addWidget(self.failed_label)

        layout.addLayout(stats_layout)

        # 总体进度
        self.overall_progress = ProgressBar()
        self.overall_progress.setVisible(False)
        layout.addWidget(self.overall_progress)

    def update_stats(self, stats: Dict[str, int]) -> None:
        """更新统计信息"""
        self.total_label.setText(f"总计: {stats.get('total', 0)}")
        self.active_label.setText(f"进行中: {stats.get('active', 0)}")
        self.completed_label.setText(f"已完成: {stats.get('completed', 0)}")
        self.failed_label.setText(f"失败: {stats.get('failed', 0)}")

        # 显示总体进度
        if stats.get("active", 0) > 0:
            self.overall_progress.setVisible(True)
            progress = stats.get("completed", 0) / \
                max(stats.get("total", 1), 1) * 100
            self.overall_progress.setValue(int(progress))
        else:
            self.overall_progress.setVisible(False)


class QuickDownloadCard(CardWidget):
    """快速下载卡片"""

    download_requested = Signal(str, str)  # name, url

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI"""
        self.setFixedHeight(100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # 标题
        title_label = StrongBodyLabel("快速下载")
        layout.addWidget(title_label)

        # 快速下载按钮布局
        buttons_layout = QHBoxLayout()

        # 常用下载按钮
        self.git_btn = PushButton("Git")
        self.git_btn.setIcon(FluentIcon.CODE)
        self.git_btn.clicked.connect(
            lambda: self.download_requested.emit(
                "Git", "https://git-scm.com/download/win"
            )
        )

        self.python_btn = PushButton("Python")
        self.python_btn.setIcon(FluentIcon.DEVELOPER_TOOLS)
        self.python_btn.clicked.connect(
            lambda: self.download_requested.emit(
                "Python", "https://www.python.org/downloads/"
            )
        )

        self.nodejs_btn = PushButton("Node.js")
        self.nodejs_btn.setIcon(FluentIcon.GLOBE)
        self.nodejs_btn.clicked.connect(
            lambda: self.download_requested.emit(
                "Node.js", "https://nodejs.org/en/download/"
            )
        )

        buttons_layout.addWidget(self.git_btn)
        buttons_layout.addWidget(self.python_btn)
        buttons_layout.addWidget(self.nodejs_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)


class DownloadHistoryWidget(QWidget):
    """下载历史组件"""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.init_ui()
        self.download_history: List[Dict] = []

    def init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 标题和控制
        header_layout = QHBoxLayout()
        title_label = StrongBodyLabel("下载历史")
        clear_btn = ToolButton(FluentIcon.DELETE)
        clear_btn.setToolTip("清除历史")
        clear_btn.clicked.connect(self.clear_history)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # 历史列表
        self.scroll_area = ScrollArea()
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.scroll_area.setWidget(self.history_widget)
        self.scroll_area.setWidgetResizable(True)

        layout.addWidget(self.scroll_area)

    def add_history_item(self, item: Dict) -> None:
        """添加历史项目"""
        self.download_history.insert(0, item)  # 最新的在前面
        if len(self.download_history) > 50:  # 保持最近50个
            self.download_history.pop()
        self.refresh_history()

    def refresh_history(self) -> None:
        """刷新历史显示"""
        # 清除现有项目
        for i in reversed(range(self.history_layout.count())):
            child = self.history_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # 添加历史项目
        for item in self.download_history[:20]:  # 显示最近20个
            history_card = self.create_history_card(item)
            self.history_layout.addWidget(history_card)

        self.history_layout.addStretch()

    def create_history_card(self, item: Dict) -> CardWidget:
        """创建历史卡片"""
        card = CardWidget()
        card.setFixedHeight(60)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)

        # 信息
        info_layout = QVBoxLayout()
        name_label = BodyLabel(item.get("name", "未知"))
        time_label = CaptionLabel(item.get("time", ""))

        info_layout.addWidget(name_label)
        info_layout.addWidget(time_label)

        # 状态
        status = item.get("status", "unknown")
        status_icon = {
            "completed": FluentIcon.ACCEPT,
            "failed": FluentIcon.CANCEL,
            "cancelled": FluentIcon.CLOSE,
        }.get(status, FluentIcon.INFO)

        status_btn = ToolButton(status_icon)
        status_btn.setEnabled(False)

        layout.addLayout(info_layout, 1)
        layout.addWidget(status_btn)

        return card

    def clear_history(self) -> None:
        """清除历史"""
        self.download_history.clear()
        self.refresh_history()


class DownloadPanel(QWidget):
    """下载管理面板"""

    download_requested = Signal(str, str)  # name, url

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = get_logger("download_panel", module="DownloadPanel")

        # 创建下载管理器实例
        self.download_manager = DownloadManager()

        self.init_ui()

        # 定时器用于更新统计
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(2000)  # 每2秒更新一次

    def init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建分段控件
        self.segment_widget = SegmentedWidget()
        self.segment_widget.addItem(
            "overview", "概览", lambda: self.switch_view(0))
        self.segment_widget.addItem(
            "active", "进行中", lambda: self.switch_view(1))
        self.segment_widget.addItem(
            "history", "历史", lambda: self.switch_view(2))
        self.segment_widget.setCurrentItem("overview")

        layout.addWidget(self.segment_widget)

        # 创建堆叠组件
        self.stacked_widget = QStackedWidget()

        # 概览页面
        overview_widget = self.create_overview_widget()
        self.stacked_widget.addWidget(overview_widget)

        # 进行中页面
        self.download_monitor = DownloadManagerWidget(self.download_manager)
        self.stacked_widget.addWidget(self.download_monitor)

        # 历史页面
        self.history_widget = DownloadHistoryWidget()
        self.stacked_widget.addWidget(self.history_widget)

        layout.addWidget(self.stacked_widget)

        # 连接信号
        self.download_monitor.download_completed_signal.connect(
            self.on_download_completed
        )

    def create_overview_widget(self) -> QWidget:
        """创建概览组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 统计卡片
        self.stats_card = DownloadStatsCard()
        layout.addWidget(self.stats_card)

        # 快速下载卡片
        self.quick_download_card = QuickDownloadCard()
        self.quick_download_card.download_requested.connect(
            self.download_requested)
        layout.addWidget(self.quick_download_card)

        layout.addStretch()
        return widget

    def switch_view(self, index: int) -> None:
        """切换视图"""
        self.stacked_widget.setCurrentIndex(index)

    def update_stats(self) -> None:
        """更新统计信息"""
        # 这里应该从实际的下载管理器获取统计信息
        # 暂时使用模拟数据
        stats = {"total": 10, "active": 2, "completed": 7, "failed": 1}
        self.stats_card.update_stats(stats)

    def on_download_completed(self, download_item: Any) -> None:
        """下载完成处理"""
        from datetime import datetime

        history_item = {
            "name": Path(download_item.file_path).name,
            "status": (
                "completed"
                if download_item.status == DownloadStatus.COMPLETED
                else "failed"
            ),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "size": download_item.file_size,
        }

        self.history_widget.add_history_item(history_item)
        self.logger.info(f"下载完成: {history_item['name']}")
