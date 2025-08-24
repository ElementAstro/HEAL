# Component Development Guide

## 📋 Quick Start Guide

This guide provides practical examples for developing new components within the HEAL application's modular architecture.

## 🛠️ Creating a New Component Module

### Step 1: Create Component Directory

```bash
# Create new component directory
mkdir app/components/my_component
```

### Step 2: Create Component Files

```python
# app/components/my_component/__init__.py
"""
My Component Module
Exports for the my_component module
"""

from .component_manager import ComponentManager
from .data_manager import DataManager
from .ui_manager import UIManager
from .signal_manager import SignalManager

__all__ = [
    'ComponentManager',
    'DataManager', 
    'UIManager',
    'SignalManager'
]
```

### Step 3: Create Manager Classes

```python
# app/components/my_component/component_manager.py
"""
Component Manager - Main component orchestration
"""

from PySide6.QtCore import QObject, Signal
from typing import Optional, Any

from app.common.logging_config import get_logger
from .data_manager import DataManager
from .ui_manager import UIManager
from .signal_manager import SignalManager

logger = get_logger(__name__)


class ComponentManager(QObject):
    """Main component manager for coordinating all component operations"""
    
    # Define signals
    component_updated = Signal(object)
    component_error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Initialize sub-managers
        self.data_manager = DataManager(self)
        self.ui_manager = UIManager(self)
        self.signal_manager = SignalManager(self)
        
        # Initialize component
        self.init_component()
    
    def init_component(self):
        """Initialize the component"""
        try:
            logger.info("Initializing component manager")
            
            # Initialize data
            self.data_manager.init_data()
            
            # Connect signals
            self.signal_manager.connect_signals()
            
            logger.info("Component manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing component manager: {e}")
            self.component_error.emit(str(e))
    
    def setup_ui(self):
        """Setup UI components"""
        try:
            self.ui_manager.setup_ui()
            logger.info("UI setup completed")
        except Exception as e:
            logger.error(f"Error setting up UI: {e}")
            self.component_error.emit(str(e))
    
    def handle_operation(self, operation_data: Any):
        """Handle component operations"""
        try:
            result = self.data_manager.process_operation(operation_data)
            self.component_updated.emit(result)
            return result
        except Exception as e:
            logger.error(f"Error handling operation: {e}")
            self.component_error.emit(str(e))
            return None
    
    def cleanup(self):
        """Cleanup component resources"""
        try:
            self.data_manager.cleanup()
            self.ui_manager.cleanup()
            self.signal_manager.cleanup()
            logger.info("Component cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
```

```python
# app/components/my_component/data_manager.py
"""
Data Manager - Handles data operations and state management
"""

from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from app.common.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ComponentData:
    """Data structure for component state"""
    id: str
    name: str
    status: str = "inactive"
    properties: Dict[str, Any] = field(default_factory=dict)
    last_updated: Optional[str] = None


class DataManager(QObject):
    """Manages component data and state"""
    
    # Define signals
    data_updated = Signal(object)
    data_error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.data_store: Dict[str, ComponentData] = {}
        self.config = {}
    
    def init_data(self):
        """Initialize data structures"""
        try:
            # Load configuration
            self.load_config()
            
            # Initialize data store
            self.data_store = {}
            
            logger.info("Data manager initialized")
            
        except Exception as e:
            logger.error(f"Error initializing data manager: {e}")
            self.data_error.emit(str(e))
    
    def load_config(self):
        """Load component configuration"""
        try:
            # Load from config file or database
            self.config = {
                'auto_update': True,
                'cache_size': 100,
                'timeout': 30
            }
            logger.info("Configuration loaded")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def add_item(self, item_id: str, name: str, properties: Dict[str, Any] = None) -> bool:
        """Add new item to data store"""
        try:
            if item_id in self.data_store:
                logger.warning(f"Item {item_id} already exists")
                return False
            
            item = ComponentData(
                id=item_id,
                name=name,
                properties=properties or {}
            )
            
            self.data_store[item_id] = item
            self.data_updated.emit(item)
            
            logger.info(f"Added item: {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding item {item_id}: {e}")
            self.data_error.emit(str(e))
            return False
    
    def get_item(self, item_id: str) -> Optional[ComponentData]:
        """Get item from data store"""
        return self.data_store.get(item_id)
    
    def get_all_items(self) -> List[ComponentData]:
        """Get all items from data store"""
        return list(self.data_store.values())
    
    def update_item(self, item_id: str, properties: Dict[str, Any]) -> bool:
        """Update item properties"""
        try:
            if item_id not in self.data_store:
                logger.warning(f"Item {item_id} not found")
                return False
            
            item = self.data_store[item_id]
            item.properties.update(properties)
            
            self.data_updated.emit(item)
            logger.info(f"Updated item: {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating item {item_id}: {e}")
            self.data_error.emit(str(e))
            return False
    
    def remove_item(self, item_id: str) -> bool:
        """Remove item from data store"""
        try:
            if item_id not in self.data_store:
                logger.warning(f"Item {item_id} not found")
                return False
            
            del self.data_store[item_id]
            logger.info(f"Removed item: {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing item {item_id}: {e}")
            self.data_error.emit(str(e))
            return False
    
    def process_operation(self, operation_data: Any) -> Any:
        """Process component operation"""
        try:
            # Implement operation logic here
            operation_type = operation_data.get('type', 'unknown')
            
            if operation_type == 'add':
                return self.add_item(
                    operation_data['id'],
                    operation_data['name'],
                    operation_data.get('properties', {})
                )
            elif operation_type == 'update':
                return self.update_item(
                    operation_data['id'],
                    operation_data['properties']
                )
            elif operation_type == 'remove':
                return self.remove_item(operation_data['id'])
            else:
                logger.warning(f"Unknown operation type: {operation_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing operation: {e}")
            self.data_error.emit(str(e))
            return None
    
    def cleanup(self):
        """Cleanup data manager resources"""
        try:
            self.data_store.clear()
            logger.info("Data manager cleanup completed")
        except Exception as e:
            logger.error(f"Error during data manager cleanup: {e}")
```

