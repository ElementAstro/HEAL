#!/usr/bin/env python3
"""
Standalone test for ConfigManager that bypasses complex import chains
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Mock all external dependencies before any imports
def setup_mocks():
    """Setup mocks for external dependencies"""

    # Mock PySide6 completely
    class MockQWidget:
        def __init__(self, *args, **kwargs): pass
        def setObjectName(self, name): pass
        def show(self): pass
        def hide(self): pass
        def close(self): pass

    class MockQObject:
        def __init__(self, *args, **kwargs): pass
        def setObjectName(self, name): pass

    mock_pyside6 = Mock()
    mock_pyside6.QtCore = Mock()
    mock_pyside6.QtWidgets = Mock()
    mock_pyside6.QtNetwork = Mock()
    mock_pyside6.QtGui = Mock()

    mock_pyside6.QtWidgets.QWidget = MockQWidget
    mock_pyside6.QtCore.QObject = MockQObject
    mock_pyside6.QtWidgets.QApplication = Mock()

    sys.modules['PySide6'] = mock_pyside6
    sys.modules['PySide6.QtCore'] = mock_pyside6.QtCore
    sys.modules['PySide6.QtWidgets'] = mock_pyside6.QtWidgets
    sys.modules['PySide6.QtNetwork'] = mock_pyside6.QtNetwork
    sys.modules['PySide6.QtGui'] = mock_pyside6.QtGui

    # Mock qfluentwidgets
    class MockStyleSheetBase:
        pass

    class MockFluentIconBase:
        pass

    mock_qfluentwidgets = Mock()
    mock_qfluentwidgets.StyleSheetBase = MockStyleSheetBase
    mock_qfluentwidgets.FluentIconBase = MockFluentIconBase
    mock_qfluentwidgets.Theme = Mock()
    mock_qfluentwidgets.qconfig = Mock()
    mock_qfluentwidgets.getIconColor = Mock()

    sys.modules['qfluentwidgets'] = mock_qfluentwidgets

    # Mock loguru
    mock_loguru = Mock()
    mock_loguru.logger = Mock()
    sys.modules['loguru'] = mock_loguru

    # Mock other dependencies
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

    # Mock resource manager with proper return values
    mock_resource_manager = Mock()
    mock_resource_manager.get_resource_path = Mock(return_value=Path("test/path"))

    # Create a mock resources module
    mock_resources = Mock()
    mock_resources.resource_manager = mock_resource_manager

    sys.modules['heal.resources'] = mock_resources
    sys.modules['heal.resources.resource_manager'] = mock_resource_manager
    
    # Mock config validator
    class MockValidationResult:
        def __init__(self):
            self.is_valid = True
            self.errors = []
            self.warnings = []
    
    class MockConfigValidator:
        def validate_config_file(self, *args, **kwargs):
            return MockValidationResult()
    
    sys.modules['heal.common.config_validator'] = Mock()
    sys.modules['heal.common.config_validator'].ConfigValidator = MockConfigValidator
    sys.modules['heal.common.config_validator'].ValidationLevel = Mock()
    sys.modules['heal.common.config_validator'].ValidationResult = MockValidationResult

def test_config_manager_standalone():
    """Test ConfigManager in isolation"""
    print("🧪 Testing ConfigManager in standalone mode...")

    setup_mocks()

    try:
        # Import directly from the module file to avoid complex import chain
        import importlib.util

        # Load config_manager module directly
        config_manager_path = Path(__file__).parent / "src" / "heal" / "common" / "config_manager.py"
        spec = importlib.util.spec_from_file_location("config_manager", config_manager_path)
        config_manager_module = importlib.util.module_from_spec(spec)

        # Mock the dependencies that config_manager needs
        with patch.dict('sys.modules', {
            'heal.resources.resource_manager': Mock(get_resource_path=Mock(return_value=Path("test/path"))),
            'heal.common.config_validator': Mock(
                ConfigValidator=Mock(),
                ValidationLevel=Mock(),
                ValidationResult=Mock()
            ),
            'heal.common.logging_config': Mock(get_logger=Mock(return_value=Mock())),
        }):
            spec.loader.exec_module(config_manager_module)

            ConfigManager = config_manager_module.ConfigManager
            ConfigType = config_manager_module.ConfigType
            ConfigPath = config_manager_module.ConfigPath
        
        print("✅ ConfigManager import successful")
        
        # Test initialization with temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            config_manager = ConfigManager(config_dir=Path(temp_dir))
            print("✅ ConfigManager initialization successful")
            
            # Test that required methods exist
            assert hasattr(config_manager, 'load_config')
            assert hasattr(config_manager, 'save_config')
            assert hasattr(config_manager, 'get_cached_config')
            print("✅ ConfigManager has required methods")
            
            # Test basic functionality
            test_data = {"test_key": "test_value", "nested": {"key": "value"}}
            
            # Test save_config
            result = config_manager.save_config(ConfigType.MAIN, test_data)
            assert result is True
            print("✅ ConfigManager save_config works")
            
            # Test load_config
            loaded_data = config_manager.load_config(ConfigType.MAIN)
            assert loaded_data is not None
            assert loaded_data.get("test_key") == "test_value"
            print("✅ ConfigManager load_config works")
            
            # Test caching
            cached_data = config_manager.get_cached_config(ConfigType.MAIN)
            assert cached_data is not None
            print("✅ ConfigManager caching works")
            
            # Test config value operations
            value = config_manager.get_config_value(ConfigType.MAIN, "test_key")
            assert value == "test_value"
            print("✅ ConfigManager get_config_value works")
            
            config_manager.set_config_value(ConfigType.MAIN, "new_key", "new_value")
            new_value = config_manager.get_config_value(ConfigType.MAIN, "new_key")
            assert new_value == "new_value"
            print("✅ ConfigManager set_config_value works")
        
        return True
        
    except Exception as e:
        print(f"❌ ConfigManager standalone test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_config_types():
    """Test ConfigType enum"""
    print("🧪 Testing ConfigType enum...")
    
    try:
        from heal.common.config_manager import ConfigType
        
        # Test enum values
        assert ConfigType.MAIN.value == "main"
        assert ConfigType.AUTO.value == "auto"
        assert ConfigType.VERSION.value == "version"
        assert ConfigType.SERVER.value == "server"
        assert ConfigType.USER.value == "user"
        print("✅ ConfigType enum values correct")
        
        return True
        
    except Exception as e:
        print(f"❌ ConfigType test failed: {e}")
        return False

def main():
    """Run standalone tests"""
    print("🚀 Running Standalone ConfigManager Tests")
    print("=" * 60)
    
    tests = [
        ("ConfigManager Standalone", test_config_manager_standalone),
        ("ConfigType Enum", test_config_types),
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
    print(f"📊 STANDALONE TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
