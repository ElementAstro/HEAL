#!/usr/bin/env python3
"""
Simple test runner that can handle missing dependencies with proper mocking
"""

import sys
import os
import traceback
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_comprehensive_mocks():
    """Setup comprehensive mocking for all external dependencies"""
    
    # Mock PySide6 completely
    mock_pyside6 = Mock()
    mock_pyside6.QtCore = Mock()
    mock_pyside6.QtWidgets = Mock()
    mock_pyside6.QtNetwork = Mock()
    mock_pyside6.QtGui = Mock()
    
    # Create proper mock classes
    class MockQWidget:
        def __init__(self, *args, **kwargs): pass
        def setObjectName(self, name): pass
        def show(self): pass
        def hide(self): pass
        def close(self): pass

    class MockQObject:
        def __init__(self, *args, **kwargs): pass
        def setObjectName(self, name): pass

    mock_pyside6.QtWidgets.QWidget = MockQWidget
    mock_pyside6.QtCore.QObject = MockQObject
    mock_pyside6.QtWidgets.QApplication = Mock()
    
    sys.modules['PySide6'] = mock_pyside6
    sys.modules['PySide6.QtCore'] = mock_pyside6.QtCore
    sys.modules['PySide6.QtWidgets'] = mock_pyside6.QtWidgets
    sys.modules['PySide6.QtNetwork'] = mock_pyside6.QtNetwork
    sys.modules['PySide6.QtGui'] = mock_pyside6.QtGui
    
    # Mock qfluentwidgets with proper class-like mocks
    class MockMaskDialogBase:
        def __init__(self, *args, **kwargs): pass
        def show(self): pass
        def hide(self): pass
        def close(self): pass

    class MockStyleSheetBase:
        """Mock base class for StyleSheet that works with Enum"""
        pass

    class MockFluentIconBase:
        """Mock base class for FluentIconBase that works with Enum"""
        pass

    mock_qfluentwidgets = Mock()
    mock_qfluentwidgets.components = Mock()
    mock_qfluentwidgets.components.dialog_box = Mock()
    mock_qfluentwidgets.components.dialog_box.mask_dialog_base = Mock()
    mock_qfluentwidgets.components.dialog_box.mask_dialog_base.MaskDialogBase = MockMaskDialogBase
    mock_qfluentwidgets.common = Mock()
    mock_qfluentwidgets.common.style_sheet = Mock()
    mock_qfluentwidgets.common.style_sheet.StyleSheetBase = MockStyleSheetBase
    mock_qfluentwidgets.window = Mock()

    # Add StyleSheetBase and FluentIconBase directly to the main qfluentwidgets module
    mock_qfluentwidgets.StyleSheetBase = MockStyleSheetBase
    mock_qfluentwidgets.FluentIconBase = MockFluentIconBase
    mock_qfluentwidgets.Theme = Mock()
    mock_qfluentwidgets.qconfig = Mock()
    mock_qfluentwidgets.getIconColor = Mock()

    sys.modules['qfluentwidgets'] = mock_qfluentwidgets
    sys.modules['qfluentwidgets.components'] = mock_qfluentwidgets.components
    sys.modules['qfluentwidgets.components.dialog_box'] = mock_qfluentwidgets.components.dialog_box
    sys.modules['qfluentwidgets.components.dialog_box.mask_dialog_base'] = mock_qfluentwidgets.components.dialog_box.mask_dialog_base
    sys.modules['qfluentwidgets.common'] = mock_qfluentwidgets.common
    sys.modules['qfluentwidgets.common.style_sheet'] = mock_qfluentwidgets.common.style_sheet
    sys.modules['qfluentwidgets.window'] = mock_qfluentwidgets.window
    
    # Mock other dependencies
    mock_loguru = Mock()
    mock_loguru.logger = Mock()
    mock_loguru.logger.info = Mock()
    mock_loguru.logger.error = Mock()
    mock_loguru.logger.debug = Mock()
    mock_loguru.logger.warning = Mock()
    
    sys.modules['loguru'] = mock_loguru
    sys.modules['aiofiles'] = Mock()
    sys.modules['aiohttp'] = Mock()
    sys.modules['asyncio'] = Mock()
    sys.modules['jsonschema'] = Mock()
    sys.modules['requests'] = Mock()
    sys.modules['psutil'] = Mock()
    sys.modules['watchdog'] = Mock()
    sys.modules['watchdog.observers'] = Mock()
    sys.modules['watchdog.events'] = Mock()
    sys.modules['yaml'] = Mock()
    sys.modules['toml'] = Mock()
    sys.modules['markdown'] = Mock()

def test_config_manager_import():
    """Test if we can import the config manager directly"""
    try:
        # Import directly without going through the main heal package
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "src" / "heal" / "common"))

        # Import the specific modules we need
        import config_manager
        from config_manager import ConfigManager, ConfigType, ConfigPath
        print("✅ ConfigManager import successful")
        return True
    except Exception as e:
        print(f"❌ ConfigManager import failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_config_manager_basic_functionality():
    """Test basic config manager functionality"""
    try:
        # Import directly to avoid complex import chain
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        # Mock the dependencies that config_manager needs
        with patch.dict('sys.modules', {
            'heal.resources': Mock(),
            'heal.resources.resource_manager': Mock(),
        }):
            from heal.common.config_manager import ConfigManager, ConfigType, ConfigPath

            # Test initialization
            with patch('pathlib.Path.mkdir'):
                config_manager = ConfigManager()
                print("✅ ConfigManager initialization successful")

            # Test basic methods exist
            assert hasattr(config_manager, 'load_config')
            assert hasattr(config_manager, 'save_config')
            assert hasattr(config_manager, 'get_cached_config')
            print("✅ ConfigManager has required methods")

            # Test method functionality
            with patch.object(config_manager, 'get_config', return_value={"test": "data"}):
                result = config_manager.load_config(ConfigType.MAIN)
                assert result == {"test": "data"}
                print("✅ ConfigManager load_config works")

            with patch.object(config_manager, 'set_config'):
                result = config_manager.save_config(ConfigType.MAIN, {"test": "data"})
                assert result is True
                print("✅ ConfigManager save_config works")

        return True
    except Exception as e:
        print(f"❌ ConfigManager basic functionality test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_logging_config_import():
    """Test if we can import the logging config"""
    try:
        from heal.common.logging_config import get_logger
        print("✅ logging_config import successful")
        return True
    except Exception as e:
        print(f"❌ logging_config import failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def run_simple_tests():
    """Run simple tests to verify basic functionality"""
    print("🚀 Running Simple Test Suite")
    print("=" * 60)
    
    # Setup mocks
    setup_comprehensive_mocks()
    
    tests = [
        ("Config Manager Import", test_config_manager_import),
        ("Config Manager Basic Functionality", test_config_manager_basic_functionality),
        ("Logging Config Import", test_logging_config_import),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    return failed == 0

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)
