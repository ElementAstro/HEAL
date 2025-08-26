"""
Module Notification System

Centralized notification management with toast notifications, history tracking,
priority-based queuing, and comprehensive user feedback mechanisms.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import FluentIcon, InfoBar, InfoBarIcon, InfoBarPosition

from src.heal.common.logging_config import get_logger

logger = get_logger(__name__)


class NotificationType(Enum):
    """Notification types"""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"


class NotificationPriority(Enum):
    """Notification priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class NotificationAction:
    """Action that can be performed from a notification"""

    action_id: str
    title: str
    handler: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Notification:
    """Notification data structure"""

    notification_id: str
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    duration: int = 5000  # milliseconds, 0 = persistent
    module_name: Optional[str] = None
    category: Optional[str] = None
    actions: List[NotificationAction] = field(default_factory=list)
    progress: Optional[float] = None  # 0-100 for progress notifications
    icon: Optional[str] = None
    read: bool = False
    dismissed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToastNotification(QFrame):
    """Toast notification widget"""

    dismissed = Signal(str)  # notification_id
    action_clicked = Signal(str, str)  # notification_id, action_id

    def __init__(self, notification: Notification, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.notification = notification
        self.setup_ui()
        self.setup_animation()

    def setup_ui(self) -> None:
        """Setup the toast UI"""
        self.setFixedWidth(350)
        self.setMaximumHeight(120)
        self.setStyleSheet(
            """
            ToastNotification {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid #ddd;
                border-radius: 8px;
                margin: 5px;
            }
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)

        # Header with icon and title
        header_layout = QHBoxLayout()

        # Icon
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)

        if self.notification.notification_type == NotificationType.SUCCESS:
            icon_label.setPixmap(FluentIcon.ACCEPT.icon().pixmap(24, 24))
        elif self.notification.notification_type == NotificationType.WARNING:
            icon_label.setPixmap(FluentIcon.WARNING.icon().pixmap(24, 24))
        elif self.notification.notification_type == NotificationType.ERROR:
            icon_label.setPixmap(FluentIcon.CLOSE.icon().pixmap(24, 24))
        else:
            icon_label.setPixmap(FluentIcon.INFO.icon().pixmap(24, 24))

        header_layout.addWidget(icon_label)

        # Title
        title_label = QLabel(self.notification.title)
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Close button
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet(
            """
            QPushButton {
                border: none;
                background: transparent;
                font-size: 16px;
                font-weight: bold;
                color: #666;
            }
            QPushButton:hover {
                color: #000;
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 10px;
            }
        """
        )
        close_button.clicked.connect(self.dismiss)
        header_layout.addWidget(close_button)

        layout.addLayout(header_layout)

        # Message
        message_label = QLabel(self.notification.message)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 9))
        layout.addWidget(message_label)

        # Actions
        if self.notification.actions:
            actions_layout = QHBoxLayout()
            actions_layout.addStretch()

            for action in self.notification.actions:
                action_button = QPushButton(action.title)
                action_button.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #0078d4;
                        color: white;
                        border: none;
                        padding: 4px 12px;
                        border-radius: 4px;
                        font-size: 9px;
                    }
                    QPushButton:hover {
                        background-color: #106ebe;
                    }
                """
                )
                action_button.clicked.connect(
                    lambda checked, aid=action.action_id: self.action_clicked.emit(
                        self.notification.notification_id, aid
                    )
                )
                actions_layout.addWidget(action_button)

            layout.addLayout(actions_layout)

        # Auto-dismiss timer
        if self.notification.duration > 0:
            self.dismiss_timer = QTimer()
            self.dismiss_timer.timeout.connect(self.dismiss)
            self.dismiss_timer.start(self.notification.duration)

    def setup_animation(self) -> None:
        """Setup slide-in animation"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_animated(self, target_rect: QRect) -> None:
        """Show with slide-in animation"""
        # Start position (off-screen right)
        start_rect = QRect(
            target_rect.x() + 400,
            target_rect.y(),
            target_rect.width(),
            target_rect.height(),
        )
        self.setGeometry(start_rect)
        self.show()

        # Animate to target position
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(target_rect)
        self.animation.start()

    def dismiss(self) -> None:
        """Dismiss the notification"""
        self.dismissed.emit(self.notification.notification_id)

        # Animate out
        current_rect = self.geometry()
        end_rect = QRect(
            current_rect.x() + 400,
            current_rect.y(),
            current_rect.width(),
            current_rect.height(),
        )

        self.animation.setStartValue(current_rect)
        self.animation.setEndValue(end_rect)
        self.animation.finished.connect(self.deleteLater)
        self.animation.start()


class ModuleNotificationSystem(QObject):
    """Centralized notification management system"""

    # Signals
    notification_added = Signal(str)  # notification_id
    notification_dismissed = Signal(str)  # notification_id
    notification_read = Signal(str)  # notification_id
    action_executed = Signal(str, str)  # notification_id, action_id

    def __init__(self, parent_widget: QWidget, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.logger = logger.bind(component="ModuleNotificationSystem")
        self.parent_widget = parent_widget

        # Notification storage
        self.notifications: Dict[str, Notification] = {}
        self.notification_queue: List[str] = []
        self.active_toasts: Dict[str, ToastNotification] = {}

        # Settings
        self.max_concurrent_toasts = 5
        self.max_history_size = 1000
        self.toast_position = "top_right"

        # Action handlers
        self.action_handlers: Dict[str, Callable] = {}

        # Persistence
        self.notifications_file = Path("config/notifications.json")
        self.notifications_file.parent.mkdir(exist_ok=True)

        # Queue processing timer
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.process_queue)
        self.queue_timer.start(500)  # Process queue every 500ms

        # Load saved notifications
        self.load_notifications()

        self.logger.info("Module Notification System initialized")

    def register_action_handler(self, action_id: str, handler: Callable) -> None:
        """Register an action handler"""
        self.action_handlers[action_id] = handler
        self.logger.debug(f"Registered action handler: {action_id}")

    def show_info(self, title: str, message: str, **kwargs: Any) -> str:
        """Show info notification"""
        return self.add_notification(
            title=title,
            message=message,
            notification_type=NotificationType.INFO,
            **kwargs,
        )

    def show_success(self, title: str, message: str, **kwargs: Any) -> str:
        """Show success notification"""
        return self.add_notification(
            title=title,
            message=message,
            notification_type=NotificationType.SUCCESS,
            **kwargs,
        )

    def show_warning(self, title: str, message: str, **kwargs: Any) -> str:
        """Show warning notification"""
        return self.add_notification(
            title=title,
            message=message,
            notification_type=NotificationType.WARNING,
            **kwargs,
        )

    def show_error(self, title: str, message: str, **kwargs: Any) -> str:
        """Show error notification"""
        return self.add_notification(
            title=title,
            message=message,
            notification_type=NotificationType.ERROR,
            duration=0,  # Persistent by default
            **kwargs,
        )

    def show_progress(
        self, title: str, message: str, progress: float = 0, **kwargs: Any
    ) -> str:
        """Show progress notification"""
        return self.add_notification(
            title=title,
            message=message,
            notification_type=NotificationType.PROGRESS,
            progress=progress,
            duration=0,  # Persistent until updated
            **kwargs,
        )

    def add_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        duration: int = 5000,
        module_name: Optional[str] = None,
        category: Optional[str] = None,
        actions: Optional[List[NotificationAction]] = None,
        **kwargs: Any,
    ) -> str:
        """Add a new notification"""

        notification_id = f"notif_{int(time.time() * 1000)}"

        notification = Notification(
            notification_id=notification_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            duration=duration,
            module_name=module_name,
            category=category,
            actions=actions or [],
            **kwargs,
        )

        # Store notification
        self.notifications[notification_id] = notification

        # Add to queue based on priority
        self._add_to_queue(notification_id)

        # Emit signal
        self.notification_added.emit(notification_id)

        # Limit history size
        self._cleanup_old_notifications()

        # Auto-save
        self.save_notifications()

        self.logger.info(f"Added notification: {title}")
        return notification_id

    def update_progress(
        self, notification_id: str, progress: float, message: Optional[str] = None
    ) -> None:
        """Update progress notification"""
        if notification_id not in self.notifications:
            return

        notification = self.notifications[notification_id]
        notification.progress = max(0, min(100, progress))

        if message:
            notification.message = message

        # Update toast if active
        if notification_id in self.active_toasts:
            toast = self.active_toasts[notification_id]
            # Update toast UI (would need to implement update method)

        self.logger.debug(f"Updated progress for {notification_id}: {progress}%")

    def dismiss_notification(self, notification_id: str) -> None:
        """Dismiss a notification"""
        if notification_id in self.notifications:
            notification = self.notifications[notification_id]
            notification.dismissed = True

            # Remove from queue if present
            if notification_id in self.notification_queue:
                self.notification_queue.remove(notification_id)

            # Remove active toast
            if notification_id in self.active_toasts:
                toast = self.active_toasts[notification_id]
                toast.dismiss()
                del self.active_toasts[notification_id]

            self.notification_dismissed.emit(notification_id)
            self.logger.debug(f"Dismissed notification: {notification_id}")

    def mark_as_read(self, notification_id: str) -> None:
        """Mark notification as read"""
        if notification_id in self.notifications:
            notification = self.notifications[notification_id]
            notification.read = True
            self.notification_read.emit(notification_id)

    def execute_action(self, notification_id: str, action_id: str) -> bool:
        """Execute a notification action"""
        if notification_id not in self.notifications:
            return False

        notification = self.notifications[notification_id]

        # Find action
        action = None
        for a in notification.actions:
            if a.action_id == action_id:
                action = a
                break

        if not action:
            return False

        try:
            # Execute action handler
            if action.handler:
                success = action.handler(notification, action.parameters)
            elif action_id in self.action_handlers:
                handler = self.action_handlers[action_id]
                success = handler(notification, action.parameters)
            else:
                self.logger.error(f"No handler found for action {action_id}")
                return False

            if success:
                self.action_executed.emit(notification_id, action_id)
                self.logger.info(
                    f"Executed action {action_id} for notification {notification_id}"
                )

                # Auto-dismiss after action
                self.dismiss_notification(notification_id)
                return True

        except Exception as e:
            self.logger.error(f"Error executing action {action_id}: {e}")

        return False

    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID"""
        return self.notifications.get(notification_id)

    def get_notifications_by_module(self, module_name: str) -> List[Notification]:
        """Get notifications for a specific module"""
        return [n for n in self.notifications.values() if n.module_name == module_name]

    def get_unread_notifications(self) -> List[Notification]:
        """Get unread notifications"""
        return [
            n for n in self.notifications.values() if not n.read and not n.dismissed
        ]

    def get_recent_notifications(self, hours: int = 24) -> List[Notification]:
        """Get recent notifications"""
        cutoff_time = time.time() - (hours * 3600)
        return [n for n in self.notifications.values() if n.timestamp > cutoff_time]

    def clear_all_notifications(self) -> None:
        """Clear all notifications"""
        # Dismiss all active toasts
        for notification_id in list(self.active_toasts.keys()):
            self.dismiss_notification(notification_id)

        # Clear storage
        self.notifications.clear()
        self.notification_queue.clear()

        self.logger.info("Cleared all notifications")
        self.save_notifications()

    def clear_read_notifications(self) -> None:
        """Clear read notifications"""
        read_notifications = [nid for nid, n in self.notifications.items() if n.read]

        for notification_id in read_notifications:
            if notification_id in self.active_toasts:
                self.dismiss_notification(notification_id)
            else:
                del self.notifications[notification_id]

        self.logger.info(f"Cleared {len(read_notifications)} read notifications")
        self.save_notifications()

    def process_queue(self) -> None:
        """Process notification queue"""
        if not self.notification_queue:
            return

        # Check if we can show more toasts
        if len(self.active_toasts) >= self.max_concurrent_toasts:
            return

        # Get next notification by priority
        next_notification_id = self._get_next_from_queue()
        if not next_notification_id:
            return

        notification = self.notifications[next_notification_id]

        # Create and show toast
        toast = ToastNotification(notification, self.parent_widget)
        toast.dismissed.connect(self._on_toast_dismissed)
        toast.action_clicked.connect(self.execute_action)

        # Position toast
        toast_rect = self._get_toast_position(len(self.active_toasts))
        toast.show_animated(toast_rect)

        # Track active toast
        self.active_toasts[next_notification_id] = toast

        # Remove from queue
        self.notification_queue.remove(next_notification_id)

    def _add_to_queue(self, notification_id: str) -> None:
        """Add notification to queue based on priority"""
        notification = self.notifications[notification_id]

        # Insert based on priority
        inserted = False
        for i, existing_id in enumerate(self.notification_queue):
            existing_notification = self.notifications[existing_id]
            if notification.priority.value > existing_notification.priority.value:
                self.notification_queue.insert(i, notification_id)
                inserted = True
                break

        if not inserted:
            self.notification_queue.append(notification_id)

    def _get_next_from_queue(self) -> Optional[str]:
        """Get next notification from queue"""
        if not self.notification_queue:
            return None

        # Return highest priority notification
        return self.notification_queue[0]

    def _get_toast_position(self, index: int) -> QRect:
        """Get position for toast notification"""
        parent_rect = self.parent_widget.rect()
        toast_height = 120
        toast_width = 350
        margin = 10

        if self.toast_position == "top_right":
            x = parent_rect.width() - toast_width - margin
            y = margin + (index * (toast_height + margin))
        elif self.toast_position == "top_left":
            x = margin
            y = margin + (index * (toast_height + margin))
        elif self.toast_position == "bottom_right":
            x = parent_rect.width() - toast_width - margin
            y = (
                parent_rect.height()
                - toast_height
                - margin
                - (index * (toast_height + margin))
            )
        else:  # bottom_left
            x = margin
            y = (
                parent_rect.height()
                - toast_height
                - margin
                - (index * (toast_height + margin))
            )

        return QRect(x, y, toast_width, toast_height)

    def _on_toast_dismissed(self, notification_id: str) -> None:
        """Handle toast dismissal"""
        if notification_id in self.active_toasts:
            del self.active_toasts[notification_id]

        self.dismiss_notification(notification_id)

    def _cleanup_old_notifications(self) -> None:
        """Remove old notifications to limit memory usage"""
        if len(self.notifications) <= self.max_history_size:
            return

        # Sort by timestamp and keep most recent
        sorted_notifications = sorted(
            self.notifications.items(), key=lambda x: x[1].timestamp, reverse=True
        )

        # Keep only the most recent notifications
        to_keep = dict(sorted_notifications[: self.max_history_size])
        self.notifications = to_keep

        self.logger.info(f"Cleaned up old notifications, kept {len(to_keep)}")

    def save_notifications(self) -> None:
        """Save notifications to disk"""
        try:
            # Only save recent notifications to avoid large files
            recent_notifications = self.get_recent_notifications(hours=168)  # 1 week

            notifications_data = {}
            for notification in recent_notifications:
                notifications_data[notification.notification_id] = {
                    "notification_id": notification.notification_id,
                    "title": notification.title,
                    "message": notification.message,
                    "notification_type": notification.notification_type.value,
                    "priority": notification.priority.value,
                    "timestamp": notification.timestamp,
                    "duration": notification.duration,
                    "module_name": notification.module_name,
                    "category": notification.category,
                    "progress": notification.progress,
                    "icon": notification.icon,
                    "read": notification.read,
                    "dismissed": notification.dismissed,
                    "metadata": notification.metadata,
                    "actions": [
                        {
                            "action_id": action.action_id,
                            "title": action.title,
                            "parameters": action.parameters,
                        }
                        for action in notification.actions
                    ],
                }

            with open(self.notifications_file, "w", encoding="utf-8") as f:
                json.dump(notifications_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Error saving notifications: {e}")

    def load_notifications(self) -> None:
        """Load notifications from disk"""
        if not self.notifications_file.exists():
            return

        try:
            with open(self.notifications_file, "r", encoding="utf-8") as f:
                notifications_data = json.load(f)

            for notification_id, data in notifications_data.items():
                # Reconstruct actions
                actions = []
                for action_data in data.get("actions", []):
                    actions.append(
                        NotificationAction(
                            action_id=action_data["action_id"],
                            title=action_data["title"],
                            parameters=action_data["parameters"],
                        )
                    )

                # Reconstruct notification
                notification = Notification(
                    notification_id=data["notification_id"],
                    title=data["title"],
                    message=data["message"],
                    notification_type=NotificationType(data["notification_type"]),
                    priority=NotificationPriority(data["priority"]),
                    timestamp=data["timestamp"],
                    duration=data["duration"],
                    module_name=data["module_name"],
                    category=data["category"],
                    actions=actions,
                    progress=data["progress"],
                    icon=data["icon"],
                    read=data["read"],
                    dismissed=data["dismissed"],
                    metadata=data["metadata"],
                )

                self.notifications[notification_id] = notification

            self.logger.info(
                f"Loaded {len(notifications_data)} notifications from disk"
            )

        except Exception as e:
            self.logger.error(f"Error loading notifications: {e}")
