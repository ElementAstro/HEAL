from typing import List, Optional
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QFrame, QSizePolicy
from PySide6.QtGui import QFont
from qfluentwidgets import (PrimaryPushButton, PushButton, ToolButton,
                           FluentIcon, setCustomStyleSheet, ToolTip)
from app.model.config import cfg
from app.common.i18n_ui import tr
from app.common.logging_config import get_logger

logger = get_logger(__name__)


class QuickActionBar(QFrame):
    """Quick action bar with frequently used server management actions."""
    
    # Signals
    start_all_requested = Signal()
    stop_all_requested = Signal()
    refresh_requested = Signal()
    view_logs_requested = Signal()
    settings_requested = Signal()
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.running_servers_count = 0
        self.total_servers_count = 0
        
        self.logger = get_logger('quick_action_bar', module='QuickActionBar')
        
        self._init_ui()
        self._setup_styles()
        self._connect_signals()
        
    def _init_ui(self):
        """Initialize the user interface."""
        self.setFixedHeight(50)
        self.setFrameStyle(QFrame.Shape.Box)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(12)
        
        # Primary actions (left side)
        self.start_all_btn = PrimaryPushButton(FluentIcon.PLAY_SOLID, tr("home.start_all"))
        self.start_all_btn.setFixedSize(100, 34)
        self.start_all_btn.setIconSize(QSize(16, 16))
        self.start_all_btn.setFont(QFont(cfg.APP_FONT, 10))
        
        self.stop_all_btn = PushButton(FluentIcon.PAUSE_BOLD, tr("home.stop_all"))
        self.stop_all_btn.setFixedSize(100, 34)
        self.stop_all_btn.setIconSize(QSize(16, 16))
        self.stop_all_btn.setFont(QFont(cfg.APP_FONT, 10))
        
        # Secondary actions (middle)
        self.refresh_btn = PushButton(FluentIcon.SYNC, tr("home.refresh"))
        self.refresh_btn.setFixedSize(80, 34)
        self.refresh_btn.setIconSize(QSize(16, 16))
        self.refresh_btn.setFont(QFont(cfg.APP_FONT, 10))
        
        self.logs_btn = PushButton(FluentIcon.DOCUMENT, tr("home.view_logs"))
        self.logs_btn.setFixedSize(90, 34)
        self.logs_btn.setIconSize(QSize(16, 16))
        self.logs_btn.setFont(QFont(cfg.APP_FONT, 10))
        
        # Utility actions (right side)
        self.settings_btn = ToolButton(FluentIcon.SETTING)
        self.settings_btn.setFixedSize(34, 34)
        self.settings_btn.setIconSize(QSize(18, 18))
        self.settings_btn.setToolTip(tr("home.settings"))
        
        # Add widgets to layout
        main_layout.addWidget(self.start_all_btn)
        main_layout.addWidget(self.stop_all_btn)
        main_layout.addWidget(self._create_separator())
        main_layout.addWidget(self.refresh_btn)
        main_layout.addWidget(self.logs_btn)
        main_layout.addStretch()  # Push settings button to the right
        main_layout.addWidget(self.settings_btn)
        
        # Initial button state update
        self._update_button_states()
        
    def _create_separator(self) -> QFrame:
        """Create a vertical separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedWidth(1)
        separator.setFixedHeight(24)
        return separator
        
    def _setup_styles(self):
        """Setup custom styles for the action bar."""
        bar_style = """
        QuickActionBar {
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 6px;
            background-color: rgba(248, 249, 250, 0.9);
        }
        """
        setCustomStyleSheet(self, bar_style, bar_style)
        
        # Custom button styles
        button_style = """
        PushButton {
            border-radius: 4px;
            padding: 2px 8px;
        }
        PrimaryPushButton {
            border-radius: 4px;
            padding: 2px 8px;
        }
        """
        
        for btn in [self.start_all_btn, self.stop_all_btn, self.refresh_btn, self.logs_btn]:
            setCustomStyleSheet(btn, button_style, button_style)
            
    def _connect_signals(self):
        """Connect button signals to corresponding actions."""
        self.start_all_btn.clicked.connect(self._on_start_all_clicked)
        self.stop_all_btn.clicked.connect(self._on_stop_all_clicked)
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        self.logs_btn.clicked.connect(self._on_logs_clicked)
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        
    def _on_start_all_clicked(self):
        """Handle start all button click."""
        self.logger.info("Start all servers requested")
        self.start_all_requested.emit()
        
    def _on_stop_all_clicked(self):
        """Handle stop all button click."""
        self.logger.info("Stop all servers requested")
        self.stop_all_requested.emit()
        
    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        self.logger.info("Refresh requested")
        self.refresh_requested.emit()
        
        # Visual feedback for refresh action
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText(tr("home.refreshing"))
        
        # Re-enable after a short delay (would be handled by actual refresh completion)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, self._reset_refresh_button)
        
    def _reset_refresh_button(self):
        """Reset refresh button to normal state."""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText(tr("home.refresh"))
        
    def _on_logs_clicked(self):
        """Handle view logs button click."""
        self.logger.info("View logs requested")
        self.view_logs_requested.emit()
        
    def _on_settings_clicked(self):
        """Handle settings button click."""
        self.logger.info("Settings requested")
        self.settings_requested.emit()
        
    def update_server_counts(self, running_count: int, total_count: int):
        """Update server counts and refresh button states."""
        self.running_servers_count = running_count
        self.total_servers_count = total_count
        
        self._update_button_states()
        self._update_button_tooltips()
        
        self.logger.debug(f"Server counts updated: {running_count}/{total_count}")
        
    def _update_button_states(self):
        """Update button enabled/disabled states based on server status."""
        has_servers = self.total_servers_count > 0
        has_stopped_servers = (self.total_servers_count - self.running_servers_count) > 0
        has_running_servers = self.running_servers_count > 0
        
        # Start All: enabled if there are stopped servers
        self.start_all_btn.setEnabled(has_servers and has_stopped_servers)
        
        # Stop All: enabled if there are running servers
        self.stop_all_btn.setEnabled(has_running_servers)
        
        # Other buttons are always enabled
        self.refresh_btn.setEnabled(True)
        self.logs_btn.setEnabled(True)
        self.settings_btn.setEnabled(True)
        
    def _update_button_tooltips(self):
        """Update button tooltips with current status information."""
        if self.total_servers_count == 0:
            start_tooltip = tr("home.no_servers_configured")
            stop_tooltip = tr("home.no_servers_configured")
        else:
            stopped_count = self.total_servers_count - self.running_servers_count
            start_tooltip = tr("home.start_all_tooltip").format(count=stopped_count)
            stop_tooltip = tr("home.stop_all_tooltip").format(count=self.running_servers_count)
            
        self.start_all_btn.setToolTip(start_tooltip)
        self.stop_all_btn.setToolTip(stop_tooltip)
        
        # Static tooltips for other buttons
        self.refresh_btn.setToolTip(tr("home.refresh_tooltip"))
        self.logs_btn.setToolTip(tr("home.logs_tooltip"))
        
    def set_loading_state(self, is_loading: bool):
        """Set the action bar to loading state (disable buttons during operations)."""
        buttons = [self.start_all_btn, self.stop_all_btn, self.refresh_btn]
        
        for button in buttons:
            button.setEnabled(not is_loading)
            
        if is_loading:
            self.logger.debug("Action bar set to loading state")
        else:
            self.logger.debug("Action bar loading state cleared")
            self._update_button_states()  # Restore proper states
            
    def highlight_action(self, action: str, duration: int = 2000):
        """Temporarily highlight a specific action button."""
        button_map = {
            "start_all": self.start_all_btn,
            "stop_all": self.stop_all_btn,
            "refresh": self.refresh_btn,
            "logs": self.logs_btn,
            "settings": self.settings_btn
        }
        
        button = button_map.get(action)
        if not button:
            return
            
        # Store original style
        original_style = button.styleSheet()
        
        # Apply highlight style
        highlight_style = original_style + """
        QPushButton {
            border: 2px solid #0078D4;
            background-color: rgba(0, 120, 212, 0.1);
        }
        """
        button.setStyleSheet(highlight_style)
        
        # Reset after duration
        from PySide6.QtCore import QTimer
        QTimer.singleShot(duration, lambda: button.setStyleSheet(original_style))
        
        self.logger.debug(f"Highlighted action: {action}")
        
    def get_action_states(self) -> dict:
        """Get current state of all action buttons."""
        return {
            "start_all_enabled": self.start_all_btn.isEnabled(),
            "stop_all_enabled": self.stop_all_btn.isEnabled(),
            "refresh_enabled": self.refresh_btn.isEnabled(),
            "logs_enabled": self.logs_btn.isEnabled(),
            "settings_enabled": self.settings_btn.isEnabled(),
            "running_servers": self.running_servers_count,
            "total_servers": self.total_servers_count
        }
