"""
Pytest configuration and shared fixtures for HEAL test suite

Provides common fixtures, test configuration, and utilities for all test modules
across the reorganized test directory structure including:
- Common utilities tests
- Component tests
- Interface tests
- Model tests
- Integration tests
"""

# Try to import pytest, but make it optional for testing
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create a minimal pytest replacement for basic functionality
    class MockPytest:
        @staticmethod
        def fixture(scope="function"):
            def decorator(func):
                return func
            return decorator

        @staticmethod
        def raises(exception_type):
            class RaisesContext:
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    if exc_type is None:
                        raise AssertionError(f"Expected {exception_type.__name__} but no exception was raised")
                    return issubclass(exc_type, exception_type)
            return RaisesContext()

    pytest = MockPytest()

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Any, Dict, Generator

# Add the src directory to the Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Mock external dependencies before any imports
mock_loguru = Mock()
mock_loguru.logger = Mock()
mock_loguru.logger.info = Mock()
mock_loguru.logger.error = Mock()
mock_loguru.logger.debug = Mock()
mock_loguru.logger.warning = Mock()

# Create proper mock classes for PySide6
class MockQWidget:
    def __init__(self, *args, **kwargs):
        pass
    def setObjectName(self, name): pass
    def show(self): pass
    def hide(self): pass
    def close(self): pass

class MockQObject:
    def __init__(self, *args, **kwargs):
        pass
    def setObjectName(self, name): pass

class MockProcess:
    def memory_info(self):
        mock_info = Mock()
        mock_info.rss = 1024 * 1024 * 50  # 50MB in bytes
        return mock_info

# Mock all external dependencies
sys.modules['loguru'] = mock_loguru
sys.modules['aiofiles'] = Mock()
sys.modules['aiohttp'] = Mock()
sys.modules['asyncio'] = Mock()
sys.modules['jsonschema'] = Mock()

# Create comprehensive PySide6 mocks
mock_pyside6 = Mock()
mock_pyside6.QtCore = Mock()
mock_pyside6.QtWidgets = Mock()
mock_pyside6.QtNetwork = Mock()
mock_pyside6.QtGui = Mock()

# Set up proper mock classes
mock_pyside6.QtWidgets.QWidget = MockQWidget
mock_pyside6.QtCore.QObject = MockQObject
mock_pyside6.QtWidgets.QApplication = Mock()

sys.modules['PySide6'] = mock_pyside6
sys.modules['PySide6.QtCore'] = mock_pyside6.QtCore
sys.modules['PySide6.QtWidgets'] = mock_pyside6.QtWidgets
sys.modules['PySide6.QtNetwork'] = mock_pyside6.QtNetwork
sys.modules['PySide6.QtGui'] = mock_pyside6.QtGui

sys.modules['qfluentwidgets'] = Mock()
sys.modules['qfluentwidgets.components'] = Mock()
sys.modules['qfluentwidgets.common'] = Mock()
sys.modules['qfluentwidgets.window'] = Mock()
sys.modules['requests'] = Mock()

# Mock psutil with proper process mock
mock_psutil = Mock()
mock_psutil.Process.return_value = MockProcess()
sys.modules['psutil'] = mock_psutil

sys.modules['watchdog'] = Mock()
sys.modules['watchdog.observers'] = Mock()
sys.modules['watchdog.events'] = Mock()
sys.modules['yaml'] = Mock()
sys.modules['toml'] = Mock()
sys.modules['configparser'] = Mock()

# PySide6 and other dependencies are mocked at module level above
PYSIDE6_AVAILABLE = False

# Import onboarding components for testing
# Note: These imports are commented out due to PySide6 dependency issues
# They will be imported within individual test files with proper mocking
# from src.heal.components.onboarding.user_state_tracker import UserLevel, OnboardingStep

