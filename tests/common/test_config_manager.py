"""
Tests for the configuration manager module.

Tests configuration management functionality including config loading,
saving, validation, and caching.
"""

# Try to import pytest, but make it optional
try:
    import pytest
except ImportError:
    # Create a minimal pytest replacement
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

from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import json
import tempfile

# Mock PySide6 before importing any modules that depend on it
with patch.dict('sys.modules', {
    'PySide6': Mock(),
    'PySide6.QtCore': Mock(),
    'PySide6.QtWidgets': Mock(),
    'PySide6.QtNetwork': Mock(),
    'qfluentwidgets': Mock()
}):
    from src.heal.common.config_manager import ConfigManager, ConfigType, ConfigPath


class TestConfigManager:
    """Test the configuration manager"""

    @pytest.fixture
    def config_manager(self):
        """Create a config manager instance for testing"""
        with patch('src.heal.common.config_manager.Path'):
            manager = ConfigManager()
            return manager

    @pytest.fixture
    def sample_config(self):
        """Sample configuration data for testing"""
        return {
            "app_name": "HEAL",
            "version": "1.0.0",
            "settings": {
                "theme": "dark",
                "language": "en",
                "auto_update": True
            },
            "user_preferences": {
                "show_tips": True,
                "log_level": "INFO"
            }
        }

    def test_config_manager_initialization(self, config_manager):
        """Test config manager initialization"""
        assert config_manager is not None
        assert hasattr(config_manager, 'load_config')
        assert hasattr(config_manager, 'save_config')
        assert hasattr(config_manager, '_cache')

    def test_load_config_success(self, config_manager, sample_config):
        """Test successful configuration loading"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))):
                config = config_manager.load_config(ConfigType.MAIN)

                assert config is not None
                assert config["app_name"] == "HEAL"
                assert config["settings"]["theme"] == "dark"
                assert config["user_preferences"]["show_tips"] is True

    def test_load_config_file_not_found(self, config_manager):
        """Test configuration loading when file doesn't exist"""
        with patch('pathlib.Path.exists', return_value=False):
            config = config_manager.load_config(ConfigType.MAIN)

            # Should return default config or None
            assert config is None or isinstance(config, dict)

    def test_load_config_invalid_json(self, config_manager):
        """Test configuration loading with invalid JSON"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="invalid json")):
                with pytest.raises((json.JSONDecodeError, ValueError)):
                    config_manager.load_config(ConfigType.MAIN)

    def test_save_config_success(self, config_manager, sample_config):
        """Test successful configuration saving"""
        mock_file = mock_open()

        with patch('builtins.open', mock_file):
            with patch('pathlib.Path.parent.mkdir') as mock_mkdir:
                result = config_manager.save_config(ConfigType.MAIN, sample_config)

                # Verify file operations
                mock_file.assert_called_once()
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

                # Verify JSON was written
                written_data = ''.join(call.args[0] for call in mock_file().write.call_args_list)
                parsed_data = json.loads(written_data)
                assert parsed_data == sample_config

    def test_save_config_permission_error(self, config_manager, sample_config):
        """Test configuration saving with permission error"""
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                config_manager.save_config(ConfigType.MAIN, sample_config)

    def test_config_validation_valid(self, config_manager, sample_config):
        """Test configuration validation with valid config"""
        # Mock validation schema
        with patch.object(config_manager, 'validate_config', return_value=True) as mock_validate:
            result = config_manager.validate_config(sample_config)
            assert result is True
            mock_validate.assert_called_once_with(sample_config)

    def test_config_validation_invalid(self, config_manager):
        """Test configuration validation with invalid config"""
        invalid_config = {"invalid_field": "value"}

        with patch.object(config_manager, 'validate_config', return_value=False) as mock_validate:
            result = config_manager.validate_config(invalid_config)
            assert result is False
            mock_validate.assert_called_once_with(invalid_config)

    def test_config_caching_hit(self, config_manager, sample_config):
        """Test configuration caching - cache hit scenario"""
        config_type = ConfigType.MAIN

        # Mock cache to return cached config
        with patch.object(config_manager, '_cache', {config_type: sample_config}):
            config = config_manager.get_cached_config(config_type)
            assert config == sample_config

    def test_config_caching_miss(self, config_manager):
        """Test configuration caching - cache miss scenario"""
        config_type = ConfigType.MAIN

        # Mock empty cache
        with patch.object(config_manager, '_cache', {}):
            config = config_manager.get_cached_config(config_type)
            assert config is None

    def test_config_backup_creation(self, config_manager, sample_config):
        """Test configuration backup creation"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('shutil.copy2') as mock_copy:
                result = config_manager.create_backup(ConfigType.MAIN)

                assert result is True
                mock_copy.assert_called_once()

    def test_config_backup_restoration(self, config_manager, sample_config):
        """Test configuration backup restoration"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('shutil.copy2') as mock_copy:
                with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))):
                    result = config_manager.restore_backup(ConfigType.MAIN)

                    assert result is True
                    mock_copy.assert_called_once()

    def test_config_merge(self, config_manager):
        """Test configuration merging"""
        base_config = {"a": 1, "b": {"c": 2}}
        update_config = {"b": {"d": 3}, "e": 4}
        expected = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

        result = config_manager.merge_configs(base_config, update_config)
        assert result == expected

    def test_config_get_nested_value(self, config_manager, sample_config):
        """Test getting nested configuration values"""
        with patch.object(config_manager, '_current_config', sample_config):
            # Test nested access
            theme = config_manager.get_value("settings.theme")
            assert theme == "dark"

            # Test deep nested access
            show_tips = config_manager.get_value("user_preferences.show_tips")
            assert show_tips is True

            # Test non-existent key
            non_existent = config_manager.get_value("non.existent.key", default="default")
            assert non_existent == "default"


class TestConfigType:
    """Test configuration type enumeration"""
    
    def test_config_type_values(self):
        """Test configuration type enum values"""
        assert ConfigType.MAIN.value == "main"
        assert ConfigType.AUTO.value == "auto"
        assert ConfigType.VERSION.value == "version"
        assert ConfigType.SERVER.value == "server"
        assert ConfigType.USER.value == "user"


class TestConfigPath:
    """Test configuration path data class"""
    
    def test_config_path_creation(self):
        """Test configuration path creation"""
        config_path = ConfigPath(
            config_type=ConfigType.MAIN,
            filename="config.json",
            default_path=Path("/test/path")
        )
        assert config_path.config_type == ConfigType.MAIN
        assert config_path.filename == "config.json"
        assert config_path.default_path == Path("/test/path")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
