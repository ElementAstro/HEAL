from typing import Any
"""
Settings Search Functionality Tests
Comprehensive testing of search engine, UI components, and integration
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock

# Mock PySide6 components for testing
class MockQObject:
    def __init__(self, parent=None) -> None:
        self.parent = parent

class MockSignal:
    def __init__(self) -> None:
        self.callbacks: list[Any] = []
    
    def connect(self, callback) -> None:
        self.callbacks.append(callback)
    
    def emit(self, *args, **kwargs) -> None:
        for callback in self.callbacks:
            callback(*args, **kwargs)

class MockQTimer:
    def __init__(self) -> None:
        self.timeout = MockSignal()
        self.active = False
    
    def start(self, interval) -> None:
        self.active = True
    
    def stop(self) -> None:
        self.active = False
    
    def setSingleShot(self, single) -> None:
        pass

# Mock the PySide6 imports
import sys
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtGui'] = Mock()
sys.modules['qfluentwidgets'] = Mock()

# Mock the Qt classes
sys.modules['PySide6.QtCore'].QObject = MockQObject
sys.modules['PySide6.QtCore'].Signal = MockSignal
sys.modules['PySide6.QtCore'].QTimer = MockQTimer

# Now import our search components
from src.heal.components.setting.search_engine import (
    SettingsSearchEngine, SettingItem, SearchResult, SearchType, FilterType, SearchFilter
)
from src.heal.components.setting.search_integration import SettingsSearchIntegrator


class TestSettingItem(unittest.TestCase):
    """Test SettingItem functionality"""
    
    def test_setting_item_creation(self) -> None:
        """Test creating a setting item"""
        item = SettingItem(
            key="test_setting",
            title="Test Setting",
            description="A test setting for unit tests",
            category="Test",
            setting_type="switch",
            value=True
        )
        
        self.assertEqual(item.key, "test_setting")
        self.assertEqual(item.title, "Test Setting")
        self.assertEqual(item.category, "Test")
        self.assertTrue(item.value)
        self.assertIsInstance(item.keywords, list)
        self.assertGreater(len(item.keywords), 0)
    
    def test_keyword_generation(self) -> None:
        """Test automatic keyword generation"""
        item = SettingItem(
            key="theme_color",
            title="Theme Color Selection",
            description="Choose your preferred theme color",
            category="Appearance",
            setting_type="color",
            value="#0078d4"
        )
        
        keywords = item.keywords
        self.assertIn("theme", keywords)
        self.assertIn("color", keywords)
        self.assertIn("selection", keywords)
        self.assertIn("appearance", keywords)
        self.assertIn("choose", keywords)


class TestSearchEngine(unittest.TestCase):
    """Test the search engine functionality"""
    
    def setUp(self) -> None:
        self.search_engine = SettingsSearchEngine()
        
        # Add test settings
        self.test_items = [
            SettingItem(
                key="theme_color",
                title="Theme Color",
                description="Choose your application theme color",
                category="Appearance",
                setting_type="color",
                value="#0078d4"
            ),
            SettingItem(
                key="auto_copy",
                title="Auto Copy",
                description="Automatically copy commands to clipboard",
                category="Behavior",
                setting_type="switch",
                value=True
            ),
            SettingItem(
                key="proxy_port",
                title="Proxy Port",
                description="Configure proxy server port",
                category="Network",
                setting_type="text",
                value="7890"
            ),
            SettingItem(
                key="language",
                title="Language",
                description="Select interface language",
                category="Appearance",
                setting_type="combo",
                value="English"
            )
        ]
        
        for item in self.test_items:
            self.search_engine.add_setting(item)
    
    def test_add_remove_settings(self) -> None:
        """Test adding and removing settings"""
        initial_count = len(self.search_engine.items)
        
        # Add a new setting
        new_item = SettingItem(
            key="new_setting",
            title="New Setting",
            description="A new test setting",
            category="Test",
            setting_type="switch",
            value=False
        )
        
        self.search_engine.add_setting(new_item)
        self.assertEqual(len(self.search_engine.items), initial_count + 1)
        
        # Remove the setting
        self.search_engine.remove_setting("new_setting")
        self.assertEqual(len(self.search_engine.items), initial_count)
    
    def test_exact_search(self) -> None:
        """Test exact string matching"""
        results = self.search_engine.search("Theme Color", search_type=SearchType.EXACT)
        
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].item.key, "theme_color")
        self.assertEqual(results[0].match_type, SearchType.EXACT)
    
    def test_fuzzy_search(self) -> None:
        """Test fuzzy string matching"""
        results = self.search_engine.search("them colr", search_type=SearchType.FUZZY)
        
        # Should find "Theme Color" despite typos
        self.assertGreater(len(results), 0)
        theme_result = next((r for r in results if r.item.key == "theme_color"), None)
        self.assertIsNotNone(theme_result)
    
    def test_keyword_search(self) -> None:
        """Test keyword-based search"""
        results = self.search_engine.search("clipboard", search_type=SearchType.KEYWORD)
        
        # Should find "Auto Copy" setting
        self.assertGreater(len(results), 0)
        auto_copy_result = next((r for r in results if r.item.key == "auto_copy"), None)
        self.assertIsNotNone(auto_copy_result)
    
    def test_category_filter(self) -> None:
        """Test category filtering"""
        category_filter = SearchFilter(
            filter_type=FilterType.CATEGORY,
            value="Appearance"
        )
        
        results = self.search_engine.search("", filters=[category_filter])
        
        # Should only return Appearance settings
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertEqual(result.item.category, "Appearance")
    
    def test_type_filter(self) -> None:
        """Test type filtering"""
        type_filter = SearchFilter(
            filter_type=FilterType.TYPE,
            value="switch"
        )
        
        results = self.search_engine.search("", filters=[type_filter])
        
        # Should only return switch settings
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertEqual(result.item.setting_type, "switch")
    
    def test_combined_search_and_filter(self) -> None:
        """Test combining search query with filters"""
        category_filter = SearchFilter(
            filter_type=FilterType.CATEGORY,
            value="Appearance"
        )
        
        results = self.search_engine.search("color", filters=[category_filter])
        
        # Should find theme color setting
        self.assertGreater(len(results), 0)
        theme_result = next((r for r in results if r.item.key == "theme_color"), None)
        self.assertIsNotNone(theme_result)
        
        # All results should be from Appearance category
        for result in results:
            self.assertEqual(result.item.category, "Appearance")
    
    def test_search_suggestions(self) -> None:
        """Test search suggestions"""
        suggestions = self.search_engine.get_suggestions("the", limit=5)
        
        self.assertIsInstance(suggestions, list)
        self.assertLessEqual(len(suggestions), 5)
        
        # Should include "theme" as a suggestion
        self.assertIn("theme", [s.lower() for s in suggestions])
    
    def test_filter_options(self) -> None:
        """Test getting filter options"""
        options = self.search_engine.get_filter_options()
        
        self.assertIn('categories', options)
        self.assertIn('types', options)
        
        categories = options['categories']
        self.assertIn('Appearance', categories)
        self.assertIn('Behavior', categories)
        self.assertIn('Network', categories)
    
    def test_search_statistics(self) -> None:
        """Test search statistics"""
        stats = self.search_engine.get_statistics()
        
        self.assertIn('total_items', stats)
        self.assertIn('total_keywords', stats)
        self.assertIn('categories', stats)
        self.assertIn('types', stats)
        
        self.assertEqual(stats['total_items'], len(self.test_items))
        self.assertGreater(stats['total_keywords'], 0)
    
    def test_real_time_search(self) -> None:
        """Test real-time search with debouncing"""
        results_received = []
        
        def on_search_completed(results: Any) -> None:
            results_received.append(results)
        
        self.search_engine.search_completed.connect(on_search_completed)
        
        # Trigger real-time search
        self.search_engine.search_realtime("theme", delay_ms=100)
        
        # Simulate timer execution
        self.search_engine._execute_delayed_search()
        
        self.assertGreater(len(results_received), 0)
        self.assertGreater(len(results_received[0]), 0)


class TestSearchIntegration(unittest.TestCase):
    """Test search integration functionality"""
    
    def setUp(self) -> None:
        self.integrator = SettingsSearchIntegrator()
    
    def test_custom_setting_registration(self) -> None:
        """Test registering custom settings"""
        self.integrator.register_custom_setting(
            key="test_custom",
            title="Custom Test Setting",
            description="A custom setting for testing",
            category="Test",
            setting_type="switch",
            value=True,
            keywords=["custom", "test", "example"]
        )
        
        # Should be in registry
        self.assertIn("test_custom", self.integrator.settings_registry)
        
        # Should be searchable
        results = self.integrator.search_engine.search("custom")
        self.assertGreater(len(results), 0)
        
        custom_result = next((r for r in results if r.item.key == "test_custom"), None)
        self.assertIsNotNone(custom_result)
    
    def test_setting_value_update(self) -> None:
        """Test updating setting values"""
        # Register a setting
        self.integrator.register_custom_setting(
            key="test_update",
            title="Update Test",
            description="Test setting updates",
            category="Test",
            setting_type="text",
            value="original"
        )
        
        # Update the value
        self.integrator.update_setting_value("test_update", "updated")
        
        # Check if updated
        setting = self.integrator.settings_registry["test_update"]
        self.assertEqual(setting.value, "updated")
    
    def test_favorite_marking(self) -> None:
        """Test marking settings as favorites"""
        # Register a setting
        self.integrator.register_custom_setting(
            key="test_favorite",
            title="Favorite Test",
            description="Test favorite functionality",
            category="Test",
            setting_type="switch",
            value=False
        )
        
        # Mark as favorite
        self.integrator.mark_setting_as_favorite("test_favorite", True)
        
        # Check if marked
        setting = self.integrator.settings_registry["test_favorite"]
        self.assertTrue(setting.is_favorite)
    
    def test_search_statistics(self) -> None:
        """Test getting search statistics"""
        # Register some settings
        for i in range(5):
            self.integrator.register_custom_setting(
                key=f"test_stat_{i}",
                title=f"Stat Test {i}",
                description=f"Statistics test setting {i}",
                category="Test",
                setting_type="switch",
                value=i % 2 == 0
            )
        
        stats = self.integrator.get_search_statistics()
        
        self.assertIn('search_engine', stats)
        self.assertIn('registered_settings', stats)
        self.assertIn('widget_mappings', stats)
        self.assertIn('categories', stats)
        
        self.assertEqual(stats['registered_settings'], 5)
    
    def test_export_import_functionality(self) -> None:
        """Test exporting and importing settings"""
        # Register some settings
        self.integrator.register_custom_setting(
            key="export_test",
            title="Export Test",
            description="Test export functionality",
            category="Test",
            setting_type="switch",
            value=True
        )
        
        # Mark as favorite
        self.integrator.mark_setting_as_favorite("export_test", True)
        
        # Export settings index
        exported = self.integrator.export_settings_index()
        
        self.assertIn('settings', exported)
        self.assertIn('statistics', exported)
        self.assertIn('export_test', exported['settings'])
        
        # Test import favorites
        favorites = {"export_test": False}
        self.integrator.import_favorites(favorites)
        
        setting = self.integrator.settings_registry["export_test"]
        self.assertFalse(setting.is_favorite)


class TestSearchPerformance(unittest.TestCase):
    """Test search performance with large datasets"""
    
    def setUp(self) -> None:
        self.search_engine = SettingsSearchEngine()
        
        # Create a large number of test settings
        self.large_dataset: list[Any] = []
        categories = ["Appearance", "Behavior", "Network", "System", "Advanced"]
        types = ["switch", "combo", "text", "button", "color"]
        
        for i in range(1000):
            item = SettingItem(
                key=f"setting_{i}",
                title=f"Test Setting {i}",
                description=f"This is test setting number {i} for performance testing",
                category=categories[i % len(categories)],
                setting_type=types[i % len(types)],
                value=i
            )
            self.large_dataset.append(item)
            self.search_engine.add_setting(item)
    
    def test_large_dataset_search_performance(self) -> None:
        """Test search performance with large dataset"""
        start_time = time.time()
        
        # Perform multiple searches
        queries = ["test", "setting", "performance", "number", "advanced"]
        
        for query in queries:
            results = self.search_engine.search(query)
            self.assertIsInstance(results, list)
        
        end_time = time.time()
        search_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(search_time, 2.0, f"Search took too long: {search_time:.3f}s")
    
    def test_index_building_performance(self) -> None:
        """Test index building performance"""
        new_engine = SettingsSearchEngine()
        
        start_time = time.time()
        
        # Add all items
        for item in self.large_dataset:
            new_engine.add_setting(item)
        
        end_time = time.time()
        index_time = end_time - start_time
        
        # Should build index within reasonable time
        self.assertLess(index_time, 1.0, f"Index building took too long: {index_time:.3f}s")
        
        # Verify index was built correctly
        self.assertEqual(len(new_engine.items), len(self.large_dataset))
    
    def test_memory_usage(self) -> None:
        """Test memory usage with large dataset"""
        import sys
        
        # Get approximate memory usage
        initial_size = sys.getsizeof(self.search_engine.items)
        
        # Add more items
        for i in range(1000, 2000):
            item = SettingItem(
                key=f"memory_test_{i}",
                title=f"Memory Test {i}",
                description=f"Memory usage test setting {i}",
                category="Test",
                setting_type="switch",
                value=True
            )
            self.search_engine.add_setting(item)
        
        final_size = sys.getsizeof(self.search_engine.items)
        
        # Memory usage should be reasonable
        memory_increase = final_size - initial_size
        self.assertLess(memory_increase, 1024 * 1024, "Memory usage too high")  # Less than 1MB


def run_search_benchmarks() -> None:
    """Run search performance benchmarks"""
    print("\n=== Settings Search Benchmarks ===")
    
    # Create search engine with test data
    engine = SettingsSearchEngine()
    
    # Add test settings
    categories = ["Appearance", "Behavior", "Network", "System"]
    types = ["switch", "combo", "text", "button"]
    
    for i in range(100):
        item = SettingItem(
            key=f"benchmark_{i}",
            title=f"Benchmark Setting {i}",
            description=f"Performance benchmark setting number {i}",
            category=categories[i % len(categories)],
            setting_type=types[i % len(types)],
            value=i
        )
        engine.add_setting(item)
    
    # Benchmark different search types
    queries = ["benchmark", "setting", "performance", "test"]
    search_types = [SearchType.EXACT, SearchType.FUZZY, SearchType.KEYWORD]
    
    for search_type in search_types:
        start_time = time.time()
        
        for query in queries:
            results = engine.search(query, search_type=search_type)
        
        end_time = time.time()
        search_time = end_time - start_time
        
        print(f"{search_type.value.title()} search (4 queries): {search_time:.3f}s "
              f"({len(queries)/search_time:.0f} queries/sec)")
    
    # Benchmark filtering
    start_time = time.time()
    
    for category in categories:
        filter_obj = SearchFilter(FilterType.CATEGORY, category)
        results = engine.search("", filters=[filter_obj])
    
    end_time = time.time()
    filter_time = end_time - start_time
    
    print(f"Category filtering (4 filters): {filter_time:.3f}s "
          f"({len(categories)/filter_time:.0f} filters/sec)")
    
    # Benchmark suggestions
    start_time = time.time()
    
    for i in range(10):
        suggestions = engine.get_suggestions(f"bench{i}", limit=5)
    
    end_time = time.time()
    suggestion_time = end_time - start_time
    
    print(f"Suggestions (10 requests): {suggestion_time:.3f}s "
          f"({10/suggestion_time:.0f} requests/sec)")


if __name__ == '__main__':
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance benchmarks
    run_search_benchmarks()
