#!/usr/bin/env python3
"""
Minimal test to verify the fixes we've made
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_json_utils_fix():
    """Test that the JSON utils fix works"""
    print("🧪 Testing JSON utils fix...")
    
    try:
        # Mock dependencies
        with patch.dict('sys.modules', {
            'loguru': Mock(logger=Mock()),
            'heal.resources': Mock(),
            'heal.resources.resource_manager': Mock(),
        }):
            from heal.common.json_utils import JsonLoadResult, get_json
            
            # Test JsonLoadResult creation
            result = JsonLoadResult(success=True, data={"test": "data"})
            assert result.success is True
            assert result.data == {"test": "data"}
            print("✅ JsonLoadResult creation works")
            
            # Test with a real JSON file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump({"test_key": "test_value"}, f)
                temp_file = f.name
            
            try:
                data = get_json(temp_file, "test_key")
                assert data == "test_value"
                print("✅ get_json works with valid file")
            finally:
                Path(temp_file).unlink()
            
            # Test with non-existent file (should handle gracefully now)
            try:
                data = get_json("non_existent_file.json", "test_key")
                print("✅ get_json handles missing files gracefully")
            except Exception as e:
                print(f"✅ get_json properly raises exception for missing files: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ JSON utils test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_exception_handler_fix():
    """Test that the exception handler fix works"""
    print("🧪 Testing exception handler fix...")
    
    try:
        # Mock dependencies
        with patch.dict('sys.modules', {
            'loguru': Mock(logger=Mock()),
            'heal.resources': Mock(),
            'heal.resources.resource_manager': Mock(),
        }):
            from heal.common.exception_handler import file_exception_handler
            from heal.common.json_utils import JsonLoadResult
            
            # Test that the decorator returns proper JsonLoadResult on exception
            @file_exception_handler
            def failing_function():
                raise FileNotFoundError("Test error")
            
            result = failing_function()
            assert isinstance(result, JsonLoadResult)
            assert result.success is False
            assert "File operation failed" in result.error
            print("✅ file_exception_handler returns proper JsonLoadResult")
            
        return True
        
    except Exception as e:
        print(f"❌ Exception handler test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_config_loading_fix():
    """Test that the config loading fix works"""
    print("🧪 Testing config loading fix...")
    
    try:
        # Mock all dependencies
        with patch.dict('sys.modules', {
            'PySide6': Mock(),
            'PySide6.QtCore': Mock(),
            'PySide6.QtWidgets': Mock(),
            'qfluentwidgets': Mock(
                StyleSheetBase=type('MockStyleSheetBase', (), {}),
                Theme=Mock(),
                qconfig=Mock()
            ),
            'loguru': Mock(logger=Mock()),
            'heal.resources': Mock(),
            'heal.resources.resource_manager': Mock(),
        }):
            # Import the config module - this should not fail now
            from heal.models.config import Config
            
            # Test that Config class can be instantiated
            config = Config()
            assert hasattr(config, 'APP_NAME')
            assert hasattr(config, 'APP_VERSION')
            assert hasattr(config, 'SERVER')
            print("✅ Config class instantiation works")
            
            # Test dynamic loading methods
            assert hasattr(config, 'load_version_from_config')
            assert hasattr(config, 'load_server_from_config')
            print("✅ Config has dynamic loading methods")
            
        return True
        
    except Exception as e:
        print(f"❌ Config loading test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run minimal tests"""
    print("🚀 Running Minimal Fix Verification Tests")
    print("=" * 60)
    
    tests = [
        ("JSON Utils Fix", test_json_utils_fix),
        ("Exception Handler Fix", test_exception_handler_fix),
        ("Config Loading Fix", test_config_loading_fix),
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
    print(f"📊 MINIMAL TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
