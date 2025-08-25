from typing import Dict, Any, Optional
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QSizePolicy)
from PySide6.QtGui import QFont, QContextMenuEvent, QPalette
from qfluentwidgets import (FluentIcon, setCustomStyleSheet, RoundMenu, Action,
                           PushButton, PrimaryPushButton, ToolButton)
from app.model.config import cfg
from app.common.i18n_ui import tr
from app.common.logging_config import get_logger

logger = get_logger(__name__)


class ServerStatusCard(QFrame):
    """Enhanced server status card with detailed information and quick actions."""
    
    # Signals
    start_requested = Signal(str)  # server_name
    stop_requested = Signal(str)   # server_name
    restart_requested = Signal(str) # server_name
    settings_requested = Signal(str) # server_name
    
    def __init__(self, server_name: str, server_config: Dict[str, Any], parent: QWidget = None):
        super().__init__(parent)
        self.server_name = server_name
        self.server_config = server_config
        self.current_status = "stopped"  # stopped, running, error, starting, stopping
        self.process_id = None
        self.port = server_config.get('port', 'N/A')
        
        self.logger = get_logger('server_status_card', module=f'ServerStatusCard-{server_name}')
        
        self._init_ui()
        self._setup_styles()
        self._connect_signals()
        
    def _init_ui(self):
        """Initialize the user interface."""
        self.setFixedSize(350, 120)
        self.setFrameStyle(QFrame.Shape.Box)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(6)
        
        # Header layout (icon, name, status)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Server icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_icon()
        
        # Server name and info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.name_label = QLabel(self.server_name)
        self.name_label.setFont(QFont(cfg.APP_FONT, 12, QFont.Weight.Bold))
        
        self.info_label = QLabel()
        self.info_label.setFont(QFont(cfg.APP_FONT, 9))
        self._update_info_text()
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.info_label)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont(cfg.APP_FONT, 16))
        self.status_indicator.setFixedSize(24, 24)
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_status_indicator()
        
        header_layout.addWidget(self.icon_label)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.status_indicator)
        
        # Action buttons layout
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)
        
        self.start_btn = PushButton(tr("home.start"))
        self.start_btn.setFixedSize(60, 28)
        self.start_btn.setFont(QFont(cfg.APP_FONT, 9))
        
        self.stop_btn = PushButton(tr("home.stop"))
        self.stop_btn.setFixedSize(60, 28)
        self.stop_btn.setFont(QFont(cfg.APP_FONT, 9))
        
        self.restart_btn = PushButton(tr("home.restart"))
        self.restart_btn.setFixedSize(60, 28)
        self.restart_btn.setFont(QFont(cfg.APP_FONT, 9))
        
        self.settings_btn = ToolButton(FluentIcon.SETTING)
        self.settings_btn.setFixedSize(28, 28)
        
        actions_layout.addWidget(self.start_btn)
        actions_layout.addWidget(self.stop_btn)
        actions_layout.addWidget(self.restart_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.settings_btn)
        
        # Add layouts to main
        main_layout.addLayout(header_layout)
        main_layout.addLayout(actions_layout)
        
        # Update button states
        self._update_button_states()
        
    def _setup_styles(self):
        """Setup custom styles for the card."""
        card_style = """
        ServerStatusCard {
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            background-color: rgba(255, 255, 255, 0.8);
        }
        ServerStatusCard:hover {
            border: 1px solid rgba(0, 0, 0, 0.2);
            background-color: rgba(255, 255, 255, 0.9);
        }
        """
        setCustomStyleSheet(self, card_style, card_style)
        
    def _connect_signals(self):
        """Connect button signals."""
        self.start_btn.clicked.connect(lambda: self.start_requested.emit(self.server_name))
        self.stop_btn.clicked.connect(lambda: self.stop_requested.emit(self.server_name))
        self.restart_btn.clicked.connect(lambda: self.restart_requested.emit(self.server_name))
        self.settings_btn.clicked.connect(lambda: self.settings_requested.emit(self.server_name))
        
    def _update_icon(self):
        """Update the server icon."""
        # This would be enhanced to show actual icons based on server config
        icon_text = self.server_name[0].upper()
        self.icon_label.setText(icon_text)
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                border-radius: 16px;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
    def _update_info_text(self):
        """Update the information text."""
        port_text = f"Port: {self.port}" if self.port != 'N/A' else "Port: N/A"
        pid_text = f" | PID: {self.process_id}" if self.process_id else ""
        self.info_label.setText(f"{port_text}{pid_text}")
        
    def _update_status_indicator(self):
        """Update the status indicator color and tooltip."""
        status_colors = {
            "stopped": "#9E9E9E",    # Gray
            "running": "#4CAF50",    # Green
            "error": "#F44336",      # Red
            "starting": "#FF9800",   # Orange
            "stopping": "#FF9800"    # Orange
        }
        
        color = status_colors.get(self.current_status, "#9E9E9E")
        self.status_indicator.setStyleSheet(f"QLabel {{ color: {color}; }}")
        self.status_indicator.setToolTip(f"Status: {self.current_status.title()}")
        
    def _update_button_states(self):
        """Update button enabled/disabled states based on current status."""
        is_running = self.current_status == "running"
        is_stopped = self.current_status == "stopped"
        is_transitioning = self.current_status in ["starting", "stopping"]
        
        self.start_btn.setEnabled(is_stopped and not is_transitioning)
        self.stop_btn.setEnabled(is_running and not is_transitioning)
        self.restart_btn.setEnabled(is_running and not is_transitioning)
        
    def update_status(self, status: str, process_id: Optional[int] = None):
        """Update the server status."""
        self.current_status = status
        self.process_id = process_id
        
        self._update_status_indicator()
        self._update_info_text()
        self._update_button_states()
        
        self.logger.debug(f"Status updated: {status}, PID: {process_id}")
        
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Show context menu with additional options."""
        menu = RoundMenu(parent=self)
        
        # Add standard actions
        open_folder_action = Action(FluentIcon.FOLDER, tr("home.open_folder"))
        view_logs_action = Action(FluentIcon.DOCUMENT, tr("home.view_logs"))
        copy_info_action = Action(FluentIcon.COPY, tr("home.copy_info"))
        
        menu.addAction(open_folder_action)
        menu.addAction(view_logs_action)
        menu.addSeparator()
        menu.addAction(copy_info_action)
        
        # Connect actions (placeholder implementations)
        open_folder_action.triggered.connect(lambda: self._open_server_folder())
        view_logs_action.triggered.connect(lambda: self._view_server_logs())
        copy_info_action.triggered.connect(lambda: self._copy_server_info())
        
        menu.exec(event.globalPos())
        
    def _open_server_folder(self):
        """Open server folder in file explorer."""
        self.logger.info(f"Opening folder for {self.server_name}")
        # Implementation would open the actual server folder
        
    def _view_server_logs(self):
        """View server logs."""
        self.logger.info(f"Viewing logs for {self.server_name}")
        # Implementation would open log viewer
        
    def _copy_server_info(self):
        """Copy server information to clipboard."""
        info = f"Server: {self.server_name}\nStatus: {self.current_status}\nPort: {self.port}"
        if self.process_id:
            info += f"\nPID: {self.process_id}"
        # Implementation would copy to clipboard
        self.logger.info(f"Copied info for {self.server_name}")
