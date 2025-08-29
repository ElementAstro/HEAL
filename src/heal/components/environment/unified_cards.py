"""
Unified Environment Cards
Simplified card hierarchy that consolidates different card types
into a more cohesive and maintainable structure.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, Signal, QTimer, QObject
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QFrame
)
from qfluentwidgets import (
    SettingCard, FluentIcon, BodyLabel, CaptionLabel,
    PrimaryPushButton, HyperlinkButton, ComboBox,
    ProgressBar, InfoBar, InfoBarPosition
)

from ...common.logging_config import get_logger
from ...common.i18n import t

logger = get_logger(__name__)


class CardType(Enum):
    """Types of environment cards"""
    STATUS = "status"
    TOOL = "tool"
    ACTION = "action"
    INFO = "info"
    CONFIGURATION = "configuration"


class CardPriority(Enum):
    """Card display priority"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class CardAction:
    """Action that can be performed from a card"""
    action_id: str
    title: str
    description: str = ""
    icon: Optional[FluentIcon] = None
    handler: Optional[Callable] = None
    enabled: bool = True
    primary: bool = False


class UnifiedEnvironmentCard(SettingCard):
    """
    Unified environment card that can display different types of content
    and actions based on configuration. Replaces multiple specialized card types.
    """
    
    action_triggered = Signal(str, str)  # card_id, action_id
    status_changed = Signal(str, str)    # card_id, new_status
    content_updated = Signal(str)        # card_id
    
    def __init__(
        self,
        card_id: str,
        title: str,
        card_type: CardType,
        icon: FluentIcon = FluentIcon.INFO,
        content: Optional[str] = None,
        priority: CardPriority = CardPriority.NORMAL,
        actions: Optional[List[CardAction]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(icon, title, content or "", parent)
        
        self.card_id = card_id
        self.card_type = card_type
        self.priority = priority
        self.actions = actions or []
        self.logger = get_logger(f"{__name__}.UnifiedEnvironmentCard.{card_id}")
        
        # Card state
        self.current_status = "ready"
        self.is_expanded = False
        self.data: Dict[str, Any] = {}
        
        # UI components
        self.action_buttons: Dict[str, QPushButton] = {}
        self.status_indicators: Dict[str, QWidget] = {}
        self.progress_bars: Dict[str, QProgressBar] = {}
        
        # Setup UI based on card type
        self._setup_card_ui()
        self._setup_actions()
        
        self.logger.debug(f"UnifiedEnvironmentCard created: {card_id}")
    
    def add_action(self, action: CardAction) -> None:
        """Add an action to the card"""
        self.actions.append(action)
        self._create_action_button(action)
        self.logger.debug(f"Added action: {action.action_id}")
    
    def remove_action(self, action_id: str) -> None:
        """Remove an action from the card"""
        self.actions = [a for a in self.actions if a.action_id != action_id]
        
        if action_id in self.action_buttons:
            button = self.action_buttons.pop(action_id)
            button.setParent(None)
            button.deleteLater()
        
        self.logger.debug(f"Removed action: {action_id}")
    
    def update_status(self, new_status: str, details: Optional[str] = None) -> None:
        """Update card status"""
        old_status = self.current_status
        self.current_status = new_status
        
        # Update UI based on status
        self._update_status_ui(new_status, details)
        
        # Emit signal
        self.status_changed.emit(self.card_id, new_status)
        
        self.logger.debug(f"Status updated: {old_status} -> {new_status}")
    
    def update_content(self, new_content: str, append: bool = False) -> None:
        """Update card content"""
        if append:
            current_content = self.contentLabel.text()
            new_content = f"{current_content}\n{new_content}"
        
        self.contentLabel.setText(new_content)
        self.content_updated.emit(self.card_id)
        
        self.logger.debug("Content updated")
    
    def set_data(self, key: str, value: Any) -> None:
        """Set card data"""
        self.data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get card data"""
        return self.data.get(key, default)
    
    def show_progress(self, progress: int, message: Optional[str] = None) -> None:
        """Show progress on the card"""
        if 'main_progress' not in self.progress_bars:
            self._create_progress_bar('main_progress')
        
        progress_bar = self.progress_bars['main_progress']
        progress_bar.setValue(progress)
        progress_bar.setVisible(True)
        
        if message:
            self.update_content(message)
    
    def hide_progress(self) -> None:
        """Hide progress indicators"""
        for progress_bar in self.progress_bars.values():
            progress_bar.setVisible(False)
    
    def expand(self) -> None:
        """Expand card to show additional details"""
        if not self.is_expanded:
            self.is_expanded = True
            self._update_expanded_ui()
    
    def collapse(self) -> None:
        """Collapse card to show minimal details"""
        if self.is_expanded:
            self.is_expanded = False
            self._update_collapsed_ui()
    
    def _setup_card_ui(self) -> None:
        """Setup card UI based on type"""
        if self.card_type == CardType.STATUS:
            self._setup_status_card()
        elif self.card_type == CardType.TOOL:
            self._setup_tool_card()
        elif self.card_type == CardType.ACTION:
            self._setup_action_card()
        elif self.card_type == CardType.INFO:
            self._setup_info_card()
        elif self.card_type == CardType.CONFIGURATION:
            self._setup_config_card()
    
    def _setup_actions(self) -> None:
        """Setup action buttons"""
        for action in self.actions:
            self._create_action_button(action)
    
    def _create_action_button(self, action: CardAction) -> None:
        """Create button for an action"""
        if action.primary:
            button = PrimaryPushButton(action.title)
        else:
            button = QPushButton(action.title)
        
        if action.icon:
            button.setIcon(action.icon)
        
        button.setEnabled(action.enabled)
        button.setToolTip(action.description)
        
        # Connect handler
        if action.handler:
            button.clicked.connect(action.handler)
        else:
            button.clicked.connect(lambda: self.action_triggered.emit(self.card_id, action.action_id))
        
        # Add to layout
        if hasattr(self, 'actionLayout'):
            self.actionLayout.addWidget(button)
        
        self.action_buttons[action.action_id] = button
    
    def _create_progress_bar(self, progress_id: str) -> None:
        """Create a progress bar"""
        progress_bar = ProgressBar()
        progress_bar.setVisible(False)
        
        # Add to layout
        if hasattr(self, 'contentLayout'):
            self.contentLayout.addWidget(progress_bar)
        
        self.progress_bars[progress_id] = progress_bar
    
    def _setup_status_card(self) -> None:
        """Setup status-specific UI"""
        # Add status indicator
        self.status_label = CaptionLabel("Ready")
        self.status_label.setStyleSheet("color: green;")
        
        # Create status layout
        if hasattr(self, 'hBoxLayout'):
            self.hBoxLayout.addWidget(self.status_label)
    
    def _setup_tool_card(self) -> None:
        """Setup tool-specific UI"""
        # Add tool status indicator
        self.tool_status_label = CaptionLabel("Unknown")
        
        # Create action layout for tool actions
        self.actionLayout = QHBoxLayout()
        
        if hasattr(self, 'vBoxLayout'):
            self.vBoxLayout.addLayout(self.actionLayout)
    
    def _setup_action_card(self) -> None:
        """Setup action-specific UI"""
        # Create action layout
        self.actionLayout = QHBoxLayout()
        
        if hasattr(self, 'vBoxLayout'):
            self.vBoxLayout.addLayout(self.actionLayout)
    
    def _setup_info_card(self) -> None:
        """Setup info-specific UI"""
        # Add info icon and styling
        self.setStyleSheet("QFrame { border: 1px solid #E0E0E0; }")
    
    def _setup_config_card(self) -> None:
        """Setup configuration-specific UI"""
        # Add configuration controls
        self.config_layout = QVBoxLayout()
        
        if hasattr(self, 'vBoxLayout'):
            self.vBoxLayout.addLayout(self.config_layout)
    
    def _update_status_ui(self, status: str, details: Optional[str] = None) -> None:
        """Update UI based on status"""
        if hasattr(self, 'status_label'):
            self.status_label.setText(status.title())
            
            # Update color based on status
            if status in ['ready', 'success', 'completed']:
                self.status_label.setStyleSheet("color: green;")
            elif status in ['warning', 'pending']:
                self.status_label.setStyleSheet("color: orange;")
            elif status in ['error', 'failed']:
                self.status_label.setStyleSheet("color: red;")
            else:
                self.status_label.setStyleSheet("color: gray;")
        
        if details:
            self.update_content(details, append=True)
    
    def _update_expanded_ui(self) -> None:
        """Update UI for expanded state"""
        # Show additional details
        for widget in self.status_indicators.values():
            widget.setVisible(True)
    
    def _update_collapsed_ui(self) -> None:
        """Update UI for collapsed state"""
        # Hide additional details
        for widget in self.status_indicators.values():
            widget.setVisible(False)


class EnvironmentCardFactory:
    """Factory for creating unified environment cards"""
    
    @staticmethod
    def create_status_card(
        card_id: str,
        title: str,
        status: str = "ready",
        icon: FluentIcon = FluentIcon.INFO
    ) -> UnifiedEnvironmentCard:
        """Create a status card"""
        card = UnifiedEnvironmentCard(
            card_id=card_id,
            title=title,
            card_type=CardType.STATUS,
            icon=icon,
            content=f"Status: {status}"
        )
        card.update_status(status)
        return card
    
    @staticmethod
    def create_tool_card(
        card_id: str,
        tool_name: str,
        tool_path: str,
        status: str = "unknown",
        actions: Optional[List[CardAction]] = None
    ) -> UnifiedEnvironmentCard:
        """Create a tool card"""
        card = UnifiedEnvironmentCard(
            card_id=card_id,
            title=tool_name,
            card_type=CardType.TOOL,
            icon=FluentIcon.DEVELOPER_TOOLS,
            content=f"Path: {tool_path}",
            actions=actions or []
        )
        card.set_data('tool_path', tool_path)
        card.update_status(status)
        return card
    
    @staticmethod
    def create_action_card(
        card_id: str,
        title: str,
        description: str,
        actions: List[CardAction],
        icon: FluentIcon = FluentIcon.PLAY
    ) -> UnifiedEnvironmentCard:
        """Create an action card"""
        return UnifiedEnvironmentCard(
            card_id=card_id,
            title=title,
            card_type=CardType.ACTION,
            icon=icon,
            content=description,
            actions=actions
        )
    
    @staticmethod
    def create_info_card(
        card_id: str,
        title: str,
        info_content: str,
        icon: FluentIcon = FluentIcon.INFO
    ) -> UnifiedEnvironmentCard:
        """Create an info card"""
        return UnifiedEnvironmentCard(
            card_id=card_id,
            title=title,
            card_type=CardType.INFO,
            icon=icon,
            content=info_content
        )
    
    @staticmethod
    def create_config_card(
        card_id: str,
        title: str,
        config_options: Dict[str, Any],
        icon: FluentIcon = FluentIcon.SETTING
    ) -> UnifiedEnvironmentCard:
        """Create a configuration card"""
        card = UnifiedEnvironmentCard(
            card_id=card_id,
            title=title,
            card_type=CardType.CONFIGURATION,
            icon=icon,
            content="Configuration options"
        )
        card.set_data('config_options', config_options)
        return card


class EnvironmentCardManager(QObject):
    """
    Manager for unified environment cards.
    Handles card lifecycle, layout, and coordination.
    """
    
    card_added = Signal(str)     # card_id
    card_removed = Signal(str)   # card_id
    card_updated = Signal(str)   # card_id
    layout_changed = Signal()
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.EnvironmentCardManager")
        
        # Card management
        self.cards: Dict[str, UnifiedEnvironmentCard] = {}
        self.card_order: List[str] = []
        self.card_groups: Dict[str, List[str]] = {}
        
        # Layout management
        self.layout_preferences: Dict[str, Any] = {
            'columns': 2,
            'spacing': 10,
            'group_spacing': 20,
            'sort_by_priority': True
        }
        
        self.logger.info("EnvironmentCardManager initialized")
    
    def add_card(self, card: UnifiedEnvironmentCard, group: Optional[str] = None) -> None:
        """Add a card to the manager"""
        card_id = card.card_id
        
        # Store card
        self.cards[card_id] = card
        self.card_order.append(card_id)
        
        # Add to group if specified
        if group:
            if group not in self.card_groups:
                self.card_groups[group] = []
            self.card_groups[group].append(card_id)
        
        # Connect signals
        card.action_triggered.connect(self._on_card_action)
        card.status_changed.connect(self._on_card_status_changed)
        card.content_updated.connect(self._on_card_content_updated)
        
        # Emit signal
        self.card_added.emit(card_id)
        
        self.logger.info(f"Added card: {card_id}")
    
    def remove_card(self, card_id: str) -> bool:
        """Remove a card from the manager"""
        if card_id not in self.cards:
            return False
        
        # Remove from order
        if card_id in self.card_order:
            self.card_order.remove(card_id)
        
        # Remove from groups
        for group_cards in self.card_groups.values():
            if card_id in group_cards:
                group_cards.remove(card_id)
        
        # Remove card
        card = self.cards.pop(card_id)
        card.setParent(None)
        card.deleteLater()
        
        # Emit signal
        self.card_removed.emit(card_id)
        
        self.logger.info(f"Removed card: {card_id}")
        return True
    
    def get_card(self, card_id: str) -> Optional[UnifiedEnvironmentCard]:
        """Get a card by ID"""
        return self.cards.get(card_id)
    
    def get_cards_by_type(self, card_type: CardType) -> List[UnifiedEnvironmentCard]:
        """Get cards by type"""
        return [card for card in self.cards.values() if card.card_type == card_type]
    
    def get_cards_by_group(self, group: str) -> List[UnifiedEnvironmentCard]:
        """Get cards by group"""
        card_ids = self.card_groups.get(group, [])
        return [self.cards[card_id] for card_id in card_ids if card_id in self.cards]
    
    def reorder_cards(self, new_order: List[str]) -> None:
        """Reorder cards"""
        # Validate new order
        if set(new_order) != set(self.card_order):
            self.logger.warning("Invalid card order provided")
            return
        
        self.card_order = new_order
        self.layout_changed.emit()
        
        self.logger.debug("Cards reordered")
    
    def sort_cards_by_priority(self) -> None:
        """Sort cards by priority"""
        def get_priority(card_id: str) -> int:
            card = self.cards.get(card_id)
            return card.priority.value if card else 0
        
        self.card_order.sort(key=get_priority, reverse=True)
        self.layout_changed.emit()
        
        self.logger.debug("Cards sorted by priority")
    
    def get_card_statistics(self) -> Dict[str, Any]:
        """Get card statistics"""
        stats = {
            'total_cards': len(self.cards),
            'card_types': {},
            'groups': len(self.card_groups),
            'priorities': {}
        }
        
        # Count by type and priority
        for card in self.cards.values():
            card_type = card.card_type.value
            priority = card.priority.value
            
            stats['card_types'][card_type] = stats['card_types'].get(card_type, 0) + 1
            stats['priorities'][priority] = stats['priorities'].get(priority, 0) + 1
        
        return stats
    
    def _on_card_action(self, card_id: str, action_id: str) -> None:
        """Handle card action"""
        self.logger.info(f"Card action triggered: {card_id}.{action_id}")
    
    def _on_card_status_changed(self, card_id: str, new_status: str) -> None:
        """Handle card status change"""
        self.card_updated.emit(card_id)
        self.logger.debug(f"Card status changed: {card_id} -> {new_status}")
    
    def _on_card_content_updated(self, card_id: str) -> None:
        """Handle card content update"""
        self.card_updated.emit(card_id)
        self.logger.debug(f"Card content updated: {card_id}")
