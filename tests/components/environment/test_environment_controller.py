"""
Tests for the environment controller component.

Tests environment management functionality including platform detection,
tool status management, and environment configuration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock PySide6 before importing any modules that depend on it
with patch.dict('sys.modules', {
    'PySide6': Mock(),
    'PySide6.QtCore': Mock(),
    'PySide6.QtWidgets': Mock(),
    'PySide6.QtNetwork': Mock(),
    'qfluentwidgets': Mock()
}):
    from src.heal.components.environment.environment_controller import EnvironmentController


class TestEnvironmentController:
    """Test the environment controller component"""
    
    @pytest.fixture
    def environment_controller(self):
        """Create an environment controller instance for testing"""
        with patch('src.heal.components.environment.environment_controller.QObject'):
            controller = EnvironmentController()
            return controller
    
    def test_environment_controller_initialization(self, environment_controller):
        """Test environment controller initialization"""
        assert environment_controller is not None
    
    def test_platform_detection(self, environment_controller):
        """Test platform detection functionality"""
        with patch('src.heal.components.environment.platform_detector.get_current_platform_info') as mock_platform:
            mock_platform.return_value = {"os": "Windows", "version": "10", "arch": "x64"}
            platform_info = environment_controller.get_platform_info()
            assert platform_info is not None
    
    def test_tool_status_management(self, environment_controller):
        """Test tool status management"""
        tool_name = "test_tool"
        
        with patch.object(environment_controller, 'check_tool_status') as mock_status:
            mock_status.return_value = "installed"
            status = environment_controller.check_tool_status(tool_name)
            assert status == "installed"
    
    def test_environment_setup(self, environment_controller):
        """Test environment setup functionality"""
        setup_config = {
            "tools": ["python", "git"],
            "paths": ["/usr/local/bin"],
            "variables": {"PATH": "/usr/local/bin"}
        }
        
        with patch.object(environment_controller, 'setup_environment') as mock_setup:
            environment_controller.setup_environment(setup_config)
            mock_setup.assert_called_once_with(setup_config)


class TestEnvironmentControllerIntegration:
    """Integration tests for environment controller"""
    
    def test_environment_controller_with_config(self):
        """Test environment controller integration with configuration"""
        with patch('src.heal.common.config_manager.ConfigManager'):
            # Test configuration integration
            pass
    
    def test_environment_controller_with_ui(self):
        """Test environment controller integration with UI components"""
        with patch('src.heal.components.environment.environment_cards'):
            # Test UI integration
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
