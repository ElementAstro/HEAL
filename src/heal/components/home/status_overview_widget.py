from datetime import datetime
from typing import Dict, List, Tuple

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import setCustomStyleSheet

from src.heal.common.i18n_ui import tr
from src.heal.common.logging_config import get_logger
from src.heal.models.config import cfg

logger = get_logger(__name__)


class StatusOverviewWidget(QFrame):
    """System-wide status overview and activity dashboard."""

    # Signals
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.server_statuses: Dict[str, str] = {}
        self.recent_activities: List[Tuple[datetime, str]] = []
        self.max_activities = 5

        self.logger = get_logger("status_overview", module="StatusOverviewWidget")

        self._init_ui()
        self._setup_styles()
        self._setup_refresh_timer()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setFixedHeight(100)
        self.setFrameStyle(QFrame.Shape.Box)

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(20)

        # Left side - System status summary
        status_layout = QVBoxLayout()
        status_layout.setSpacing(4)

        self.system_status_label = QLabel(tr("home.system_status"))
        self.system_status_label.setFont(QFont(cfg.APP_FONT, 11, QFont.Weight.Bold))

        self.status_summary_label = QLabel("0/0 Running")
        self.status_summary_label.setFont(QFont(cfg.APP_FONT, 10))

        # Server status indicators
        self.server_indicators_layout = QHBoxLayout()
        self.server_indicators_layout.setSpacing(12)

        status_layout.addWidget(self.system_status_label)
        status_layout.addWidget(self.status_summary_label)
        status_layout.addLayout(self.server_indicators_layout)

        # Right side - Recent activity
        activity_layout = QVBoxLayout()
        activity_layout.setSpacing(4)

        self.activity_label = QLabel(tr("home.recent_activity"))
        self.activity_label.setFont(QFont(cfg.APP_FONT, 11, QFont.Weight.Bold))

        # Activity scroll area
        self.activity_scroll = QScrollArea()
        self.activity_scroll.setFixedHeight(60)
        self.activity_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.activity_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.activity_scroll.setFrameStyle(QFrame.Shape.NoFrame)

        self.activity_widget = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_widget)
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(2)

        self.activity_scroll.setWidget(self.activity_widget)
        self.activity_scroll.setWidgetResizable(True)

        activity_layout.addWidget(self.activity_label)
        activity_layout.addWidget(self.activity_scroll)

        # Add to main layout
        main_layout.addLayout(status_layout, 1)
        main_layout.addWidget(self._create_separator())
        main_layout.addLayout(activity_layout, 1)

        # Initialize with empty state
        self._update_display()

    def _create_separator(self) -> QFrame:
        """Create a vertical separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedWidth(1)
        return separator

    def _setup_styles(self) -> None:
        """Setup custom styles for the widget."""
        widget_style = """
        StatusOverviewWidget {
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 6px;
            background-color: rgba(240, 248, 255, 0.8);
        }
        """
        setCustomStyleSheet(self, widget_style, widget_style)

    def _setup_refresh_timer(self) -> None:
        """Setup automatic refresh timer."""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_display)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def update_server_status(self, server_name: str, status: str) -> None:
        """Update the status of a specific server."""
        old_status = self.server_statuses.get(server_name, "unknown")
        self.server_statuses[server_name] = status

        # Add activity if status changed
        if old_status != status and old_status != "unknown":
            activity = f"{server_name}: {old_status} → {status}"
            self.add_activity(activity)

        self._update_display()
        self.logger.debug(f"Server status updated: {server_name} = {status}")

    def add_activity(self, activity: str) -> None:
        """Add a new activity to the recent activities list."""
        timestamp = datetime.now()
        self.recent_activities.insert(0, (timestamp, activity))

        # Keep only the most recent activities
        if len(self.recent_activities) > self.max_activities:
            self.recent_activities = self.recent_activities[: self.max_activities]

        self._update_activity_display()
        self.logger.debug(f"Activity added: {activity}")

    def _update_display(self) -> None:
        """Update the entire display."""
        self._update_status_summary()
        self._update_server_indicators()
        self._update_activity_display()

    def _update_status_summary(self) -> None:
        """Update the system status summary."""
        total_servers = len(self.server_statuses)
        running_servers = sum(
            1 for status in self.server_statuses.values() if status == "running"
        )

        self.status_summary_label.setText(f"{running_servers}/{total_servers} Running")

        # Color code the summary
        if total_servers == 0:
            color = "#9E9E9E"  # Gray - no servers
        elif running_servers == total_servers:
            color = "#4CAF50"  # Green - all running
        elif running_servers == 0:
            color = "#F44336"  # Red - none running
        else:
            color = "#FF9800"  # Orange - partial

        self.status_summary_label.setStyleSheet(f"QLabel {{ color: {color}; }}")

    def _update_server_indicators(self) -> None:
        """Update individual server status indicators."""
        # Clear existing indicators
        for i in reversed(range(self.server_indicators_layout.count())):
            child = self.server_indicators_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Add indicators for each server
        for server_name, status in self.server_statuses.items():
            indicator = self._create_server_indicator(server_name, status)
            self.server_indicators_layout.addWidget(indicator)

        # Add stretch to left-align indicators
        self.server_indicators_layout.addStretch()

    def _create_server_indicator(self, server_name: str, status: str) -> QLabel:
        """Create a status indicator for a specific server."""
        status_colors = {
            "stopped": "#9E9E9E",  # Gray
            "running": "#4CAF50",  # Green
            "error": "#F44336",  # Red
            "starting": "#FF9800",  # Orange
            "stopping": "#FF9800",  # Orange
        }

        color = status_colors.get(status, "#9E9E9E")

        indicator = QLabel(f"● {server_name}")
        indicator.setFont(QFont(cfg.APP_FONT, 9))
        indicator.setStyleSheet(f"QLabel {{ color: {color}; }}")
        indicator.setToolTip(f"{server_name}: {status.title()}")

        return indicator

    def _update_activity_display(self) -> None:
        """Update the recent activity display."""
        # Clear existing activity items
        for i in reversed(range(self.activity_layout.count())):
            child = self.activity_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Add recent activities
        if not self.recent_activities:
            no_activity_label = QLabel(tr("home.no_recent_activity"))
            no_activity_label.setFont(QFont(cfg.APP_FONT, 9))
            no_activity_label.setStyleSheet("QLabel { color: #9E9E9E; }")
            self.activity_layout.addWidget(no_activity_label)
        else:
            for timestamp, activity in self.recent_activities:
                activity_item = self._create_activity_item(timestamp, activity)
                self.activity_layout.addWidget(activity_item)

        # Add stretch to top-align items
        self.activity_layout.addStretch()

    def _create_activity_item(self, timestamp: datetime, activity: str) -> QLabel:
        """Create an activity item widget."""
        time_str = timestamp.strftime("%H:%M")
        text = f"{time_str} - {activity}"

        item = QLabel(text)
        item.setFont(QFont(cfg.APP_FONT, 8))
        item.setStyleSheet("QLabel { color: #666666; }")
        item.setWordWrap(True)

        return item

    def _refresh_display(self) -> None:
        """Refresh the display (called by timer)."""
        self._update_display()

    def clear_activities(self) -> None:
        """Clear all recent activities."""
        self.recent_activities.clear()
        self._update_activity_display()
        self.logger.info("Activities cleared")

    def get_system_summary(self) -> Dict[str, int]:
        """Get system status summary."""
        total = len(self.server_statuses)
        running = sum(
            1 for status in self.server_statuses.values() if status == "running"
        )
        stopped = sum(
            1 for status in self.server_statuses.values() if status == "stopped"
        )
        error = sum(1 for status in self.server_statuses.values() if status == "error")

        return {"total": total, "running": running, "stopped": stopped, "error": error}
