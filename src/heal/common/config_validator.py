"""
Configuration Validator - 配置文件验证器
提供配置文件的完整验证机制，确保配置的正确性和安全性
"""

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jsonschema

from .logging_config import get_logger

logger = get_logger(__name__)


class ValidationLevel(Enum):
    """验证级别"""

    STRICT = "strict"  # 严格验证，任何错误都会失败
    NORMAL = "normal"  # 正常验证，允许一些警告
    LOOSE = "loose"  # 宽松验证，只检查关键错误


class ValidationSeverity(Enum):
    """验证严重性"""

    ERROR = "error"  # 错误，会导致验证失败
    WARNING = "warning"  # 警告，不会导致验证失败
    INFO = "info"  # 信息，仅供参考


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]
    fixed_issues: List[str]

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        self.info.append(message)

    def add_fixed(self, message: str) -> None:
        self.fixed_issues.append(message)


class ConfigValidator:
    """配置验证器"""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.NORMAL) -> None:
        self.validation_level = validation_level
        self.logger = logger.bind(component="ConfigValidator")

        # 配置文件模式定义
        self.schemas = self._load_schemas()

        # 默认值
        self.default_values = self._load_default_values()

    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """加载配置文件模式"""
        return {
            "config.json": {
                "type": "object",
                "required": [
                    "PASSWORD",
                    "UID",
                    "KEY",
                    "SERVER_URL",
                    "PROXY_PORT",
                    "SERVER",
                ],
                "properties": {
                    "PASSWORD": {"type": "string", "minLength": 1},
                    "UID": {"type": "string", "pattern": "^[0-9]+$"},
                    "KEY": {"type": "string", "minLength": 1},
                    "SERVER_URL": {"type": "string", "pattern": "^[^:]+:[0-9]+$"},
                    "ROUTE_APPLY": {"type": "string"},
                    "ROUTE_VERIFY": {"type": "string"},
                    "ROUTE_REMOTE": {"type": "string"},
                    "PROXY_PORT": {"type": "string", "pattern": "^[0-9]+$"},
                    "SERVER": {
                        "type": "object",
                        "patternProperties": {
                            ".*": {
                                "type": "object",
                                "required": ["ICON", "ICON_TYPE", "COMMAND"],
                                "properties": {
                                    "ICON": {"type": "string"},
                                    "ICON_TYPE": {"type": "string"},
                                    "COMMAND": {"type": "string"},
                                },
                            }
                        },
                    },
                },
            },
            "auto.json": {
                "type": "object",
                "properties": {
                    "Style": {
                        "type": "object",
                        "properties": {
                            "DpiScale": {"type": ["string", "number"]},
                            "Language": {"type": "string"},
                        },
                    },
                    "Function": {
                        "type": "object",
                        "properties": {
                            "AutoCopy": {"type": "boolean"},
                            "UseLogin": {"type": "boolean"},
                            "UseAudio": {"type": "boolean"},
                        },
                    },
                    "Proxy": {
                        "type": "object",
                        "properties": {
                            "ProxyStatus": {"type": "boolean"},
                            "ChinaStatus": {"type": "boolean"},
                        },
                    },
                },
            },
        }

    def _load_default_values(self) -> Dict[str, Dict[str, Any]]:
        """加载默认值"""
        return {
            "config.json": {
                "PASSWORD": "default_password",
                "UID": "10001",
                "KEY": "default_key",
                "SERVER_URL": "127.0.0.1:443",
                "ROUTE_APPLY": "/api/fireflylauncherlethe/apply",
                "ROUTE_VERIFY": "/api/fireflylauncherlethe/verify",
                "ROUTE_REMOTE": "/api/fireflylauncherlethe/remote",
                "PROXY_PORT": "7890",
                "SERVER": {},
            },
            "auto.json": {
                "Style": {"DpiScale": "Auto", "Language": "English"},
                "Function": {"AutoCopy": True, "UseLogin": False, "UseAudio": True},
                "Proxy": {"ProxyStatus": True, "ChinaStatus": False},
            },
        }

    def validate_file(self, file_path: str, auto_fix: bool = False) -> ValidationResult:
        """验证单个配置文件"""
        result = ValidationResult(True, [], [], [], [])

        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                result.add_error(f"配置文件不存在: {file_path}")

                if auto_fix:
                    self._create_default_config(file_path, result)

                return result

            # 检查文件权限
            if not os.access(file_path, os.R_OK):
                result.add_error(f"无法读取配置文件: {file_path}")
                return result

            # 加载JSON文件
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except json.JSONDecodeError as e:
                result.add_error(f"JSON格式错误: {e}")
                return result
            except UnicodeDecodeError as e:
                result.add_error(f"文件编码错误: {e}")
                return result

            # 获取文件名用于模式验证
            filename = os.path.basename(file_path)

            # JSON模式验证
            if filename in self.schemas:
                try:
                    jsonschema.validate(config_data, self.schemas[filename])
                    result.add_info(f"JSON模式验证通过: {filename}")
                except jsonschema.ValidationError as e:
                    if self.validation_level == ValidationLevel.STRICT:
                        result.add_error(f"模式验证失败: {e.message}")
                    else:
                        result.add_warning(f"模式验证警告: {e.message}")

                        if auto_fix:
                            self._fix_schema_issues(config_data, filename, result)

            # 自定义验证规则
            self._validate_custom_rules(config_data, filename, result, auto_fix)

            # 安全性检查
            self._validate_security(config_data, filename, result)

            self.logger.debug(f"配置文件验证完成: {file_path}")

        except Exception as e:
            result.add_error(f"验证过程中发生错误: {e}")
            self.logger.error(f"验证配置文件时发生错误 {file_path}: {e}")

        return result

    def _create_default_config(self, file_path: str, result: ValidationResult) -> None:
        """创建默认配置文件"""
        try:
            filename = os.path.basename(file_path)

            if filename in self.default_values:
                # 确保目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # 写入默认配置
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(
                        self.default_values[filename], f, indent=2, ensure_ascii=False
                    )

                result.add_fixed(f"创建默认配置文件: {file_path}")
                result.is_valid = True

        except Exception as e:
            result.add_error(f"创建默认配置文件失败: {e}")

    def _fix_schema_issues(
        self, config_data: Dict[str, Any], filename: str, result: ValidationResult
    ) -> None:
        """修复模式问题"""
        try:
            if filename in self.default_values:
                defaults = self.default_values[filename]
                fixed_count = 0

                # 递归修复缺失的字段
                def fix_missing_fields(
                    data: Dict[str, Any], defaults: Dict[str, Any], path: str = ""
                ) -> None:
                    nonlocal fixed_count

                    for key, default_value in defaults.items():
                        current_path = f"{path}.{key}" if path else key

                        if key not in data:
                            data[key] = default_value
                            result.add_fixed(
                                f"添加缺失字段 {current_path}: {default_value}"
                            )
                            fixed_count += 1
                        elif isinstance(default_value, dict) and isinstance(
                            data[key], dict
                        ):
                            fix_missing_fields(data[key], default_value, current_path)

                fix_missing_fields(config_data, defaults)

                if fixed_count > 0:
                    result.add_info(f"修复了 {fixed_count} 个缺失字段")

        except Exception as e:
            result.add_warning(f"修复模式问题时发生错误: {e}")

    def _validate_custom_rules(
        self,
        config_data: Dict[str, Any],
        filename: str,
        result: ValidationResult,
        auto_fix: bool,
    ) -> None:
        """自定义验证规则"""
        if filename == "config.json":
            # 验证端口号
            if "PROXY_PORT" in config_data:
                try:
                    port = int(config_data["PROXY_PORT"])
                    if not (1 <= port <= 65535):
                        result.add_error("PROXY_PORT 必须在 1-65535 范围内")
                except ValueError:
                    result.add_error("PROXY_PORT 必须是有效的数字")

            # 验证服务器配置
            if "SERVER" in config_data and isinstance(config_data["SERVER"], dict):
                for server_name, server_config in config_data["SERVER"].items():
                    if not isinstance(server_config, dict):
                        result.add_error(f"服务器配置 {server_name} 必须是对象")
                        continue

                    required_fields = ["ICON", "ICON_TYPE", "COMMAND"]
                    for field in required_fields:
                        if field not in server_config:
                            result.add_error(
                                f"服务器 {server_name} 缺少必需字段: {field}"
                            )

    def _validate_security(
        self, config_data: Dict[str, Any], filename: str, result: ValidationResult
    ) -> None:
        """安全性验证"""
        if filename == "config.json":
            # 检查默认密码
            if config_data.get("PASSWORD") == "default_password":
                result.add_warning("使用默认密码存在安全风险")

            # 检查密码强度
            password = config_data.get("PASSWORD", "")
            if len(password) < 8:
                result.add_warning("密码长度建议至少8位")

            # 检查敏感信息
            sensitive_fields = ["PASSWORD", "KEY"]
            for field in sensitive_fields:
                if field in config_data and config_data[field]:
                    result.add_info(f"检测到敏感字段: {field}")

    def validate_all_configs(
        self, config_dir: str = "config", auto_fix: bool = False
    ) -> Dict[str, ValidationResult]:
        """验证所有配置文件"""
        results = {}

        try:
            config_files = [
                "config.json",
                "auto.json",
                "download.json",
                "mods.json",
                "server.json",
                "setup.json",
                "version.json",
            ]

            for config_file in config_files:
                file_path = os.path.join(config_dir, config_file)
                results[config_file] = self.validate_file(file_path, auto_fix)

            self.logger.info(f"配置验证完成，共验证 {len(config_files)} 个文件")

        except Exception as e:
            self.logger.error(f"批量验证配置文件时发生错误: {e}")

        return results

    def get_validation_summary(
        self, results: Dict[str, ValidationResult]
    ) -> Dict[str, Any]:
        """获取验证摘要"""
        total_files = len(results)
        valid_files = sum(1 for r in results.values() if r.is_valid)
        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())
        total_fixed = sum(len(r.fixed_issues) for r in results.values())

        return {
            "total_files": total_files,
            "valid_files": valid_files,
            "invalid_files": total_files - valid_files,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_fixed": total_fixed,
            "validation_level": self.validation_level.value,
        }


# 全局配置验证器实例
config_validator = ConfigValidator()


def validate_config_file(file_path: str, auto_fix: bool = False) -> ValidationResult:
    """验证单个配置文件的便捷函数"""
    return config_validator.validate_file(file_path, auto_fix)


def validate_all_configs(auto_fix: bool = False) -> Dict[str, ValidationResult]:
    """验证所有配置文件的便捷函数"""
    return config_validator.validate_all_configs(auto_fix=auto_fix)
