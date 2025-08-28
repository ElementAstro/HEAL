"""
Configuration Validator - 配置文件验证器
提供配置文件的完整验证机制，确保配置的正确性和安全性
Enhanced with performance optimizations and caching
"""

import json
import os
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

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
class ValidationCacheEntry:
    """验证缓存条目"""

    result: 'ValidationResult'
    file_hash: str
    validation_time: float
    cache_time: float = field(default_factory=time.time)


@dataclass
class ValidationResult:
    """验证结果 - Enhanced with performance metrics"""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]
    fixed_issues: List[str]
    validation_time: float = 0.0
    cache_hit: bool = False

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
    """配置验证器 - Enhanced with performance optimizations"""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.NORMAL,
                 enable_cache: bool = True) -> None:
        self.validation_level = validation_level
        self.enable_cache = enable_cache
        self.logger = logger.bind(component="ConfigValidator")

        # 配置文件模式定义
        self.schemas = self._load_schemas()

        # 默认值
        self.default_values = self._load_default_values()

        # Validation cache
        self.validation_cache: Dict[str, ValidationCacheEntry] = {}
        self.cache_ttl = 300.0  # 5 minutes
        self.max_cache_size = 100

        # Performance tracking
        self.validation_stats = {
            "total_validations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_validation_time": 0.0,
            "average_validation_time": 0.0
        }

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

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception:
            return ""

    def _is_cache_valid(self, file_path: str) -> bool:
        """检查缓存是否有效"""
        if not self.enable_cache or file_path not in self.validation_cache:
            return False

        cache_entry = self.validation_cache[file_path]
        current_time = time.time()

        # Check TTL
        if current_time - cache_entry.cache_time > self.cache_ttl:
            return False

        # Check file hash
        current_hash = self._calculate_file_hash(file_path)
        if current_hash != cache_entry.file_hash:
            return False

        return True

    def _update_cache(self, file_path: str, result: ValidationResult) -> None:
        """更新验证缓存"""
        if not self.enable_cache:
            return

        try:
            file_hash = self._calculate_file_hash(file_path)

            # Clean cache if full
            if len(self.validation_cache) >= self.max_cache_size:
                self._cleanup_cache()

            self.validation_cache[file_path] = ValidationCacheEntry(
                result=result,
                file_hash=file_hash,
                validation_time=result.validation_time
            )

            self.logger.debug(f"Updated validation cache for {file_path}")

        except Exception as e:
            self.logger.warning(f"Failed to update validation cache: {e}")

    def _cleanup_cache(self) -> None:
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []

        for file_path, cache_entry in self.validation_cache.items():
            if current_time - cache_entry.cache_time > self.cache_ttl:
                expired_keys.append(file_path)

        for key in expired_keys:
            del self.validation_cache[key]

        self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def validate_file(self, file_path: str, auto_fix: bool = False) -> ValidationResult:
        """验证单个配置文件 - Enhanced with caching"""
        start_time = time.time()

        # Check cache first
        if self._is_cache_valid(file_path):
            cache_entry = self.validation_cache[file_path]
            cached_result = cache_entry.result
            cached_result.cache_hit = True
            self.validation_stats["cache_hits"] += 1
            self.logger.debug(f"Cache hit for validation of {file_path}")
            return cached_result

        self.validation_stats["cache_misses"] += 1

        result = ValidationResult(True, [], [], [], [])

        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                result.add_error(f"配置文件不存在: {file_path}")

                if auto_fix:
                    self._create_default_config(file_path, result)

                result.validation_time = time.time() - start_time
                self._update_cache(file_path, result)
                return result

            # 检查文件权限
            if not os.access(file_path, os.R_OK):
                result.add_error(f"无法读取配置文件: {file_path}")
                result.validation_time = time.time() - start_time
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
                            self._fix_schema_issues(
                                config_data, filename, result)

            # 自定义验证规则
            self._validate_custom_rules(
                config_data, filename, result, auto_fix)

            # 安全性检查
            self._validate_security(config_data, filename, result)

            self.logger.debug(f"配置文件验证完成: {file_path}")

        except Exception as e:
            result.add_error(f"验证过程中发生错误: {e}")
            self.logger.error(f"验证配置文件时发生错误 {file_path}: {e}")

        # Update performance stats
        validation_time = time.time() - start_time
        result.validation_time = validation_time

        self.validation_stats["total_validations"] += 1
        self.validation_stats["total_validation_time"] += validation_time
        self.validation_stats["average_validation_time"] = (
            self.validation_stats["total_validation_time"] /
            self.validation_stats["total_validations"]
        )

        # Update cache
        self._update_cache(file_path, result)

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
                            fix_missing_fields(
                                data[key], default_value, current_path)

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

    def clear_cache(self, file_path: Optional[str] = None) -> None:
        """清除验证缓存"""
        if file_path:
            if file_path in self.validation_cache:
                del self.validation_cache[file_path]
                self.logger.debug(f"Cleared validation cache for {file_path}")
        else:
            self.validation_cache.clear()
            self.logger.debug("Cleared all validation cache")

    def get_validation_stats(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        cache_entries = []
        for file_path, cache_entry in self.validation_cache.items():
            cache_entries.append({
                "file_path": file_path,
                "validation_time": cache_entry.validation_time,
                "cache_age": time.time() - cache_entry.cache_time,
                "file_hash": cache_entry.file_hash[:8]  # First 8 chars
            })

        return {
            **self.validation_stats,
            "cache_enabled": self.enable_cache,
            "cache_entries": len(self.validation_cache),
            "max_cache_size": self.max_cache_size,
            "cache_ttl": self.cache_ttl,
            "cache_details": cache_entries
        }


# 全局配置验证器实例 - 启用缓存
config_validator = ConfigValidator(enable_cache=True)


def validate_config_file(file_path: str, auto_fix: bool = False) -> ValidationResult:
    """验证单个配置文件的便捷函数"""
    return config_validator.validate_file(file_path, auto_fix)


def validate_all_configs(auto_fix: bool = False) -> Dict[str, ValidationResult]:
    """验证所有配置文件的便捷函数"""
    return config_validator.validate_all_configs(auto_fix=auto_fix)