# Define mock enums for testing without importing actual modules
class UserLevel:
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class OnboardingStep:
    WELCOME = "welcome"
    BASIC_SETUP = "basic_setup"
    FEATURE_TOUR = "feature_tour"
    FIRST_SERVER = "first_server"
    CUSTOMIZATION = "customization"
    ADVANCED_FEATURES = "advanced_features"
    COMPLETION = "completion"


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the entire test session"""
    # Since we're mocking PySide6 at module level, create a mock app
    mock_app = Mock()
    mock_app.instance = Mock(return_value=mock_app)
    yield mock_app


@pytest.fixture
def main_window(qapp):
    """Create a main window widget for testing"""
    window = Mock()
    window.setObjectName = Mock()
    window.close = Mock()
    yield window


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager with default onboarding data"""
    with patch('src.heal.common.config_manager.ConfigManager') as mock_cm:
        mock_instance = Mock()
        mock_instance.get_config.return_value = {
            "onboarding": {
                "is_first_time": True,
                "completed_steps": [],
                "last_login": None,
                "app_launches": 1,
                "onboarding_version": "1.0.0",
                "user_level": "beginner",
                "preferred_features": [],
                "skipped_tutorials": [],
                "help_preferences": {
                    "show_tips": True,
                    "show_tooltips": True,
                    "show_contextual_help": True,
                    "tutorial_speed": "normal"
                },
                "behavior_patterns": {
                    "session_duration": [],
                    "feature_usage": {},
                    "error_frequency": {},
                    "workflow_patterns": []
                }
            }
        }
        mock_instance.save_config.return_value = None
        mock_cm.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_config_manager_returning_user():
    """Create a mock configuration manager for a returning user"""
    with patch('src.heal.common.config_manager.ConfigManager') as mock_cm:
        mock_instance = Mock()
        mock_instance.get_config.return_value = {
            "onboarding": {
                "is_first_time": False,
                "completed_steps": ["welcome", "basic_setup", "feature_tour"],
                "last_login": "2024-01-15T10:30:00",
                "app_launches": 25,
                "onboarding_version": "1.0.0",
                "user_level": "intermediate",
                "preferred_features": ["server_management", "log_viewer", "batch_operations"],
                "skipped_tutorials": ["advanced_features"],
                "help_preferences": {
                    "show_tips": True,
                    "show_tooltips": False,
                    "show_contextual_help": True,
                    "tutorial_speed": "fast"
                },
                "behavior_patterns": {
                    "session_duration": [1800, 2400, 1200],
                    "feature_usage": {
                        "server_management": 45,
                        "log_viewer": 23,
                        "batch_operations": 12
                    },
                    "error_frequency": {
                        "connection_error": 3,
                        "configuration_error": 1
                    },
                    "workflow_patterns": [
                        "login -> home -> server_management",
                        "login -> home -> log_viewer -> troubleshooting"
                    ]
                }
            }
        }
        mock_instance.save_config.return_value = None
        mock_cm.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_config_manager_advanced_user():
    """Create a mock configuration manager for an advanced user"""
    with patch('src.heal.common.config_manager.ConfigManager') as mock_cm:
        mock_instance = Mock()
        mock_instance.get_config.return_value = {
            "onboarding": {
                "is_first_time": False,
                "completed_steps": [
                    "welcome", "basic_setup", "feature_tour", 
                    "first_server", "customization", "advanced_features", "completion"
                ],
                "last_login": "2024-01-20T14:45:00",
                "app_launches": 150,
                "onboarding_version": "1.0.0",
                "user_level": "advanced",
                "preferred_features": [
                    "server_management", "module_development", "api_integration",
                    "performance_tuning", "automation", "custom_commands"
                ],
                "skipped_tutorials": [],
                "help_preferences": {
                    "show_tips": False,
                    "show_tooltips": False,
                    "show_contextual_help": False,
                    "tutorial_speed": "fast"
                },
                "behavior_patterns": {
                    "session_duration": [3600, 4200, 2800, 5400],
                    "feature_usage": {
                        "server_management": 200,
                        "module_development": 85,
                        "api_integration": 45,
                        "performance_tuning": 32,
                        "automation": 67
                    },
                    "error_frequency": {
                        "connection_error": 2,
                        "module_error": 5,
                        "performance_issue": 3
                    },
                    "workflow_patterns": [
                        "login -> tools -> module_development",
                        "login -> home -> batch_operations -> performance_monitoring",
                        "login -> environment -> api_configuration -> testing"
                    ]
                }
            }
        }
        mock_instance.save_config.return_value = None
        mock_cm.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_user_actions():
    """Provide sample user actions for testing"""
    return [
        ("app_started", {"timestamp": "2024-01-20T10:00:00"}),
        ("home_page_viewed", {"page": "home"}),
        ("server_card_clicked", {"server_id": "test_server_1"}),
        ("server_started", {"server_id": "test_server_1"}),
        ("logs_viewed", {"server_id": "test_server_1", "duration": 120}),
        ("module_downloaded", {"module": "astronomy_tools", "size": "15MB"}),
        ("settings_accessed", {"section": "performance"}),
        ("help_requested", {"type": "tooltip", "context": "server_management"}),
        ("tutorial_started", {"tutorial_id": "feature_tour"}),
        ("tutorial_completed", {"tutorial_id": "feature_tour", "duration": 300}),
        ("error_encountered", {"type": "connection_error", "server": "remote_server"}),
        ("problem_resolved", {"solution": "proxy_configuration"}),
        ("feature_discovered", {"feature": "batch_operations"}),
        ("recommendation_accepted", {"rec_id": "setup_first_server"}),
        ("app_closed", {"session_duration": 1800})
    ]


