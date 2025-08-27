"""
Documentation Integration System

Seamlessly integrates documentation into the application with in-app help,
quick access, contextual documentation, and smart content suggestions.
"""

import json
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

from PySide6.QtCore import QObject, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget
from qfluentwidgets import InfoBar, InfoBarPosition, MessageBox, TeachingTip

from src.heal.common.i18n_ui import tr
from src.heal.common.logging_config import get_logger
from .user_state_tracker import UserLevel, UserStateTracker


class DocumentationType(Enum):
    """Types of documentation content"""
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    GUIDE = "guide"
    FAQ = "faq"
    TROUBLESHOOTING = "troubleshooting"
    API = "api"
    EXAMPLES = "examples"


class DocumentationItem:
    """Represents a documentation item"""
    
    def __init__(
        self,
        doc_id: str,
        title: str,
        content: str,
        doc_type: DocumentationType,
        tags: List[str],
        url: Optional[str] = None,
        local_path: Optional[str] = None,
        user_levels: Optional[List[UserLevel]] = None,
        prerequisites: Optional[List[str]] = None,
        related_items: Optional[List[str]] = None,
    ):
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.doc_type = doc_type
        self.tags = tags
        self.url = url
        self.local_path = local_path
        self.user_levels = user_levels or [UserLevel.BEGINNER, UserLevel.INTERMEDIATE, UserLevel.ADVANCED]
        self.prerequisites = prerequisites or []
        self.related_items = related_items or []
        self.view_count = 0
        self.last_viewed: Optional[datetime] = None
    
    def is_relevant(self, user_level: UserLevel, completed_actions: Set[str]) -> bool:
        """Check if this documentation is relevant for the user"""
        # Check user level
        if user_level not in self.user_levels:
            return False
        
        # Check prerequisites
        for prereq in self.prerequisites:
            if prereq not in completed_actions:
                return False
        
        return True
    
    def mark_viewed(self) -> None:
        """Mark this documentation as viewed"""
        from datetime import datetime
        self.view_count += 1
        self.last_viewed = datetime.now()


