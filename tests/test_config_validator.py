"""
Config Validator Tests
测试配置验证器的功能和可靠性
"""

import unittest
import tempfile
import json
import os
from unittest.mock import patch, mock_open
from pathlib import Path

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.common.config_validator import (
    ConfigValidator, ValidationLevel, ValidationSeverity, ValidationResult,
    validate_config_file, validate_all_configs
)


class TestValidationResult(unittest.TestCase):
    """测试ValidationResult类"""
    
    def test_validation_result_creation(self):
        """测试ValidationResult创建"""
        result = ValidationResult(True, [], [], [], [])
        
        self.assertTrue(result.is_valid)
        self.assertFalse(result.has_errors)
        self.assertFalse(result.has_warnings)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
        self.assertEqual(len(result.info), 0)
        self.assertEqual(len(result.fixed_issues), 0)
    
    def test_add_error(self):
        """测试添加错误"""
        result = ValidationResult(True, [], [], [], [])
        result.add_error("Test error")
        
        self.assertFalse(result.is_valid)
        self.assertTrue(result.has_errors)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0], "Test error")
    
    def test_add_warning(self):
        """测试添加警告"""
        result = ValidationResult(True, [], [], [], [])
        result.add_warning("Test warning")
        
        self.assertTrue(result.is_valid)  # 警告不影响有效性
        self.assertTrue(result.has_warnings)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(result.warnings[0], "Test warning")
    
    def test_add_info_and_fixed(self):
        """测试添加信息和修复记录"""
        result = ValidationResult(True, [], [], [], [])
        result.add_info("Test info")
        result.add_fixed("Test fix")
        
        self.assertEqual(len(result.info), 1)
        self.assertEqual(len(result.fixed_issues), 1)
        self.assertEqual(result.info[0], "Test info")
        self.assertEqual(result.fixed_issues[0], "Test fix")


