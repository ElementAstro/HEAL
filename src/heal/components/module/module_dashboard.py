"""
Module Dashboard

Unified dashboard with system health overview, quick actions panel, recent activity feed,
and comprehensive module management statistics and insights.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    ElevatedCardWidget,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    ProgressBar,
    PushButton,
    SimpleCardWidget,
    SubtitleLabel,
    TitleLabel,
)

from src.heal.common.logging_config import get_logger
from .module_bulk_operations import ModuleBulkOperations
from .module_error_handler import ModuleErrorHandler
from .module_metrics_manager import ModuleMetricsManager
from .module_notification_system import ModuleNotificationSystem
from .module_workflow_manager import ModuleWorkflowManager

logger = get_logger(__name__)


@dataclass
class DashboardStats:
    """Dashboard statistics"""

    total_modules: int = 0
    enabled_modules: int = 0
    disabled_modules: int = 0
    error_modules: int = 0
    active_workflows: int = 0
    pending_operations: int = 0
    recent_errors: int = 0
    system_health_score: float = 100.0


class QuickActionCard(SimpleCardWidget):
    """Quick action card widget"""

    action_triggered = Signal(str)  # action_id

    def __init__(
        self,
        title: str,
        description: str,
        icon: FluentIcon,
        action_id: str,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self.action_id = action_id
        self.setup_ui(title, description, icon)

    def setup_ui(self, title: str, description: str, icon: FluentIcon) -> None:
        """Setup the card UI"""
        self.setFixedSize(200, 120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        # Icon and title
        header_layout = QHBoxLayout()

        icon_label = QLabel()
        icon_label.setPixmap(icon.icon().pixmap(24, 24))
        header_layout.addWidget(icon_label)

        title_label = SubtitleLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Description
        desc_label = CaptionLabel(description)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

        # Action button
        action_button = PushButton("执行")
        action_button.clicked.connect(
            lambda: self.action_triggered.emit(self.action_id)
        )
        layout.addWidget(action_button)


class SystemHealthCard(ElevatedCardWidget):
    """System health overview card"""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setup_ui()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_health_data)
        self.update_timer.start(5000)  # Update every 5 seconds

    def setup_ui(self) -> None:
        """Setup the health card UI"""
        self.setFixedHeight(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = TitleLabel("系统健康状态")
        layout.addWidget(title_label)

        # Health metrics grid
        metrics_layout = QGridLayout()

        # Overall health score
        self.health_score_label = SubtitleLabel("100%")
        self.health_score_label.setStyleSheet(
            "color: #10b981; font-size: 24px; font-weight: bold;"
        )
        metrics_layout.addWidget(QLabel("健康评分:"), 0, 0)
        metrics_layout.addWidget(self.health_score_label, 0, 1)

        # Active modules
        self.active_modules_label = BodyLabel("0")
        metrics_layout.addWidget(QLabel("活跃模组:"), 1, 0)
        metrics_layout.addWidget(self.active_modules_label, 1, 1)

        # Error count
        self.error_count_label = BodyLabel("0")
        metrics_layout.addWidget(QLabel("错误数量:"), 2, 0)
        metrics_layout.addWidget(self.error_count_label, 2, 1)

        # Active workflows
        self.workflows_label = BodyLabel("0")
        metrics_layout.addWidget(QLabel("活跃工作流:"), 3, 0)
        metrics_layout.addWidget(self.workflows_label, 3, 1)

        layout.addLayout(metrics_layout)

        # Health progress bar
        self.health_progress = ProgressBar()
        self.health_progress.setValue(100)
        layout.addWidget(self.health_progress)

    def update_health_data(self, stats: Optional[DashboardStats] = None) -> None:
        """Update health display with new data"""
        if stats is None:
            # Generate mock data for now
            stats = DashboardStats(
                total_modules=10,
                enabled_modules=8,
                error_modules=1,
                active_workflows=2,
                system_health_score=85.0,
            )

        # Update health score
        health_score = int(stats.system_health_score)
        self.health_score_label.setText(f"{health_score}%")
        self.health_progress.setValue(health_score)

        # Update color based on health
        if health_score >= 80:
            color = "#10b981"  # Green
        elif health_score >= 60:
            color = "#f59e0b"  # Yellow
        else:
            color = "#ef4444"  # Red

        self.health_score_label.setStyleSheet(
            f"color: {color}; font-size: 24px; font-weight: bold;"
        )

        # Update other metrics
        self.active_modules_label.setText(str(stats.enabled_modules))
        self.error_count_label.setText(str(stats.error_modules))
        self.workflows_label.setText(str(stats.active_workflows))


class RecentActivityCard(ElevatedCardWidget):
    """Recent activity feed card"""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.activities: List[Dict[str, Any]] = []
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the activity card UI"""
        self.setMinimumHeight(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = TitleLabel("最近活动")
        layout.addWidget(title_label)

        # Activity list
        self.activity_scroll = QScrollArea()
        self.activity_scroll.setWidgetResizable(True)
        self.activity_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.activity_widget = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_widget)
        self.activity_layout.setSpacing(8)

        self.activity_scroll.setWidget(self.activity_widget)
        layout.addWidget(self.activity_scroll)

        # Add some sample activities
        self.add_activity("模组启用", "成功启用模组 'TestMod'", "success")
        self.add_activity("工作流完成", "模组 'AnotherMod' 安装完成", "info")
        self.add_activity("验证警告", "模组 'ProblematicMod' 验证发现问题", "warning")

    def add_activity(self, title: str, description: str, activity_type: str = "info") -> None:
        """Add new activity to the feed"""
        activity_frame = QFrame()
        activity_frame.setStyleSheet(
            """
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
            }
        """
        )

        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setContentsMargins(10, 8, 10, 8)
        activity_layout.setSpacing(4)

        # Header with icon and title
        header_layout = QHBoxLayout()

        # Icon based on type
        icon_label = QLabel()
        if activity_type == "success":
            icon_label.setPixmap(FluentIcon.ACCEPT.icon().pixmap(16, 16))
        elif activity_type == "warning":
            icon_label.setPixmap(FluentIcon.WARNING.icon().pixmap(16, 16))
        elif activity_type == "error":
            icon_label.setPixmap(FluentIcon.CLOSE.icon().pixmap(16, 16))
        else:
            icon_label.setPixmap(FluentIcon.INFO.icon().pixmap(16, 16))

        header_layout.addWidget(icon_label)

        title_label = BodyLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Timestamp
        timestamp_label = CaptionLabel(time.strftime("%H:%M"))
        timestamp_label.setStyleSheet("color: #666;")
        header_layout.addWidget(timestamp_label)

        activity_layout.addLayout(header_layout)

        # Description
        desc_label = CaptionLabel(description)
        desc_label.setWordWrap(True)
        activity_layout.addWidget(desc_label)

        # Add to top of list
        self.activity_layout.insertWidget(0, activity_frame)

        # Limit number of activities
        if self.activity_layout.count() > 20:
            item = self.activity_layout.takeAt(20)
            if item.widget():
                item.widget().deleteLater()