class DocumentationIntegration(QObject):
    """Manages in-app documentation integration and smart content delivery"""
    
    # Signals
    documentation_opened = Signal(str)  # doc_id
    help_requested = Signal(str, str)  # context, query
    search_performed = Signal(str)  # query
    
    def __init__(self, user_tracker: UserStateTracker, main_window: QWidget, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger("documentation_integration", module="DocumentationIntegration")
        self.user_tracker = user_tracker
        self.main_window = main_window
        
        # Documentation management
        self.documentation_items: Dict[str, DocumentationItem] = {}
        self.search_index: Dict[str, Set[str]] = {}  # keyword -> doc_ids
        self.context_mapping: Dict[str, List[str]] = {}  # context -> doc_ids
        self.user_history: List[str] = []  # Recently viewed doc_ids
        
        # Configuration
        self.docs_base_url = "https://heal-docs.example.com"
        self.local_docs_path = Path("docs")
        
        self._init_documentation_database()
        self._build_search_index()
        self._setup_context_mapping()
    
    def _init_documentation_database(self) -> None:
        """Initialize the documentation database"""
        docs_data = [
            # Getting started documentation
            {
                "doc_id": "getting_started",
                "title": "Getting Started with HEAL",
                "content": "Complete guide to setting up and using HEAL for the first time.",
                "type": DocumentationType.GUIDE,
                "tags": ["setup", "beginner", "introduction"],
                "url": "/getting-started",
                "user_levels": [UserLevel.BEGINNER],
            },
            {
                "doc_id": "first_server_setup",
                "title": "Setting Up Your First Server",
                "content": "Step-by-step guide to configuring and launching your first server.",
                "type": DocumentationType.TUTORIAL,
                "tags": ["server", "setup", "configuration"],
                "url": "/tutorials/first-server",
                "user_levels": [UserLevel.BEGINNER, UserLevel.INTERMEDIATE],
            },
            
            # Feature documentation
            {
                "doc_id": "server_management",
                "title": "Server Management Guide",
                "content": "Comprehensive guide to managing servers in HEAL.",
                "type": DocumentationType.GUIDE,
                "tags": ["server", "management", "operations"],
                "url": "/guides/server-management",
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
            },
            {
                "doc_id": "module_system",
                "title": "Module System Overview",
                "content": "Understanding and using the HEAL module system.",
                "type": DocumentationType.REFERENCE,
                "tags": ["modules", "plugins", "extensions"],
                "url": "/reference/modules",
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
            },
            {
                "doc_id": "module_development",
                "title": "Developing Custom Modules",
                "content": "Guide to creating custom modules for HEAL.",
                "type": DocumentationType.TUTORIAL,
                "tags": ["development", "modules", "programming"],
                "url": "/tutorials/module-development",
                "user_levels": [UserLevel.ADVANCED],
                "prerequisites": ["used_modules", "programming_experience"],
            },
            
            # Troubleshooting documentation
            {
                "doc_id": "connection_troubleshooting",
                "title": "Connection Issues Troubleshooting",
                "content": "Solutions for common connection problems.",
                "type": DocumentationType.TROUBLESHOOTING,
                "tags": ["troubleshooting", "connection", "network"],
                "url": "/troubleshooting/connection",
            },
            {
                "doc_id": "performance_optimization",
                "title": "Performance Optimization Guide",
                "content": "Tips and techniques for optimizing HEAL performance.",
                "type": DocumentationType.GUIDE,
                "tags": ["performance", "optimization", "tuning"],
                "url": "/guides/performance",
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
            },
            
            # FAQ documentation
            {
                "doc_id": "general_faq",
                "title": "Frequently Asked Questions",
                "content": "Common questions and answers about HEAL.",
                "type": DocumentationType.FAQ,
                "tags": ["faq", "questions", "help"],
                "url": "/faq",
            },
            {
                "doc_id": "configuration_faq",
                "title": "Configuration FAQ",
                "content": "Frequently asked questions about configuration.",
                "type": DocumentationType.FAQ,
                "tags": ["faq", "configuration", "settings"],
                "url": "/faq/configuration",
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
            },
            
            # API documentation
            {
                "doc_id": "api_reference",
                "title": "API Reference",
                "content": "Complete API reference for HEAL.",
                "type": DocumentationType.API,
                "tags": ["api", "reference", "programming"],
                "url": "/api",
                "user_levels": [UserLevel.ADVANCED],
                "prerequisites": ["programming_experience"],
            },
            
            # Examples
            {
                "doc_id": "configuration_examples",
                "title": "Configuration Examples",
                "content": "Example configurations for common use cases.",
                "type": DocumentationType.EXAMPLES,
                "tags": ["examples", "configuration", "templates"],
                "url": "/examples/configuration",
                "user_levels": [UserLevel.INTERMEDIATE, UserLevel.ADVANCED],
            },
        ]
        
        # Create DocumentationItem objects
        for doc_data in docs_data:
            doc_item = DocumentationItem(
                doc_id=doc_data["doc_id"],
                title=doc_data["title"],
                content=doc_data["content"],
                doc_type=DocumentationType(doc_data["type"]),
                tags=doc_data["tags"],
                url=doc_data.get("url"),
                user_levels=[UserLevel(level) for level in doc_data.get("user_levels", ["beginner", "intermediate", "advanced"])],
                prerequisites=doc_data.get("prerequisites"),
                related_items=doc_data.get("related_items"),
            )
            self.documentation_items[doc_item.doc_id] = doc_item
        
        self.logger.info(f"Initialized {len(self.documentation_items)} documentation items")
    
    def _build_search_index(self) -> None:
        """Build search index for documentation"""
        for doc_id, doc_item in self.documentation_items.items():
            # Index title words
            title_words = re.findall(r'\w+', doc_item.title.lower())
            for word in title_words:
                if word not in self.search_index:
                    self.search_index[word] = set()
                self.search_index[word].add(doc_id)
            
            # Index content words
            content_words = re.findall(r'\w+', doc_item.content.lower())
            for word in content_words:
                if word not in self.search_index:
                    self.search_index[word] = set()
                self.search_index[word].add(doc_id)
            
            # Index tags
            for tag in doc_item.tags:
                if tag not in self.search_index:
                    self.search_index[tag] = set()
                self.search_index[tag].add(doc_id)
        
        self.logger.info(f"Built search index with {len(self.search_index)} terms")
    
    def _setup_context_mapping(self) -> None:
        """Setup context-to-documentation mapping"""
        self.context_mapping = {
            "home": ["getting_started", "server_management", "general_faq"],
            "launcher": ["first_server_setup", "server_management", "configuration_examples"],
            "download": ["module_system", "getting_started"],
            "environment": ["module_development", "configuration_examples"],
            "tools": ["module_development", "api_reference"],
            "settings": ["configuration_faq", "performance_optimization"],
            "error": ["connection_troubleshooting", "general_faq"],
            "performance": ["performance_optimization"],
        }
    
    def search_documentation(self, query: str, limit: int = 10) -> List[DocumentationItem]:
        """Search documentation based on query"""
        self.search_performed.emit(query)
        
        query_words = re.findall(r'\w+', query.lower())
        if not query_words:
            return []
        
        # Find matching documents
        matching_docs: Dict[str, int] = {}
        
        for word in query_words:
            if word in self.search_index:
                for doc_id in self.search_index[word]:
                    matching_docs[doc_id] = matching_docs.get(doc_id, 0) + 1
        
        # Sort by relevance (number of matching words)
        sorted_docs = sorted(matching_docs.items(), key=lambda x: x[1], reverse=True)
        
        # Filter by user level and return DocumentationItem objects
        user_level = self.user_tracker.get_user_level()
        completed_actions = set()  # Would get from user tracker
        
        results = []
        for doc_id, score in sorted_docs[:limit]:
            doc_item = self.documentation_items[doc_id]
            if doc_item.is_relevant(user_level, completed_actions):
                results.append(doc_item)
        
        self.logger.info(f"Search for '{query}' returned {len(results)} results")
        return results
    
    def get_contextual_documentation(self, context: str, limit: int = 5) -> List[DocumentationItem]:
        """Get documentation relevant to current context"""
        if context not in self.context_mapping:
            return []
        
        doc_ids = self.context_mapping[context]
        user_level = self.user_tracker.get_user_level()
        completed_actions = set()  # Would get from user tracker
        
        relevant_docs = []
        for doc_id in doc_ids:
            if doc_id in self.documentation_items:
                doc_item = self.documentation_items[doc_id]
                if doc_item.is_relevant(user_level, completed_actions):
                    relevant_docs.append(doc_item)
        
        return relevant_docs[:limit]
    
    def get_recommended_documentation(self, limit: int = 3) -> List[DocumentationItem]:
        """Get recommended documentation based on user behavior"""
        user_level = self.user_tracker.get_user_level()
        completed_actions = set()  # Would get from user tracker
        
        # Get documentation appropriate for user level
        level_docs = []
        for doc_item in self.documentation_items.values():
            if doc_item.is_relevant(user_level, completed_actions):
                level_docs.append(doc_item)
        
        # Sort by relevance (unviewed docs first, then by type priority)
        type_priority = {
            DocumentationType.TUTORIAL: 5,
            DocumentationType.GUIDE: 4,
            DocumentationType.FAQ: 3,
            DocumentationType.REFERENCE: 2,
            DocumentationType.API: 1,
        }
        
        level_docs.sort(key=lambda d: (d.view_count == 0, type_priority.get(d.doc_type, 0)), reverse=True)
        
        return level_docs[:limit]
    
    def open_documentation(self, doc_id: str, in_app: bool = True) -> bool:
        """Open documentation item"""
        if doc_id not in self.documentation_items:
            self.logger.error(f"Documentation not found: {doc_id}")
            return False
        
        doc_item = self.documentation_items[doc_id]
        doc_item.mark_viewed()
        
        if doc_id not in self.user_history:
            self.user_history.append(doc_id)
            # Keep only last 20 items
            if len(self.user_history) > 20:
                self.user_history.pop(0)
        
        if in_app:
            self._show_in_app_documentation(doc_item)
        else:
            self._open_external_documentation(doc_item)
        
        self.documentation_opened.emit(doc_id)
        self.logger.info(f"Opened documentation: {doc_id}")
        return True
    
    def _show_in_app_documentation(self, doc_item: DocumentationItem) -> None:
        """Show documentation in-app"""
        # Create a message box or dialog with documentation content
        msg_box = MessageBox(
            title=doc_item.title,
            content=doc_item.content,
            parent=self.main_window
        )
        
        # Add button to open full documentation
        if doc_item.url:
            msg_box.yesButton.setText(tr("docs.open_full", default="Open Full Documentation"))
            msg_box.yesButton.clicked.connect(lambda: self._open_external_documentation(doc_item))
        
        msg_box.exec()
    
    def _open_external_documentation(self, doc_item: DocumentationItem) -> None:
        """Open documentation in external browser"""
        if doc_item.url:
            full_url = urljoin(self.docs_base_url, doc_item.url)
            QDesktopServices.openUrl(QUrl(full_url))
        elif doc_item.local_path:
            local_file = self.local_docs_path / doc_item.local_path
            if local_file.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(local_file)))
    
    def show_contextual_help(self, context: str, widget: Optional[QWidget] = None) -> None:
        """Show contextual help for current context"""
        self.help_requested.emit(context, "")
        
        docs = self.get_contextual_documentation(context, limit=1)
        if docs:
            doc_item = docs[0]
            
            # Show as teaching tip if widget provided
            if widget:
                tip = TeachingTip.create(
                    target=widget,
                    icon=None,
                    title=tr("docs.contextual_help", default="📖 Help"),
                    content=f"**{doc_item.title}**\n\n{doc_item.content[:200]}...",
                    isClosable=True,
                    parent=self.main_window
                )
                
                # Add button to open full documentation
                # This would require custom TeachingTip implementation
            else:
                # Show as info bar
                InfoBar.info(
                    title=tr("docs.help_available", default="📖 Help Available"),
                    content=f"{doc_item.title} - Click to open",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self.main_window
                )
    
    def get_documentation_statistics(self) -> Dict[str, Any]:
        """Get statistics about documentation usage"""
        total_docs = len(self.documentation_items)
        viewed_docs = len([d for d in self.documentation_items.values() if d.view_count > 0])
        
        type_counts = {}
        for doc_item in self.documentation_items.values():
            doc_type = doc_item.doc_type.value
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        most_viewed = sorted(
            self.documentation_items.values(),
            key=lambda d: d.view_count,
            reverse=True
        )[:5]
        
        return {
            "total_documentation": total_docs,
            "viewed_documentation": viewed_docs,
            "view_rate": (viewed_docs / total_docs) * 100 if total_docs > 0 else 0,
            "type_distribution": type_counts,
            "most_viewed": [{"id": d.doc_id, "title": d.title, "views": d.view_count} for d in most_viewed],
            "recent_history": self.user_history[-5:],
            "search_index_size": len(self.search_index),
        }
    
    def suggest_documentation_for_error(self, error_type: str, error_context: str) -> List[DocumentationItem]:
        """Suggest documentation for specific errors"""
        error_mapping = {
            "connection_error": ["connection_troubleshooting", "general_faq"],
            "configuration_error": ["configuration_faq", "configuration_examples"],
            "performance_issue": ["performance_optimization"],
            "module_error": ["module_system", "module_development"],
        }
        
        suggested_doc_ids = error_mapping.get(error_type, ["general_faq"])
        suggestions = []
        
        for doc_id in suggested_doc_ids:
            if doc_id in self.documentation_items:
                suggestions.append(self.documentation_items[doc_id])
        
        return suggestions
