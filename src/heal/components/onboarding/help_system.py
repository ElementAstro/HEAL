"""
Consolidated Help System
Merges contextual help, documentation integration, and help-related functionality
into a single cohesive system with simplified hierarchy.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from ...common.logging_config import get_logger

# Re-export for backward compatibility
from .contextual_help import ContextualHelpSystem
from .documentation_integration import DocumentationIntegration

logger = get_logger(__name__)


class HelpType(Enum):
    """Types of help content"""
    TOOLTIP = "tooltip"
    CONTEXTUAL = "contextual"
    TUTORIAL = "tutorial"
    DOCUMENTATION = "documentation"
    FAQ = "faq"
    VIDEO = "video"


class HelpPriority(Enum):
    """Help content priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class HelpItem:
    """Unified help item structure"""
    help_id: str
    title: str
    content: str
    help_type: HelpType
    priority: HelpPriority = HelpPriority.NORMAL
    context: Optional[str] = None
    widget_id: Optional[str] = None
    keywords: List[str] = None
    url: Optional[str] = None
    video_url: Optional[str] = None
    prerequisites: List[str] = None
    related_items: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.prerequisites is None:
            self.prerequisites = []
        if self.related_items is None:
            self.related_items = []


class HelpSystem(QObject):
    """
    Consolidated help system that merges:
    - ContextualHelpSystem
    - DocumentationIntegration
    - Help content management
    
    Provides unified interface for all help-related functionality.
    """
    
    help_requested = Signal(str)  # help_id
    help_shown = Signal(str, str)  # help_id, context
    help_dismissed = Signal(str)  # help_id
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.HelpSystem")
        
        # Help content storage
        self.help_items: Dict[str, HelpItem] = {}
        self.context_mapping: Dict[str, List[str]] = {}  # context -> help_ids
        self.widget_mapping: Dict[str, List[str]] = {}   # widget_id -> help_ids
        
        # Help handlers
        self.help_handlers: Dict[str, Callable] = {}
        
        # Configuration
        self.help_config_file = Path("config/help_system.json")
        
        # Initialize help content
        self._load_help_content()
        self._register_default_handlers()
        
        self.logger.info("HelpSystem initialized")
    
    def register_help_item(self, help_item: HelpItem) -> None:
        """Register a help item"""
        self.help_items[help_item.help_id] = help_item
        
        # Update context mapping
        if help_item.context:
            if help_item.context not in self.context_mapping:
                self.context_mapping[help_item.context] = []
            self.context_mapping[help_item.context].append(help_item.help_id)
        
        # Update widget mapping
        if help_item.widget_id:
            if help_item.widget_id not in self.widget_mapping:
                self.widget_mapping[help_item.widget_id] = []
            self.widget_mapping[help_item.widget_id].append(help_item.help_id)
        
        self.logger.debug(f"Registered help item: {help_item.help_id}")
    
    def show_help(self, help_id: str, context: Optional[str] = None) -> bool:
        """Show specific help item"""
        if help_id not in self.help_items:
            self.logger.warning(f"Help item not found: {help_id}")
            return False
        
        help_item = self.help_items[help_id]
        
        # Use appropriate handler based on help type
        handler_key = f"show_{help_item.help_type.value}"
        if handler_key in self.help_handlers:
            success = self.help_handlers[handler_key](help_item, context)
            if success:
                self.help_shown.emit(help_id, context or "")
                self.logger.info(f"Showed help: {help_id}")
            return success
        else:
            self.logger.warning(f"No handler for help type: {help_item.help_type.value}")
            return False
    
    def show_contextual_help(self, context: str, widget: Optional[QWidget] = None) -> List[str]:
        """Show help for specific context"""
        shown_help_ids = []
        
        # Get help items for context
        help_ids = self.context_mapping.get(context, [])
        
        # Also check widget-specific help if widget provided
        if widget and hasattr(widget, 'objectName'):
            widget_id = widget.objectName()
            widget_help_ids = self.widget_mapping.get(widget_id, [])
            help_ids.extend(widget_help_ids)
        
        # Remove duplicates and sort by priority
        unique_help_ids = list(set(help_ids))
        help_items = [self.help_items[hid] for hid in unique_help_ids if hid in self.help_items]
        help_items.sort(key=lambda x: x.priority.value, reverse=True)
        
        # Show help items
        for help_item in help_items:
            if self.show_help(help_item.help_id, context):
                shown_help_ids.append(help_item.help_id)
        
        return shown_help_ids
    
    def search_help(self, query: str, help_type: Optional[HelpType] = None) -> List[HelpItem]:
        """Search help content"""
        results = []
        query_lower = query.lower()
        
        for help_item in self.help_items.values():
            # Filter by type if specified
            if help_type and help_item.help_type != help_type:
                continue
            
            # Search in title, content, and keywords
            if (query_lower in help_item.title.lower() or
                query_lower in help_item.content.lower() or
                any(query_lower in keyword.lower() for keyword in help_item.keywords)):
                results.append(help_item)
        
        # Sort by priority
        results.sort(key=lambda x: x.priority.value, reverse=True)
        return results
    
    def get_help_for_error(self, error_type: str, error_context: Dict[str, Any]) -> List[HelpItem]:
        """Get help items for specific error"""
        # Search for error-related help
        error_help = self.search_help(error_type)
        
        # Add context-specific help if available
        context = error_context.get('context', '')
        if context:
            context_help = self.context_mapping.get(context, [])
            for help_id in context_help:
                if help_id in self.help_items:
                    help_item = self.help_items[help_id]
                    if help_item not in error_help:
                        error_help.append(help_item)
        
        return error_help
    
    def register_help_handler(self, help_type: str, handler: Callable) -> None:
        """Register a help handler for specific type"""
        handler_key = f"show_{help_type}"
        self.help_handlers[handler_key] = handler
        self.logger.debug(f"Registered help handler: {help_type}")
    
    def get_help_statistics(self) -> Dict[str, Any]:
        """Get help system statistics"""
        stats = {
            'total_help_items': len(self.help_items),
            'help_types': {},
            'contexts': len(self.context_mapping),
            'widgets': len(self.widget_mapping)
        }
        
        # Count by type
        for help_item in self.help_items.values():
            help_type = help_item.help_type.value
            stats['help_types'][help_type] = stats['help_types'].get(help_type, 0) + 1
        
        return stats
    
    def _load_help_content(self) -> None:
        """Load help content from configuration"""
        try:
            if self.help_config_file.exists():
                with open(self.help_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for help_data in data.get('help_items', []):
                    help_item = HelpItem(
                        help_id=help_data['help_id'],
                        title=help_data['title'],
                        content=help_data['content'],
                        help_type=HelpType(help_data['help_type']),
                        priority=HelpPriority(help_data.get('priority', HelpPriority.NORMAL.value)),
                        context=help_data.get('context'),
                        widget_id=help_data.get('widget_id'),
                        keywords=help_data.get('keywords', []),
                        url=help_data.get('url'),
                        video_url=help_data.get('video_url'),
                        prerequisites=help_data.get('prerequisites', []),
                        related_items=help_data.get('related_items', [])
                    )
                    self.register_help_item(help_item)
                
                self.logger.info(f"Loaded {len(self.help_items)} help items")
                
        except Exception as e:
            self.logger.error(f"Failed to load help content: {e}")
    
    def _register_default_handlers(self) -> None:
        """Register default help handlers"""
        
        def show_tooltip(help_item: HelpItem, context: Optional[str] = None) -> bool:
            """Show tooltip help"""
            # Placeholder for tooltip implementation
            self.logger.debug(f"Showing tooltip: {help_item.title}")
            return True
        
        def show_contextual(help_item: HelpItem, context: Optional[str] = None) -> bool:
            """Show contextual help"""
            # Placeholder for contextual help implementation
            self.logger.debug(f"Showing contextual help: {help_item.title}")
            return True
        
        def show_documentation(help_item: HelpItem, context: Optional[str] = None) -> bool:
            """Show documentation"""
            # Placeholder for documentation implementation
            self.logger.debug(f"Showing documentation: {help_item.title}")
            return True
        
        def show_tutorial(help_item: HelpItem, context: Optional[str] = None) -> bool:
            """Show tutorial"""
            # Placeholder for tutorial implementation
            self.logger.debug(f"Showing tutorial: {help_item.title}")
            return True
        
        def show_faq(help_item: HelpItem, context: Optional[str] = None) -> bool:
            """Show FAQ"""
            # Placeholder for FAQ implementation
            self.logger.debug(f"Showing FAQ: {help_item.title}")
            return True
        
        def show_video(help_item: HelpItem, context: Optional[str] = None) -> bool:
            """Show video help"""
            # Placeholder for video implementation
            self.logger.debug(f"Showing video: {help_item.title}")
            return True
        
        # Register handlers
        self.register_help_handler('tooltip', show_tooltip)
        self.register_help_handler('contextual', show_contextual)
        self.register_help_handler('documentation', show_documentation)
        self.register_help_handler('tutorial', show_tutorial)
        self.register_help_handler('faq', show_faq)
        self.register_help_handler('video', show_video)