```python
# app/components/my_component/ui_manager.py
"""
UI Manager - Handles user interface components and interactions
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import (
    CardWidget, PushButton, BodyLabel, SubtitleLabel,
    InfoBar, InfoBarPosition, MessageBox
)

from app.common.logging_config import get_logger

logger = get_logger(__name__)


class ComponentCard(CardWidget):
    """Custom card widget for component items"""
    
    item_clicked = Signal(str)
    item_updated = Signal(str, dict)
    
    def __init__(self, item_id: str, item_name: str, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.item_name = item_name
        self.setup_ui()
    
    def setup_ui(self):
        """Setup card UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = SubtitleLabel(self.item_name)
        layout.addWidget(title_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.edit_button = PushButton("Edit")
        self.edit_button.clicked.connect(self.on_edit_clicked)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = PushButton("Delete")
        self.delete_button.clicked.connect(self.on_delete_clicked)
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def on_edit_clicked(self):
        """Handle edit button click"""
        self.item_clicked.emit(self.item_id)
    
    def on_delete_clicked(self):
        """Handle delete button click"""
        # Show confirmation dialog
        result = MessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {self.item_name}?",
            MessageBox.Yes | MessageBox.No
        )
        
        if result == MessageBox.Yes:
            self.item_updated.emit(self.item_id, {'action': 'delete'})


class UIManager(QObject):
    """Manages UI components and interactions"""
    
    # Define signals
    ui_updated = Signal()
    ui_error = Signal(str)
    user_action = Signal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.main_widget = None
        self.cards = {}
    
    def setup_ui(self):
        """Setup main UI components"""
        try:
            if not self.parent or not hasattr(self.parent, 'parent'):
                logger.warning("No parent widget available for UI setup")
                return
            
            # Create main widget
            self.main_widget = QWidget()
            layout = QVBoxLayout(self.main_widget)
            
            # Header
            header_label = SubtitleLabel("My Component")
            layout.addWidget(header_label)
            
            # Add button
            add_button = PushButton("Add Item")
            add_button.clicked.connect(self.on_add_clicked)
            layout.addWidget(add_button)
            
            # Cards container
            self.cards_widget = QWidget()
            self.cards_layout = QVBoxLayout(self.cards_widget)
            layout.addWidget(self.cards_widget)
            
            logger.info("UI setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up UI: {e}")
            self.ui_error.emit(str(e))
    
    def add_card(self, item_id: str, item_name: str):
        """Add new card to UI"""
        try:
            if item_id in self.cards:
                logger.warning(f"Card {item_id} already exists")
                return
            
            card = ComponentCard(item_id, item_name)
            card.item_clicked.connect(self.on_card_clicked)
            card.item_updated.connect(self.on_card_updated)
            
            self.cards[item_id] = card
            self.cards_layout.addWidget(card)
            
            logger.info(f"Added card: {item_id}")
            
        except Exception as e:
            logger.error(f"Error adding card {item_id}: {e}")
            self.ui_error.emit(str(e))
    
    def remove_card(self, item_id: str):
        """Remove card from UI"""
        try:
            if item_id not in self.cards:
                logger.warning(f"Card {item_id} not found")
                return
            
            card = self.cards[item_id]
            self.cards_layout.removeWidget(card)
            card.deleteLater()
            del self.cards[item_id]
            
            logger.info(f"Removed card: {item_id}")
            
        except Exception as e:
            logger.error(f"Error removing card {item_id}: {e}")
            self.ui_error.emit(str(e))
    
    def on_add_clicked(self):
        """Handle add button click"""
        self.user_action.emit('add_item', {})
    
    def on_card_clicked(self, item_id: str):
        """Handle card click"""
        self.user_action.emit('edit_item', {'id': item_id})
    
    def on_card_updated(self, item_id: str, data: dict):
        """Handle card update"""
        self.user_action.emit('update_item', {'id': item_id, 'data': data})
    
    def show_message(self, title: str, message: str, success: bool = True):
        """Show info message"""
        try:
            if success:
                InfoBar.success(
                    title=title,
                    content=message,
                    orient=InfoBarPosition.TOP,
                    isClosable=True,
                    parent=self.main_widget
                )
            else:
                InfoBar.error(
                    title=title,
                    content=message,
                    orient=InfoBarPosition.TOP,
                    isClosable=True,
                    parent=self.main_widget
                )
        except Exception as e:
            logger.error(f"Error showing message: {e}")
    
    def cleanup(self):
        """Cleanup UI resources"""
        try:
            for card in self.cards.values():
                card.deleteLater()
            self.cards.clear()
            
            if self.main_widget:
                self.main_widget.deleteLater()
                self.main_widget = None
            
            logger.info("UI manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during UI manager cleanup: {e}")
```