@pytest.fixture
def sample_system_states():
    """Provide sample system states for testing"""
    return [
        {"cpu_usage": 45, "memory_usage": 60, "servers_active": 2},
        {"cpu_usage": 85, "memory_usage": 75, "servers_active": 5},
        {"cpu_usage": 25, "memory_usage": 40, "servers_active": 1},
        {"cpu_usage": 95, "memory_usage": 90, "servers_active": 8},
        {"cpu_usage": 55, "memory_usage": 65, "servers_active": 3}
    ]


@pytest.fixture
def sample_error_scenarios():
    """Provide sample error scenarios for testing"""
    return [
        ("connection_error", {"server": "remote_server", "port": 8080, "timeout": 30}),
        ("configuration_error", {"setting": "proxy_url", "value": "invalid_url"}),
        ("performance_issue", {"cpu": 95, "memory": 90, "response_time": 5000}),
        ("module_error", {"module": "custom_module", "error": "import_failed"}),
        ("authentication_error", {"user": "test_user", "reason": "invalid_credentials"}),
        ("network_error", {"type": "dns_resolution", "domain": "example.com"}),
        ("storage_error", {"type": "disk_full", "available": "100MB"}),
        ("api_error", {"endpoint": "/api/servers", "status_code": 500})
    ]


@pytest.fixture
def performance_test_data():
    """Provide data for performance testing"""
    return {
        "large_action_set": [
            (f"performance_action_{i}", {"index": i, "data": "x" * 100})
            for i in range(1000)
        ],
        "search_queries": [
            "server setup", "configuration", "troubleshooting", "module development",
            "performance optimization", "connection issues", "getting started",
            "advanced features", "api integration", "automation"
        ],
        "system_states": [
            {"cpu_usage": i % 100, "memory_usage": (i * 2) % 100, "active_servers": i % 10}
            for i in range(100)
        ]
    }


@pytest.fixture
def mock_qt_widgets():
    """Mock Qt widgets to avoid UI dependencies in tests"""
    with patch('src.heal.components.onboarding.contextual_help.TeachingTip') as mock_tip:
        with patch('src.heal.components.onboarding.contextual_help.InfoBar') as mock_info:
            with patch('qfluentwidgets.MessageBox') as mock_msg:
                mock_tip.create.return_value = Mock()
                mock_info.info.return_value = Mock()
                mock_msg.return_value = Mock()
                yield {
                    'teaching_tip': mock_tip,
                    'info_bar': mock_info,
                    'message_box': mock_msg
                }


@pytest.fixture
def disable_timers():
    """Disable QTimer functionality for testing"""
    with patch.object(QTimer, 'start') as mock_start:
        with patch.object(QTimer, 'stop') as mock_stop:
            with patch.object(QTimer, 'isActive', return_value=False) as mock_active:
                yield {
                    'start': mock_start,
                    'stop': mock_stop,
                    'is_active': mock_active
                }