class ModuleDashboard(QWidget):
    """Main module dashboard widget"""

    # Signals
    quick_action_triggered = Signal(str)  # action_id

    def __init__(
        self,
        workflow_manager: ModuleWorkflowManager,
        error_handler: ModuleErrorHandler,
        notification_system: ModuleNotificationSystem,
        bulk_operations: ModuleBulkOperations,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self.logger = logger.bind(component="ModuleDashboard")

        # System references
        self.workflow_manager = workflow_manager
        self.error_handler = error_handler
        self.notification_system = notification_system
        self.bulk_operations = bulk_operations

        # Dashboard data
        self.current_stats = DashboardStats()

        self.setup_ui()
        self.setup_connections()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard_data)
        self.update_timer.start(10000)  # Update every 10 seconds

        self.logger.info("Module Dashboard initialized")

    def setup_ui(self) -> None:
        """Setup the dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title_label = TitleLabel("模组管理仪表板")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - System health and quick actions
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(20)

        # System health card
        self.health_card = SystemHealthCard()
        left_layout.addWidget(self.health_card)

        # Quick actions
        actions_label = SubtitleLabel("快速操作")
        left_layout.addWidget(actions_label)

        actions_grid = QGridLayout()
        actions_grid.setSpacing(15)

        # Create quick action cards
        quick_actions = [
            ("刷新模组", "重新加载所有模组", FluentIcon.SYNC, "refresh_modules"),
            ("批量验证", "验证所有模组", FluentIcon.CERTIFICATE, "validate_all"),
            (
                "系统检查",
                "检查系统健康状态",
                FluentIcon.CARE_RIGHT_SOLID,
                "system_check",
            ),
            ("清理缓存", "清理临时文件", FluentIcon.BROOM, "cleanup_cache"),
            ("导出报告", "导出系统报告", FluentIcon.SAVE, "export_report"),
            ("设置", "打开系统设置", FluentIcon.SETTING, "open_settings"),
        ]

        for i, (title, desc, icon, action_id) in enumerate(quick_actions):
            card = QuickActionCard(title, desc, icon, action_id)
            card.action_triggered.connect(self.quick_action_triggered.emit)
            actions_grid.addWidget(card, i // 2, i % 2)

        left_layout.addLayout(actions_grid)
        left_layout.addStretch()

        main_splitter.addWidget(left_panel)

        # Right panel - Recent activity and statistics
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(20)

        # Recent activity card
        self.activity_card = RecentActivityCard()
        right_layout.addWidget(self.activity_card)

        # Statistics cards
        stats_label = SubtitleLabel("统计信息")
        right_layout.addWidget(stats_label)

        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)

        # Module statistics
        self.total_modules_card = self.create_stat_card(
            "总模组数", "0", FluentIcon.FOLDER
        )
        self.enabled_modules_card = self.create_stat_card(
            "已启用", "0", FluentIcon.ACCEPT
        )
        self.error_modules_card = self.create_stat_card(
            "错误模组", "0", FluentIcon.CLOSE
        )
        self.workflows_card = self.create_stat_card("活跃工作流", "0", FluentIcon.PLAY)

        stats_layout.addWidget(self.total_modules_card, 0, 0)
        stats_layout.addWidget(self.enabled_modules_card, 0, 1)
        stats_layout.addWidget(self.error_modules_card, 1, 0)
        stats_layout.addWidget(self.workflows_card, 1, 1)

        right_layout.addLayout(stats_layout)
        right_layout.addStretch()

        main_splitter.addWidget(right_panel)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)

        layout.addWidget(main_splitter)

    def create_stat_card(
        self, title: str, value: str, icon: FluentIcon
    ) -> SimpleCardWidget:
        """Create a statistics card"""
        card = SimpleCardWidget()
        card.setFixedSize(150, 100)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        # Icon and title
        header_layout = QHBoxLayout()

        icon_label = QLabel()
        icon_label.setPixmap(icon.icon().pixmap(20, 20))
        header_layout.addWidget(icon_label)

        title_label = CaptionLabel(title)
        header_layout.addWidget(title_label)

        layout.addLayout(header_layout)

        # Value
        value_label = TitleLabel(value)
        value_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        # Store value label for updates
        card.value_label = value_label

        return card

    def setup_connections(self) -> None:
        """Setup signal connections"""
        # Connect to system events
        self.workflow_manager.workflow_completed.connect(self._on_workflow_completed)
        self.workflow_manager.workflow_step_failed.connect(self._on_workflow_failed)
        self.bulk_operations.operation_completed.connect(
            self._on_bulk_operation_completed
        )
        self.error_handler.error_occurred.connect(self._on_error_occurred)

    def update_dashboard_data(self) -> None:
        """Update dashboard with current data"""
        try:
            # Collect statistics
            stats = DashboardStats()

            # Get workflow statistics
            active_workflows = self.workflow_manager.get_active_workflows()
            stats.active_workflows = len(active_workflows)

            # Get error statistics
            recent_errors = self.error_handler.get_recent_errors(hours=24)
            stats.recent_errors = len(recent_errors)

            # Get bulk operation statistics
            active_operations = self.bulk_operations.get_active_operations()
            stats.pending_operations = len(active_operations)

            # Calculate health score
            stats.system_health_score = self._calculate_health_score(stats)

            # Update UI
            self.current_stats = stats
            self._update_statistics_display()
            self.health_card.update_health_data(stats)

        except Exception as e:
            self.logger.error(f"Error updating dashboard data: {e}")

    def _calculate_health_score(self, stats: DashboardStats) -> float:
        """Calculate system health score"""
        base_score = 100.0

        # Deduct points for errors
        if stats.recent_errors > 0:
            base_score -= min(stats.recent_errors * 5, 30)

        # Deduct points for failed modules
        if stats.error_modules > 0:
            base_score -= min(stats.error_modules * 10, 40)

        # Bonus for active workflows (shows system is being used)
        if stats.active_workflows > 0:
            base_score += min(stats.active_workflows * 2, 10)

        return max(0.0, min(100.0, base_score))

    def _update_statistics_display(self) -> None:
        """Update statistics cards"""
        stats = self.current_stats

        self.total_modules_card.value_label.setText(str(stats.total_modules))
        self.enabled_modules_card.value_label.setText(str(stats.enabled_modules))
        self.error_modules_card.value_label.setText(str(stats.error_modules))
        self.workflows_card.value_label.setText(str(stats.active_workflows))

    def add_activity(self, title: str, description: str, activity_type: str = "info") -> None:
        """Add activity to the feed"""
        self.activity_card.add_activity(title, description, activity_type)

    # Event handlers
    def _on_workflow_completed(self, workflow_id: str) -> None:
        """Handle workflow completion"""
        workflow = self.workflow_manager.get_workflow(workflow_id)
        if workflow:
            self.add_activity(
                "工作流完成", f"模组 '{workflow.module_name}' 工作流已完成", "success"
            )

    def _on_workflow_failed(self, workflow_id: str, step: str, error: str) -> None:
        """Handle workflow failure"""
        workflow = self.workflow_manager.get_workflow(workflow_id)
        if workflow:
            self.add_activity(
                "工作流失败", f"模组 '{workflow.module_name}' 在{step}步骤失败", "error"
            )

    def _on_bulk_operation_completed(self, operation_id: str, success: bool) -> None:
        """Handle bulk operation completion"""
        operation = self.bulk_operations.get_operation(operation_id)
        if operation:
            activity_type = "success" if success else "error"
            self.add_activity(
                "批量操作完成",
                f"批量{operation.operation_type.value}操作已完成",
                activity_type,
            )

    def _on_error_occurred(self, error_id: str) -> None:
        """Handle error occurrence"""
        error = self.error_handler.get_error(error_id)
        if error:
            self.add_activity("系统错误", error.user_friendly_message, "error")