```python
# app/components/my_component/signal_manager.py
"""
Signal Manager - Handles signal connections and event coordination
"""

from PySide6.QtCore import QObject, Signal

from app.common.logging_config import get_logger

logger = get_logger(__name__)


class SignalManager(QObject):
    """Manages signal connections and event coordination"""
    
    # Define global signals
    component_ready = Signal()
    component_error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.connections = []
    
    def connect_signals(self):
        """Connect all component signals"""
        try:
            if not self.parent:
                logger.warning("No parent available for signal connections")
                return
            
            # Connect data manager signals
            if hasattr(self.parent, 'data_manager'):
                connection = self.parent.data_manager.data_updated.connect(
                    self.on_data_updated
                )
                self.connections.append(connection)
                
                connection = self.parent.data_manager.data_error.connect(
                    self.on_data_error
                )
                self.connections.append(connection)
            
            # Connect UI manager signals
            if hasattr(self.parent, 'ui_manager'):
                connection = self.parent.ui_manager.user_action.connect(
                    self.on_user_action
                )
                self.connections.append(connection)
                
                connection = self.parent.ui_manager.ui_error.connect(
                    self.on_ui_error
                )
                self.connections.append(connection)
            
            logger.info("Signal connections established")
            
        except Exception as e:
            logger.error(f"Error connecting signals: {e}")
            self.component_error.emit(str(e))
    
    def on_data_updated(self, data):
        """Handle data update signal"""
        try:
            logger.info(f"Data updated: {data}")
            
            # Update UI if needed
            if hasattr(self.parent, 'ui_manager') and hasattr(data, 'id'):
                self.parent.ui_manager.add_card(data.id, data.name)
            
        except Exception as e:
            logger.error(f"Error handling data update: {e}")
            self.component_error.emit(str(e))
    
    def on_data_error(self, error: str):
        """Handle data error signal"""
        logger.error(f"Data error: {error}")
        
        # Show error message in UI
        if hasattr(self.parent, 'ui_manager'):
            self.parent.ui_manager.show_message(
                "Data Error",
                error,
                success=False
            )
        
        self.component_error.emit(error)
    
    def on_user_action(self, action: str, data: dict):
        """Handle user action signal"""
        try:
            logger.info(f"User action: {action}, data: {data}")
            
            # Process action through component manager
            if hasattr(self.parent, 'handle_operation'):
                operation_data = {
                    'type': action,
                    **data
                }
                self.parent.handle_operation(operation_data)
            
        except Exception as e:
            logger.error(f"Error handling user action: {e}")
            self.component_error.emit(str(e))
    
    def on_ui_error(self, error: str):
        """Handle UI error signal"""
        logger.error(f"UI error: {error}")
        self.component_error.emit(error)
    
    def cleanup(self):
        """Cleanup signal connections"""
        try:
            # Disconnect all connections
            for connection in self.connections:
                if connection:
                    self.disconnect(connection)
            
            self.connections.clear()
            logger.info("Signal manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during signal manager cleanup: {e}")
```

## 📝 Integration Example