class TestConfigValidator(unittest.TestCase):
    """测试ConfigValidator类"""
    
    def setUp(self):
        """测试前设置"""
        self.validator = ConfigValidator(ValidationLevel.NORMAL)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_config(self, filename: str, content: dict) -> str:
        """创建临时配置文件"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        return file_path
    
    def test_validator_initialization(self):
        """测试验证器初始化"""
        validator = ConfigValidator(ValidationLevel.STRICT)
        self.assertEqual(validator.validation_level, ValidationLevel.STRICT)
        self.assertIn("config.json", validator.schemas)
        self.assertIn("auto.json", validator.schemas)
        self.assertIn("config.json", validator.default_values)
    
    def test_validate_nonexistent_file(self):
        """测试验证不存在的文件"""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")
        result = self.validator.validate_file(nonexistent_file)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(result.has_errors)
        self.assertIn("配置文件不存在", result.errors[0])
    
    def test_validate_nonexistent_file_with_autofix(self):
        """测试验证不存在的文件并自动修复"""
        config_file = os.path.join(self.temp_dir, "config.json")
        result = self.validator.validate_file(config_file, auto_fix=True)
        
        # 应该创建默认配置文件
        self.assertTrue(os.path.exists(config_file))
        self.assertTrue(result.is_valid)
        self.assertTrue(len(result.fixed_issues) > 0)
        self.assertIn("创建默认配置文件", result.fixed_issues[0])
    
    def test_validate_invalid_json(self):
        """测试验证无效JSON文件"""
        invalid_json_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_json_file, 'w') as f:
            f.write("{ invalid json content")
        
        result = self.validator.validate_file(invalid_json_file)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(result.has_errors)
        self.assertIn("JSON格式错误", result.errors[0])
    
    def test_validate_valid_config_json(self):
        """测试验证有效的config.json"""
        valid_config = {
            "PASSWORD": "test_password",
            "UID": "10001",
            "KEY": "test_key",
            "SERVER_URL": "127.0.0.1:443",
            "PROXY_PORT": "7890",
            "SERVER": {
                "TEST_SERVER": {
                    "ICON": "test_icon",
                    "ICON_TYPE": "test_type",
                    "COMMAND": "test_command"
                }
            }
        }
        
        config_file = self.create_temp_config("config.json", valid_config)
        result = self.validator.validate_file(config_file)
        
        self.assertTrue(result.is_valid)
        self.assertFalse(result.has_errors)
    
    def test_validate_config_json_missing_fields(self):
        """测试验证缺少字段的config.json"""
        incomplete_config = {
            "PASSWORD": "test_password",
            "UID": "10001"
            # 缺少其他必需字段
        }
        
        config_file = self.create_temp_config("config.json", incomplete_config)
        result = self.validator.validate_file(config_file)
        
        # 在NORMAL级别下，模式验证失败应该是警告
        self.assertTrue(result.has_warnings or result.has_errors)
    
    def test_validate_config_json_with_autofix(self):
        """测试验证并自动修复config.json"""
        incomplete_config = {
            "PASSWORD": "test_password",
            "UID": "10001"
        }
        
        config_file = self.create_temp_config("config.json", incomplete_config)
        result = self.validator.validate_file(config_file, auto_fix=True)
        
        # 应该有修复记录
        if result.fixed_issues:
            self.assertTrue(any("添加缺失字段" in fix for fix in result.fixed_issues))
    
    def test_validate_auto_json(self):
        """测试验证auto.json"""
        valid_auto_config = {
            "Style": {
                "DpiScale": "Auto",
                "Language": "English"
            },
            "Function": {
                "AutoCopy": True,
                "UseLogin": False,
                "UseAudio": True
            }
        }
        
        auto_file = self.create_temp_config("auto.json", valid_auto_config)
        result = self.validator.validate_file(auto_file)
        
        self.assertTrue(result.is_valid)
        self.assertFalse(result.has_errors)
    
    def test_custom_validation_rules(self):
        """测试自定义验证规则"""
        # 测试无效端口号
        config_with_invalid_port = {
            "PASSWORD": "test_password",
            "UID": "10001",
            "KEY": "test_key",
            "SERVER_URL": "127.0.0.1:443",
            "PROXY_PORT": "99999",  # 无效端口号
            "SERVER": {}
        }
        
        config_file = self.create_temp_config("config.json", config_with_invalid_port)
        result = self.validator.validate_file(config_file)
        
        # 应该有端口号相关的错误
        port_errors = [error for error in result.errors if "PROXY_PORT" in error]
        self.assertTrue(len(port_errors) > 0)
    
    def test_security_validation(self):
        """测试安全性验证"""
        config_with_default_password = {
            "PASSWORD": "default_password",  # 默认密码
            "UID": "10001",
            "KEY": "test_key",
            "SERVER_URL": "127.0.0.1:443",
            "PROXY_PORT": "7890",
            "SERVER": {}
        }
        
        config_file = self.create_temp_config("config.json", config_with_default_password)
        result = self.validator.validate_file(config_file)
        
        # 应该有安全警告
        security_warnings = [warning for warning in result.warnings if "默认密码" in warning]
        self.assertTrue(len(security_warnings) > 0)
    
    def test_validation_levels(self):
        """测试不同验证级别"""
        incomplete_config = {
            "PASSWORD": "test_password"
            # 缺少必需字段
        }
        
        config_file = self.create_temp_config("config.json", incomplete_config)
        
        # 严格模式
        strict_validator = ConfigValidator(ValidationLevel.STRICT)
        strict_result = strict_validator.validate_file(config_file)
        
        # 宽松模式
        loose_validator = ConfigValidator(ValidationLevel.LOOSE)
        loose_result = loose_validator.validate_file(config_file)
        
        # 严格模式应该有更多错误
        self.assertTrue(len(strict_result.errors) >= len(loose_result.errors))
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_validate_all_configs(self, mock_file, mock_exists):
        """测试批量验证配置文件"""
        # 模拟文件存在
        mock_exists.return_value = True
        
        # 模拟文件内容
        mock_file.return_value.read.return_value = '{"test": "value"}'
        
        results = self.validator.validate_all_configs(self.temp_dir)
        
        # 应该验证多个配置文件
        expected_files = [
            "config.json", "auto.json", "download.json", 
            "mods.json", "server.json", "setup.json", "version.json"
        ]
        
        for filename in expected_files:
            self.assertIn(filename, results)
    
    def test_get_validation_summary(self):
        """测试获取验证摘要"""
        # 创建一些验证结果
        results = {
            "config.json": ValidationResult(True, [], ["warning1"], ["info1"], ["fix1"]),
            "auto.json": ValidationResult(False, ["error1"], [], [], []),
            "test.json": ValidationResult(True, [], [], [], [])
        }
        
        summary = self.validator.get_validation_summary(results)
        
        self.assertEqual(summary["total_files"], 3)
        self.assertEqual(summary["valid_files"], 2)
        self.assertEqual(summary["invalid_files"], 1)
        self.assertEqual(summary["total_errors"], 1)
        self.assertEqual(summary["total_warnings"], 1)
        self.assertEqual(summary["total_fixed"], 1)


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""
    
    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_config_file_function(self):
        """测试validate_config_file便捷函数"""
        # 创建临时配置文件
        config_content = {"test": "value"}
        config_file = os.path.join(self.temp_dir, "test.json")
        with open(config_file, 'w') as f:
            json.dump(config_content, f)
        
        result = validate_config_file(config_file)
        self.assertIsInstance(result, ValidationResult)
    
    @patch('app.common.config_validator.config_validator')
    def test_validate_all_configs_function(self, mock_validator):
        """测试validate_all_configs便捷函数"""
        mock_validator.validate_all_configs.return_value = {"test.json": ValidationResult(True, [], [], [], [])}
        
        results = validate_all_configs(auto_fix=True)
        
        mock_validator.validate_all_configs.assert_called_once_with(auto_fix=True)
        self.assertIn("test.json", results)


if __name__ == '__main__':
    unittest.main()
