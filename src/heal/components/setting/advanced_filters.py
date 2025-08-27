"""
Advanced Filter Options for Settings Search
Provides sophisticated filtering capabilities beyond basic category and type filters
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    CheckBox,
    ComboBox,
    DatePicker,
    FluentIcon,
    Slider,
    SpinBox,
    ToggleButton,
)

from src.heal.common.logging_config import get_logger
from .search_engine import FilterType, SearchFilter, SettingItem


class AdvancedFilterType(Enum):
    """Advanced filter types"""

    VALUE_RANGE = "value_range"
    DATE_RANGE = "date_range"
    USAGE_FREQUENCY = "usage_frequency"
    COMPLEXITY_LEVEL = "complexity_level"
    DEPENDENCY = "dependency"
    CUSTOM_FUNCTION = "custom_function"


@dataclass
class AdvancedFilter:
    """Advanced filter configuration"""

    filter_type: AdvancedFilterType
    name: str
    description: str
    filter_function: Callable[[SettingItem], bool]
    enabled: bool = True
    parameters: Optional[Dict[str, Any]] = None


class ValueRangeFilter(CardWidget):
    """Filter settings by value ranges (for numeric settings)"""

    filter_changed = Signal(object)  # AdvancedFilter

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger("value_range_filter", module="ValueRangeFilter")
        self.min_value = 0
        self.max_value = 100
        self.current_min = 0
        self.current_max = 100
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the value range filter UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header
        header = BodyLabel("Value Range")
        layout.addWidget(header)

        desc = CaptionLabel("Filter numeric settings by value range")
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # Range sliders (using two separate sliders for min/max)
        range_layout = QHBoxLayout()

        # Min slider
        min_label = BodyLabel("Min:")
        range_layout.addWidget(min_label)
        self.min_slider = Slider(Qt.Orientation.Horizontal)
        self.min_slider.setRange(0, 100)
        self.min_slider.setValue(0)
        self.min_slider.valueChanged.connect(self.on_range_changed)
        range_layout.addWidget(self.min_slider)

        # Max slider
        max_label = BodyLabel("Max:")
        range_layout.addWidget(max_label)
        self.max_slider = Slider(Qt.Orientation.Horizontal)
        self.max_slider.setRange(0, 100)
        self.max_slider.setValue(100)
        self.max_slider.valueChanged.connect(self.on_range_changed)
        range_layout.addWidget(self.max_slider)

        layout.addLayout(range_layout)

        # Value labels
        value_layout = QHBoxLayout()
        self.min_label = CaptionLabel("0")
        self.max_label = CaptionLabel("100")
        value_layout.addWidget(self.min_label)
        value_layout.addStretch()
        value_layout.addWidget(self.max_label)
        layout.addLayout(value_layout)

    def on_range_changed(self, value: int) -> None:
        """Handle range change"""
        # Get values from both sliders
        min_val = self.min_slider.value()
        max_val = self.max_slider.value()

        # Ensure min <= max
        if min_val > max_val:
            if self.sender() == self.min_slider:
                self.max_slider.setValue(min_val)
                max_val = min_val
            else:
                self.min_slider.setValue(max_val)
                min_val = max_val

        self.current_min, self.current_max = min_val, max_val
        self.min_label.setText(str(self.current_min))
        self.max_label.setText(str(self.current_max))

        # Create filter function
        def value_filter(item: SettingItem) -> bool:
            try:
                if isinstance(item.value, (int, float)):
                    return self.current_min <= item.value <= self.current_max
                return True  # Non-numeric values pass through
            except:
                return True

        advanced_filter = AdvancedFilter(
            filter_type=AdvancedFilterType.VALUE_RANGE,
            name="Value Range",
            description=f"Values between {self.current_min} and {self.current_max}",
            filter_function=value_filter,
        )

        self.filter_changed.emit(advanced_filter)


class DateRangeFilter(CardWidget):
    """Filter settings by modification date range"""

    filter_changed = Signal(object)  # AdvancedFilter

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger("date_range_filter", module="DateRangeFilter")
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the date range filter UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header
        header = BodyLabel("Date Range")
        layout.addWidget(header)

        desc = CaptionLabel("Filter by when settings were last modified")
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # Date range controls
        date_layout = QHBoxLayout()

        # From date
        date_layout.addWidget(QLabel("From:"))
        self.from_date = DatePicker()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.dateChanged.connect(self.on_date_changed)
        date_layout.addWidget(self.from_date)

        # To date
        date_layout.addWidget(QLabel("To:"))
        self.to_date = DatePicker()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.dateChanged.connect(self.on_date_changed)
        date_layout.addWidget(self.to_date)

        layout.addLayout(date_layout)

    def on_date_changed(self) -> None:
        """Handle date change"""
        from_timestamp = self.from_date.date().toPython().timestamp()
        to_timestamp = self.to_date.date().toPython().timestamp() + 86400  # End of day

        def date_filter(item: SettingItem) -> bool:
            # last_modified is always a float, so no need to check isinstance
            return bool(from_timestamp <= item.last_modified <= to_timestamp)

        advanced_filter = AdvancedFilter(
            filter_type=AdvancedFilterType.DATE_RANGE,
            name="Date Range",
            description=f"Modified between {self.from_date.date().toString()} and {self.to_date.date().toString()}",
            filter_function=date_filter,
        )

        self.filter_changed.emit(advanced_filter)


class ComplexityFilter(CardWidget):
    """Filter settings by complexity level"""

    filter_changed = Signal(object)  # AdvancedFilter

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger("complexity_filter", module="ComplexityFilter")
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the complexity filter UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header
        header = BodyLabel("Complexity Level")
        layout.addWidget(header)

        desc = CaptionLabel(
            "Filter by setting complexity (basic, intermediate, advanced)"
        )
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # Complexity options
        self.button_group = QButtonGroup()
        options_layout = QVBoxLayout()

        self.all_radio = QRadioButton("All Settings")
        self.all_radio.setChecked(True)
        self.all_radio.toggled.connect(self.on_complexity_changed)
        self.button_group.addButton(self.all_radio)
        options_layout.addWidget(self.all_radio)

        self.basic_radio = QRadioButton("Basic Settings Only")
        self.basic_radio.toggled.connect(self.on_complexity_changed)
        self.button_group.addButton(self.basic_radio)
        options_layout.addWidget(self.basic_radio)

        self.advanced_radio = QRadioButton("Advanced Settings Only")
        self.advanced_radio.toggled.connect(self.on_complexity_changed)
        self.button_group.addButton(self.advanced_radio)
        options_layout.addWidget(self.advanced_radio)

        layout.addLayout(options_layout)

    def on_complexity_changed(self) -> None:
        """Handle complexity filter change"""
        if self.all_radio.isChecked():
            filter_function = lambda item: True
            description = "All complexity levels"
        elif self.basic_radio.isChecked():
            filter_function = lambda item: not item.is_advanced
            description = "Basic settings only"
        else:  # advanced_radio
            filter_function = lambda item: item.is_advanced
            description = "Advanced settings only"

        advanced_filter = AdvancedFilter(
            filter_type=AdvancedFilterType.COMPLEXITY_LEVEL,
            name="Complexity Level",
            description=description,
            filter_function=filter_function,
        )

        self.filter_changed.emit(advanced_filter)


class UsageFrequencyFilter(CardWidget):
    """Filter settings by usage frequency"""

    filter_changed = Signal(object)  # AdvancedFilter

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(
            "usage_frequency_filter", module="UsageFrequencyFilter"
        )
        self.usage_stats: Dict[str, int] = {}  # setting_key -> access_count
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the usage frequency filter UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header
        header = BodyLabel("Usage Frequency")
        layout.addWidget(header)

        desc = CaptionLabel("Filter by how frequently settings are accessed")
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # Frequency options
        self.frequency_combo = ComboBox()
        self.frequency_combo.addItems(
            [
                "All Settings",
                "Frequently Used (>10 times)",
                "Moderately Used (3-10 times)",
                "Rarely Used (1-2 times)",
                "Never Used",
            ]
        )
        self.frequency_combo.currentTextChanged.connect(self.on_frequency_changed)
        layout.addWidget(self.frequency_combo)

    def update_usage_stats(self, stats: Dict[str, int]) -> None:
        """Update usage statistics"""
        self.usage_stats = stats
        self.on_frequency_changed()

    def on_frequency_changed(self) -> None:
        """Handle frequency filter change"""
        selection = self.frequency_combo.currentText()

        if selection == "All Settings":
            filter_function = lambda item: True
        elif selection == "Frequently Used (>10 times)":
            filter_function = lambda item: self.usage_stats.get(item.key, 0) > 10
        elif selection == "Moderately Used (3-10 times)":
            filter_function = lambda item: 3 <= self.usage_stats.get(item.key, 0) <= 10
        elif selection == "Rarely Used (1-2 times)":
            filter_function = lambda item: 1 <= self.usage_stats.get(item.key, 0) <= 2
        else:  # Never Used
            filter_function = lambda item: self.usage_stats.get(item.key, 0) == 0

        advanced_filter = AdvancedFilter(
            filter_type=AdvancedFilterType.USAGE_FREQUENCY,
            name="Usage Frequency",
            description=selection,
            filter_function=filter_function,
        )

        self.filter_changed.emit(advanced_filter)


class CustomFilterBuilder(CardWidget):
    """Build custom filters using a simple query language"""

    filter_changed = Signal(object)  # AdvancedFilter

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger("custom_filter_builder", module="CustomFilterBuilder")
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the custom filter builder UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header
        header = BodyLabel("Custom Filter")
        layout.addWidget(header)

        desc = CaptionLabel("Build custom filters using simple expressions")
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # Examples
        examples = CaptionLabel(
            "Examples:\n"
            "• title contains 'theme'\n"
            "• category = 'Appearance'\n"
            "• type = 'switch' AND is_favorite = true"
        )
        examples.setStyleSheet("color: #888; font-family: monospace;")
        layout.addWidget(examples)

        # Filter expression input
        from qfluentwidgets import LineEdit

        self.expression_input = LineEdit()
        self.expression_input.setPlaceholderText("Enter filter expression...")
        self.expression_input.textChanged.connect(self.on_expression_changed)
        layout.addWidget(self.expression_input)

    def on_expression_changed(self, expression: str) -> None:
        """Handle custom expression change"""
        if not expression.strip():
            return

        try:
            filter_function = self._parse_expression(expression)

            advanced_filter = AdvancedFilter(
                filter_type=AdvancedFilterType.CUSTOM_FUNCTION,
                name="Custom Filter",
                description=f"Expression: {expression}",
                filter_function=filter_function,
            )

            self.filter_changed.emit(advanced_filter)

        except Exception as e:
            self.logger.warning(f"Invalid filter expression: {e}")

    def _parse_expression(self, expression: str) -> Callable[[SettingItem], bool]:
        """Parse a simple filter expression into a function"""
        # Simple expression parser for basic conditions
        # This is a simplified version - could be expanded with a proper parser

        expression = expression.lower().strip()

        def filter_function(item: SettingItem) -> bool:
            try:
                # Replace item properties in expression
                context = {
                    "title": item.title.lower(),
                    "description": item.description.lower(),
                    "category": item.category.lower(),
                    "type": item.setting_type.lower(),
                    "is_favorite": item.is_favorite,
                    "is_advanced": item.is_advanced,
                }

                # Simple keyword matching
                if "contains" in expression:
                    parts = expression.split("contains")
                    if len(parts) == 2:
                        field = parts[0].strip()
                        search_value = parts[1].strip().strip("'\"")
                        field_value = context.get(field, "")
                        return search_value in str(field_value)

                elif "=" in expression:
                    parts = expression.split("=")
                    if len(parts) == 2:
                        field = parts[0].strip()
                        value_str = parts[1].strip().strip("'\"")
                        compare_value: Union[str, bool] = value_str
                        if value_str in ["true", "false"]:
                            compare_value = value_str == "true"
                        return context.get(field) == compare_value

                # Default: search in all text fields
                return (
                    expression in item.title.lower()
                    or expression in item.description.lower()
                    or expression in item.category.lower()
                )

            except Exception:
                return False

        return filter_function


class AdvancedFilterManager(QWidget):
    """Manager for all advanced filters"""

    filters_changed = Signal(list)  # List[AdvancedFilter]

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(
            "advanced_filter_manager", module="AdvancedFilterManager"
        )
        self.active_filters: List[AdvancedFilter] = []
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the advanced filter manager UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Filter components
        self.value_range_filter = ValueRangeFilter()
        self.value_range_filter.filter_changed.connect(self.on_filter_changed)
        layout.addWidget(self.value_range_filter)

        self.date_range_filter = DateRangeFilter()
        self.date_range_filter.filter_changed.connect(self.on_filter_changed)
        layout.addWidget(self.date_range_filter)

        self.complexity_filter = ComplexityFilter()
        self.complexity_filter.filter_changed.connect(self.on_filter_changed)
        layout.addWidget(self.complexity_filter)

        self.usage_frequency_filter = UsageFrequencyFilter()
        self.usage_frequency_filter.filter_changed.connect(self.on_filter_changed)
        layout.addWidget(self.usage_frequency_filter)

        self.custom_filter_builder = CustomFilterBuilder()
        self.custom_filter_builder.filter_changed.connect(self.on_filter_changed)
        layout.addWidget(self.custom_filter_builder)

    def on_filter_changed(self, advanced_filter: AdvancedFilter) -> None:
        """Handle filter changes"""
        # Update or add the filter
        existing_index = -1
        for i, f in enumerate(self.active_filters):
            if f.filter_type == advanced_filter.filter_type:
                existing_index = i
                break

        if existing_index >= 0:
            self.active_filters[existing_index] = advanced_filter
        else:
            self.active_filters.append(advanced_filter)

        # Emit updated filters
        self.filters_changed.emit(self.active_filters)
        self.logger.debug(f"Updated advanced filter: {advanced_filter.name}")

    def clear_filters(self) -> None:
        """Clear all active filters"""
        self.active_filters.clear()
        self.filters_changed.emit(self.active_filters)

    def get_combined_filter_function(self) -> Callable[[SettingItem], bool]:
        """Get a combined filter function from all active filters"""
        if not self.active_filters:
            return lambda item: True

        def combined_filter(item: SettingItem) -> bool:
            # All filters must pass (AND logic)
            return all(
                f.filter_function(item) for f in self.active_filters if f.enabled
            )

        return combined_filter