```python
# app/my_new_interface.py
"""
New Interface using the component system
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from app.components.my_component import ComponentManager
from app.common.logging_config import get_logger

logger = get_logger(__name__)


class MyNewInterface(QWidget):
    """New interface using modular components"""
    
    # Define interface signals
    navigate_to = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        # Initialize component manager
        self.component_manager = ComponentManager(self)
        
        # Setup UI
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()
    
    def setup_ui(self):
        """Setup interface UI"""
        try:
            layout = QVBoxLayout(self)
            
            # Setup component UI
            self.component_manager.setup_ui()
            
            # Add component widget to layout
            if self.component_manager.ui_manager.main_widget:
                layout.addWidget(self.component_manager.ui_manager.main_widget)
            
            logger.info("Interface UI setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up interface UI: {e}")
    
    def connect_signals(self):
        """Connect interface signals"""
        try:
            # Connect component signals
            self.component_manager.component_updated.connect(
                self.on_component_updated
            )
            self.component_manager.component_error.connect(
                self.on_component_error
            )
            
            logger.info("Interface signals connected")
            
        except Exception as e:
            logger.error(f"Error connecting interface signals: {e}")
    
    def on_component_updated(self, data):
        """Handle component update"""
        logger.info(f"Component updated: {data}")
        
        # Handle update logic here
        pass
    
    def on_component_error(self, error: str):
        """Handle component error"""
        logger.error(f"Component error: {error}")
        
        # Handle error display/recovery here
        pass
    
    def closeEvent(self, event):
        """Handle interface close event"""
        try:
            # Cleanup component
            self.component_manager.cleanup()
            
            # Accept close event
            event.accept()
            
        except Exception as e:
            logger.error(f"Error during interface close: {e}")
            event.accept()
```

## 🧪 Testing Example

```python
# tests/test_my_component.py
"""
Test suite for my_component
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication

from app.components.my_component import (
    ComponentManager, DataManager, UIManager, SignalManager
)
from app.components.my_component.data_manager import ComponentData


class TestDataManager:
    """Test data manager functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.data_manager = DataManager()
        self.data_manager.init_data()
    
    def test_add_item(self):
        """Test adding item to data store"""
        result = self.data_manager.add_item("test_1", "Test Item")
        assert result is True
        assert "test_1" in self.data_manager.data_store
        
        item = self.data_manager.get_item("test_1")
        assert item is not None
        assert item.name == "Test Item"
    
    def test_add_duplicate_item(self):
        """Test adding duplicate item"""
        self.data_manager.add_item("test_1", "Test Item")
        result = self.data_manager.add_item("test_1", "Duplicate Item")
        assert result is False
    
    def test_update_item(self):
        """Test updating item properties"""
        self.data_manager.add_item("test_1", "Test Item")
        
        result = self.data_manager.update_item("test_1", {"status": "active"})
        assert result is True
        
        item = self.data_manager.get_item("test_1")
        assert item.properties["status"] == "active"
    
    def test_remove_item(self):
        """Test removing item from data store"""
        self.data_manager.add_item("test_1", "Test Item")
        
        result = self.data_manager.remove_item("test_1")
        assert result is True
        assert "test_1" not in self.data_manager.data_store
    
    def test_get_all_items(self):
        """Test getting all items"""
        self.data_manager.add_item("test_1", "Test Item 1")
        self.data_manager.add_item("test_2", "Test Item 2")
        
        items = self.data_manager.get_all_items()
        assert len(items) == 2
        assert any(item.id == "test_1" for item in items)
        assert any(item.id == "test_2" for item in items)


class TestComponentManager:
    """Test component manager functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.component_manager = ComponentManager()
    
    def test_initialization(self):
        """Test component manager initialization"""
        assert self.component_manager.data_manager is not None
        assert self.component_manager.ui_manager is not None
        assert self.component_manager.signal_manager is not None
    
    @patch('app.components.my_component.component_manager.logger')
    def test_handle_operation_add(self, mock_logger):
        """Test handling add operation"""
        operation_data = {
            'type': 'add',
            'id': 'test_1',
            'name': 'Test Item'
        }
        
        result = self.component_manager.handle_operation(operation_data)
        assert result is True
        
        item = self.component_manager.data_manager.get_item("test_1")
        assert item is not None
        assert item.name == "Test Item"
    
    def test_handle_operation_unknown(self):
        """Test handling unknown operation"""
        operation_data = {
            'type': 'unknown_operation'
        }
        
        result = self.component_manager.handle_operation(operation_data)
        assert result is False


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__])
```

## 🚀 Best Practices

### 1. **Component Separation**

- Keep managers focused on single responsibilities
- Use clear interfaces between components
- Minimize dependencies between managers

### 2. **Error Handling**

- Always use try-except blocks in manager methods
- Emit error signals for UI feedback
- Log errors with appropriate levels

### 3. **Signal Management**

- Use typed signals with clear naming
- Connect signals in signal manager
- Properly disconnect on cleanup

### 4. **Testing**

- Write unit tests for each manager
- Test signal connections and data flow
- Mock external dependencies

### 5. **Documentation**

- Document all public methods and signals
- Include usage examples
- Keep documentation up to date

This guide provides a complete framework for developing new components within the HEAL application's modular architecture. Follow these patterns for consistent, maintainable code.