# Test markers for categorizing tests
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as requiring UI components"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add markers based on test file names
        if "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        if "ui" in item.name.lower() or "widget" in item.name.lower():
            item.add_marker(pytest.mark.ui)
        
        # Mark tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["concurrent", "stress", "load", "benchmark"]):
            item.add_marker(pytest.mark.slow)


# Utility functions for tests
def create_test_user_tracker(user_level: UserLevel = UserLevel.BEGINNER, 
                           is_first_time: bool = True) -> Mock:
    """Create a mock user tracker with specified settings"""
    tracker = Mock()
    tracker.get_user_level.return_value = user_level
    tracker.is_first_time_user.return_value = is_first_time
    tracker.should_show_tips.return_value = True
    tracker.should_show_tooltips.return_value = True
    tracker.should_show_contextual_help.return_value = True
    tracker.get_tutorial_speed.return_value = "normal"
    tracker.get_completed_steps.return_value = []
    tracker.get_help_preferences.return_value = {
        "show_tips": True,
        "show_tooltips": True,
        "show_contextual_help": True,
        "tutorial_speed": "normal"
    }
    return tracker


def assert_performance_threshold(actual_time: float, expected_max: float, operation: str):
    """Assert that an operation completed within expected time"""
    assert actual_time <= expected_max, (
        f"{operation} took {actual_time:.3f}s, expected <= {expected_max:.3f}s"
    )


def assert_memory_usage_reasonable(initial_objects: int, final_objects: int, 
                                 max_increase: int, operation: str):
    """Assert that memory usage increase is reasonable"""
    increase = final_objects - initial_objects
    assert increase <= max_increase, (
        f"{operation} increased object count by {increase}, expected <= {max_increase}"
    )


# Cleanup functions
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Force garbage collection after each test
    import gc
    gc.collect()


# Skip conditions for certain environments
def pytest_runtest_setup(item):
    """Setup function run before each test"""
    # Skip UI tests if no display is available
    if item.get_closest_marker("ui"):
        if os.environ.get("DISPLAY") is None and os.name != "nt":
            pytest.skip("UI tests require a display")
    
    # Skip performance tests in CI unless explicitly requested
    if item.get_closest_marker("performance"):
        if os.environ.get("CI") and not os.environ.get("RUN_PERFORMANCE_TESTS"):
            pytest.skip("Performance tests skipped in CI (set RUN_PERFORMANCE_TESTS=1 to enable)")


# Test reporting hooks
def pytest_runtest_logreport(report):
    """Log test results"""
    if report.when == "call":
        if report.outcome == "failed":
            print(f"\n❌ FAILED: {report.nodeid}")
        elif report.outcome == "passed":
            print(f"✅ PASSED: {report.nodeid}")


# Session-level fixtures for expensive setup
@pytest.fixture(scope="session")
def test_data_directory():
    """Create a temporary directory for test data"""
    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp(prefix="heal_tests_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


# Additional fixtures for the reorganized test structure

@pytest.fixture
def mock_download_manager():
    """Create a mock download manager for testing"""
    with patch('src.heal.models.download_manager.DownloadManager') as mock_dm:
        mock_instance = Mock()
        mock_instance.add_download.return_value = "download_id_123"
        mock_instance.get_download_status.return_value = "downloading"
        mock_instance.cancel_download.return_value = True
        mock_dm.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_process_manager():
    """Create a mock process manager for testing"""
    with patch('src.heal.models.process_manager.ProcessManager') as mock_pm:
        mock_instance = Mock()
        mock_instance.start_process.return_value = "process_id_123"
        mock_instance.get_process_status.return_value = "running"
        mock_instance.stop_process.return_value = True
        mock_pm.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager for testing"""
    with patch('src.heal.common.cache_manager.global_cache_manager') as mock_cm:
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.put.return_value = None
        mock_cm.get_cache.return_value = mock_cache
        yield mock_cm


@pytest.fixture
def mock_memory_optimizer():
    """Create a mock memory optimizer for testing"""
    with patch('src.heal.common.memory_optimizer.global_memory_optimizer') as mock_mo:
        mock_mo.optimize.return_value = {"freed_objects": 100, "memory_freed": "10MB"}
        mock_mo.monitor.get_memory_stats.return_value = {"used": "50MB", "available": "200MB"}
        yield mock_mo
