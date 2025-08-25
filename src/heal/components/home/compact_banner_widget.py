from datetime import datetime
from typing import List, Optional

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import setCustomStyleSheet

from src.heal.common.i18n_ui import tr
from src.heal.common.logging_config import get_logger
from src.heal.models.config import cfg

logger = get_logger(__name__)


class CompactBannerWidget(QFrame):
    """Compact banner widget replacing the large flip view with functional information."""

    # Signals
    banner_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_tip_index = 0
        self.tips_list = [
            tr("home.tip_server_management"),
            tr("home.tip_quick_actions"),
            tr("home.tip_status_monitoring"),
            tr("home.tip_context_menus"),
            tr("home.tip_keyboard_shortcuts"),
        ]

        self.logger = get_logger("compact_banner", module="CompactBannerWidget")

        self._init_ui()
        self._setup_styles()
        self._setup_tip_rotation()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setFixedHeight(120)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 12, 20, 12)
        main_layout.setSpacing(20)

        # Left side - App branding and info
        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)

        # App title
        self.app_title = QLabel(cfg.APP_NAME)
        self.app_title.setFont(QFont(cfg.APP_FONT, 16, QFont.Weight.Bold))
        self.app_title.setStyleSheet("QLabel { color: #2C3E50; }")

        # App subtitle/version
        self.app_subtitle = QLabel(
            f"Version {cfg.APP_VERSION} - Server Management Dashboard"
        )
        self.app_subtitle.setFont(QFont(cfg.APP_FONT, 10))
        self.app_subtitle.setStyleSheet("QLabel { color: #7F8C8D; }")

        # Current time
        self.time_label = QLabel()
        self.time_label.setFont(QFont(cfg.APP_FONT, 9))
        self.time_label.setStyleSheet("QLabel { color: #95A5A6; }")
        self._update_time()

        left_layout.addWidget(self.app_title)
        left_layout.addWidget(self.app_subtitle)
        left_layout.addStretch()
        left_layout.addWidget(self.time_label)

        # Center - Rotating tips/information
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tip_title = QLabel(tr("home.tip_title"))
        self.tip_title.setFont(QFont(cfg.APP_FONT, 11, QFont.Weight.Bold))
        self.tip_title.setStyleSheet("QLabel { color: #34495E; }")
        self.tip_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tip_content = QLabel()
        self.tip_content.setFont(QFont(cfg.APP_FONT, 10))
        self.tip_content.setStyleSheet("QLabel { color: #5D6D7E; }")
        self.tip_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tip_content.setWordWrap(True)
        self.tip_content.setMaximumWidth(300)

        center_layout.addWidget(self.tip_title)
        center_layout.addWidget(self.tip_content)

        # Right side - System status and quick info
        right_layout = QVBoxLayout()
        right_layout.setSpacing(4)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # System status
        self.system_status_title = QLabel(tr("home.system_status"))
        self.system_status_title.setFont(QFont(cfg.APP_FONT, 11, QFont.Weight.Bold))
        self.system_status_title.setStyleSheet("QLabel { color: #2C3E50; }")

        self.system_status_info = QLabel("Ready")
        self.system_status_info.setFont(QFont(cfg.APP_FONT, 10))
        self.system_status_info.setStyleSheet("QLabel { color: #27AE60; }")

        # Quick stats
        self.stats_label = QLabel("0 servers configured")
        self.stats_label.setFont(QFont(cfg.APP_FONT, 9))
        self.stats_label.setStyleSheet("QLabel { color: #7F8C8D; }")

        right_layout.addWidget(self.system_status_title)
        right_layout.addWidget(self.system_status_info)
        right_layout.addStretch()
        right_layout.addWidget(self.stats_label)

        # Add layouts to main
        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self._create_separator())
        main_layout.addLayout(center_layout, 1)
        main_layout.addWidget(self._create_separator())
        main_layout.addLayout(right_layout, 1)

        # Initialize display
        self._update_tip_display()

    def _create_separator(self) -> QFrame:
        """Create a vertical separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedWidth(1)
        separator.setStyleSheet("QFrame { color: rgba(0, 0, 0, 0.1); }")
        return separator

    def _setup_styles(self) -> None:
        """Setup custom styles for the banner."""
        banner_style = """
        CompactBannerWidget {
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(240, 248, 255, 0.9),
                stop:1 rgba(230, 240, 250, 0.9));
        }
        CompactBannerWidget:hover {
            border: 1px solid rgba(0, 0, 0, 0.2);
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(245, 250, 255, 0.95),
                stop:1 rgba(235, 245, 255, 0.95));
        }
        """
        setCustomStyleSheet(self, banner_style, banner_style)

    def _setup_tip_rotation(self) -> None:
        """Setup automatic tip rotation timer."""
        self.tip_timer = QTimer(self)
        self.tip_timer.timeout.connect(self._rotate_tip)
        self.tip_timer.start(8000)  # Change tip every 8 seconds

        # Time update timer
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)  # Update time every second

    def _rotate_tip(self) -> None:
        """Rotate to the next tip."""
        if self.tips_list:
            self.current_tip_index = (self.current_tip_index + 1) % len(self.tips_list)
            self._update_tip_display()

    def _update_tip_display(self) -> None:
        """Update the tip display with current tip."""
        if self.tips_list and self.current_tip_index < len(self.tips_list):
            tip = self.tips_list[self.current_tip_index]
            self.tip_content.setText(tip)

            # Add fade effect for tip changes
            self._fade_tip_content()

    def _fade_tip_content(self) -> None:
        """Add a subtle fade effect when changing tips."""
        effect = QGraphicsOpacityEffect()
        self.tip_content.setGraphicsEffect(effect)

        # Simple opacity animation (would be enhanced with QPropertyAnimation in full implementation)
        effect.setOpacity(0.7)
        QTimer.singleShot(100, lambda: effect.setOpacity(1.0))

    def _update_time(self) -> None:
        """Update the current time display."""
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.time_label.setText(f"{current_date} {current_time}")

    def update_system_status(self, status: str, color: str = "#27AE60") -> None:
        """Update the system status display."""
        self.system_status_info.setText(status)
        self.system_status_info.setStyleSheet(f"QLabel {{ color: {color}; }}")
        self.logger.debug(f"System status updated: {status}")

    def update_stats(self, stats_text: str) -> None:
        """Update the statistics display."""
        self.stats_label.setText(stats_text)
        self.logger.debug(f"Stats updated: {stats_text}")

    def add_custom_tip(self, tip: str) -> None:
        """Add a custom tip to the rotation."""
        if tip not in self.tips_list:
            self.tips_list.append(tip)
            self.logger.debug(f"Custom tip added: {tip}")

    def remove_custom_tip(self, tip: str) -> None:
        """Remove a custom tip from the rotation."""
        if tip in self.tips_list:
            self.tips_list.remove(tip)
            # Adjust current index if necessary
            if self.current_tip_index >= len(self.tips_list):
                self.current_tip_index = 0
            self._update_tip_display()
            self.logger.debug(f"Custom tip removed: {tip}")

    def set_tips_list(self, tips: List[str]) -> None:
        """Set a new list of tips."""
        self.tips_list = tips
        self.current_tip_index = 0
        self._update_tip_display()
        self.logger.debug(f"Tips list updated with {len(tips)} tips")

    def mousePressEvent(self, event) -> None:
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.banner_clicked.emit()
            self.logger.debug("Banner clicked")
        super().mousePressEvent(event)

    def pause_tip_rotation(self) -> None:
        """Pause the automatic tip rotation."""
        self.tip_timer.stop()
        self.logger.debug("Tip rotation paused")

    def resume_tip_rotation(self) -> None:
        """Resume the automatic tip rotation."""
        self.tip_timer.start(8000)
        self.logger.debug("Tip rotation resumed")

    def get_current_info(self) -> dict:
        """Get current banner information."""
        return {
            "app_name": self.app_title.text(),
            "app_subtitle": self.app_subtitle.text(),
            "current_time": self.time_label.text(),
            "system_status": self.system_status_info.text(),
            "stats": self.stats_label.text(),
            "current_tip": self.tip_content.text(),
            "tip_index": self.current_tip_index,
            "total_tips": len(self.tips_list),
        }
