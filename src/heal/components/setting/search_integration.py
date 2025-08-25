"""
Settings Search Integration
Integrates search functionality with existing settings interface
"""

import time
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon

from src.heal.common.logging_config import get_logger
from src.heal.models.setting_card import SettingCardGroup
from .performance_manager import get_performance_manager
from .search_engine import (
    FilterType,
    SearchResult,
    SearchType,
    SettingItem,
    SettingsSearchEngine,
)
from .search_ui import SettingsSearchWidget


class SettingsSearchIntegrator(QObject):
    """Integrates search functionality with settings interface"""

    # Signals
    search_mode_changed = Signal(bool)  # True when search is active
    setting_found = Signal(str, object)  # setting_key, widget

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.logger = get_logger("search_integrator", module="SettingsSearchIntegrator")

        # Search components
        self.search_engine = SettingsSearchEngine()
        self.search_widget = SettingsSearchWidget(self.search_engine)

        # Settings registry
        self.settings_registry: Dict[str, SettingItem] = {}
        self.widget_registry: Dict[str, QWidget] = {}
        self.category_mapping: Dict[str, str] = {}

        # Performance integration
        self.performance_manager = get_performance_manager()

        # Connect signals
        self.search_widget.setting_selected.connect(self.on_setting_selected)
        self.search_widget.search_mode_changed.connect(self.search_mode_changed)

        self.logger.info("Settings search integrator initialized")

    def register_setting_interface(
        self, interface_name: str, interface: SettingCardGroup
    ) -> None:
        """Register a settings interface for search indexing"""
        try:
            # Extract settings from the interface
            settings = self._extract_settings_from_interface(interface, interface_name)

            # Add to search index
            for setting in settings:
                self.search_engine.add_setting(setting)
                self.settings_registry[setting.key] = setting

            self.logger.info(
                f"Registered {len(settings)} settings from {interface_name}"
            )

        except Exception as e:
            self.logger.error(f"Failed to register interface {interface_name}: {e}")

    def _extract_settings_from_interface(
        self, interface: SettingCardGroup, category: str
    ) -> List[SettingItem]:
        """Extract setting items from a settings interface"""
        settings = []

        # Iterate through all widgets in the interface
        for i in range(interface.cardLayout.count()):
            item = interface.cardLayout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                setting_item = self._create_setting_item_from_widget(widget, category)
                if setting_item:
                    settings.append(setting_item)
                    # Store widget reference for navigation
                    self.widget_registry[setting_item.key] = widget

        return settings

    def _create_setting_item_from_widget(
        self, widget: QWidget, category: str
    ) -> Optional[SettingItem]:
        """Create a SettingItem from a widget"""
        try:
            # Extract information from different widget types
            title = ""
            description = ""
            setting_type = "unknown"
            value = None

            # Handle different setting card types
            if hasattr(widget, "titleLabel") and hasattr(widget, "contentLabel"):
                title = widget.titleLabel.text() if widget.titleLabel else ""
                description = widget.contentLabel.text() if widget.contentLabel else ""

            # Determine setting type based on widget class
            widget_class = widget.__class__.__name__
            if "Switch" in widget_class:
                setting_type = "switch"
                value = getattr(widget, "isChecked", lambda: False)()
            elif "ComboBox" in widget_class:
                setting_type = "combo"
                value = getattr(widget, "currentText", lambda: "")()
            elif "Push" in widget_class or "Button" in widget_class:
                setting_type = "button"
            elif "Color" in widget_class:
                setting_type = "color"
            elif "LineEdit" in widget_class:
                setting_type = "text"
                value = getattr(widget, "text", lambda: "")()

            # Generate unique key
            key = f"{category.lower()}_{title.lower().replace(' ', '_')}"

            # Create setting item
            setting_item = SettingItem(
                key=key,
                title=title,
                description=description,
                category=category,
                setting_type=setting_type,
                value=value,
                widget=widget,
            )

            return setting_item

        except Exception as e:
            self.logger.error(f"Failed to create setting item from widget: {e}")
            return None

    def register_custom_setting(
        self,
        key: str,
        title: str,
        description: str,
        category: str,
        setting_type: str,
        value: Any | None = None,
        widget: QWidget | None = None,
        keywords: List[str] | None = None,
    ) -> None:
        """Register a custom setting item"""
        setting_item = SettingItem(
            key=key,
            title=title,
            description=description,
            category=category,
            setting_type=setting_type,
            value=value,
            widget=widget,
            keywords=keywords or [],
        )

        self.search_engine.add_setting(setting_item)
        self.settings_registry[key] = setting_item

        if widget:
            self.widget_registry[key] = widget

        self.logger.debug(f"Registered custom setting: {key}")

    def update_setting_value(self, key: str, new_value: Any) -> None:
        """Update a setting value in the search index"""
        if key in self.settings_registry:
            setting_item = self.settings_registry[key]
            setting_item.value = new_value
            setting_item.last_modified = time.time()

            # Update in search engine
            self.search_engine.update_setting(setting_item)

            self.logger.debug(f"Updated setting value: {key}")

    def mark_setting_as_favorite(self, key: str, is_favorite: bool = True) -> None:
        """Mark a setting as favorite"""
        if key in self.settings_registry:
            setting_item = self.settings_registry[key]
            setting_item.is_favorite = is_favorite

            # Update in search engine
            self.search_engine.update_setting(setting_item)

            self.logger.debug(f"Marked setting as favorite: {key} = {is_favorite}")

    def on_setting_selected(self, setting_item: SettingItem) -> None:
        """Handle setting selection from search results"""
        try:
            # Find the widget associated with this setting
            widget = self.widget_registry.get(setting_item.key)
            if widget:
                # Emit signal to navigate to the setting
                self.setting_found.emit(setting_item.key, widget)

                # Scroll to the widget if possible
                self._scroll_to_widget(widget)

                # Highlight the widget temporarily
                self._highlight_widget(widget)

                self.logger.info(f"Navigated to setting: {setting_item.title}")
            else:
                self.logger.warning(f"Widget not found for setting: {setting_item.key}")

        except Exception as e:
            self.logger.error(f"Failed to navigate to setting: {e}")

    def _scroll_to_widget(self, widget: QWidget) -> None:
        """Scroll to make the widget visible"""
        try:
            # Find the scroll area parent
            parent = widget.parent()
            while parent:
                if hasattr(parent, "ensureWidgetVisible"):
                    parent.ensureWidgetVisible(widget)
                    break
                parent = parent.parent()
        except Exception as e:
            self.logger.debug(f"Could not scroll to widget: {e}")

    def _highlight_widget(self, widget: QWidget) -> None:
        """Temporarily highlight a widget"""
        try:
            # Store original style
            original_style = widget.styleSheet()

            # Apply highlight style
            highlight_style = """
                border: 2px solid #0078d4;
                border-radius: 4px;
                background-color: rgba(0, 120, 212, 0.1);
            """
            widget.setStyleSheet(original_style + highlight_style)

            # Remove highlight after delay
            QTimer.singleShot(2000, lambda: widget.setStyleSheet(original_style))

        except Exception as e:
            self.logger.debug(f"Could not highlight widget: {e}")

    def get_search_widget(self) -> SettingsSearchWidget:
        """Get the search widget for UI integration"""
        return self.search_widget

    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search statistics"""
        engine_stats = self.search_engine.get_statistics()

        return {
            "search_engine": engine_stats,
            "registered_settings": len(self.settings_registry),
            "widget_mappings": len(self.widget_registry),
            "categories": len(
                set(item.category for item in self.settings_registry.values())
            ),
        }

    def export_settings_index(self) -> Dict[str, Any]:
        """Export the settings index for debugging or backup"""
        return {
            "settings": {
                key: {
                    "title": item.title,
                    "description": item.description,
                    "category": item.category,
                    "type": item.setting_type,
                    "keywords": item.keywords,
                    "is_favorite": item.is_favorite,
                }
                for key, item in self.settings_registry.items()
            },
            "statistics": self.get_search_statistics(),
        }

    def import_favorites(self, favorites: Dict[str, bool]) -> None:
        """Import favorite settings"""
        for key, is_favorite in favorites.items():
            self.mark_setting_as_favorite(key, is_favorite)

        self.logger.info(f"Imported {len(favorites)} favorite settings")

    def clear_search_index(self) -> None:
        """Clear the search index"""
        self.search_engine.clear_index()
        self.settings_registry.clear()
        self.widget_registry.clear()
        self.logger.info("Cleared search index")

    def rebuild_search_index(self, interfaces: Dict[str, SettingCardGroup]) -> None:
        """Rebuild the search index from interfaces"""
        self.clear_search_index()

        for name, interface in interfaces.items():
            self.register_setting_interface(name, interface)

        self.logger.info(f"Rebuilt search index with {len(interfaces)} interfaces")


class SearchEnabledSettingsInterface:
    """Mixin class to add search functionality to settings interfaces"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.search_integrator = SettingsSearchIntegrator()
        self.search_widget = self.search_integrator.get_search_widget()
        self.original_interfaces: dict[str, Any] = {}

        # Connect search signals
        self.search_integrator.search_mode_changed.connect(self.on_search_mode_changed)
        self.search_integrator.setting_found.connect(self.on_setting_found)

    def add_search_to_layout(self, layout: QVBoxLayout) -> None:
        """Add search widget to the layout"""
        # Insert search widget at the top
        layout.insertWidget(0, self.search_widget)

    def register_interfaces_for_search(self, interfaces: Dict[str, SettingCardGroup]) -> None:
        """Register all interfaces for search"""
        self.original_interfaces = interfaces
        self.search_integrator.rebuild_search_index(interfaces)

    def on_search_mode_changed(self, is_search_active: bool) -> None:
        """Handle search mode changes"""
        # Override in subclass to handle search mode changes
        # For example, hide/show normal interface tabs
        pass

    def on_setting_found(self, setting_key: str, widget: QWidget) -> None:
        """Handle setting found from search"""
        # Override in subclass to handle navigation to found settings
        # For example, switch to the appropriate tab and scroll to widget
        pass


# Global search integrator instance
_search_integrator: Optional[SettingsSearchIntegrator] = None


def get_search_integrator() -> SettingsSearchIntegrator:
    """Get global search integrator instance"""
    global _search_integrator
    if _search_integrator is None:
        _search_integrator = SettingsSearchIntegrator()
    return _search_integrator


def register_setting_for_search(
    key: str,
    title: str,
    description: str,
    category: str,
    setting_type: str,
    value: Any | None = None,
    widget: QWidget | None = None,
    keywords: List[str] | None = None,
) -> None:
    """Convenience function to register a setting for search"""
    integrator = get_search_integrator()
    integrator.register_custom_setting(
        key, title, description, category, setting_type, value, widget, keywords
    )
