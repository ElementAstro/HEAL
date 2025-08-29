"""
JSON Utilities - 统一JSON处理工具
消除项目中JSON文件操作的重复代码
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .cache_manager import cached, get_file_cached
from .exception_handler import file_exception_handler
from .logging_config import get_logger
from .performance_analyzer import profile_io, profile_performance

logger = get_logger(__name__)


@dataclass
class JsonLoadResult:
    """JSON加载结果"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class JsonUtils:
    """JSON工具类 - 统一JSON文件操作"""

    @staticmethod
    @file_exception_handler
    @profile_performance(threshold=0.05)  # 监控JSON加载性能
    def load_json_file(
        file_path: Union[str, Path],
        encoding: str = "utf-8",
        create_if_missing: bool = False,
        default_content: Optional[Dict[str, Any]] = None,
    ) -> JsonLoadResult:
        """
        安全地加载JSON文件

        Args:
            file_path: 文件路径
            encoding: 文件编码
            create_if_missing: 如果文件不存在是否创建
            default_content: 文件不存在时的默认内容

        Returns:
            JsonLoadResult: 加载结果
        """
        file_path = Path(file_path)
        result = JsonLoadResult(success=False)

        try:
            # 检查文件是否存在
            if not file_path.exists():
                if create_if_missing and default_content is not None:
                    # 创建默认文件
                    JsonUtils.save_json_file(
                        file_path, default_content, encoding)
                    result.data = default_content
                    result.success = True
                    result.warnings.append(f"文件不存在，已创建默认文件: {file_path}")
                    logger.info(f"创建默认JSON文件: {file_path}")
                else:
                    result.error = f"文件不存在: {file_path}"
                    logger.error(result.error)
                return result

            # 检查文件权限
            if not os.access(file_path, os.R_OK):
                result.error = f"无法读取文件: {file_path}"
                logger.error(result.error)
                return result

            # 读取文件 - 监控IO性能，优先使用缓存
            content: str
            with profile_io(f"json_read_{file_path.name}"):
                # 尝试从文件缓存获取内容
                from .cache_manager import global_cache_manager, FileCache
                file_cache = global_cache_manager.get_cache("file")
                if file_cache and isinstance(file_cache, FileCache):
                    cached_content = file_cache.get_file_content(
                        file_path, encoding)
                    if cached_content is not None:
                        content = cached_content.strip()
                        logger.debug(f"从缓存读取JSON文件: {file_path}")
                    else:
                        with open(file_path, "r", encoding=encoding) as f:
                            content = f.read().strip()
                else:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read().strip()

            # 检查空文件
            if not content:
                if default_content is not None:
                    result.data = default_content
                    result.warnings.append("文件为空，使用默认内容")
                else:
                    result.data = {}
                    result.warnings.append("文件为空，返回空字典")
                result.success = True
                return result

            # 解析JSON
            result.data = json.loads(content)
            result.success = True
            logger.debug(f"成功加载JSON文件: {file_path}")

        except json.JSONDecodeError as e:
            result.error = f"JSON格式错误: {e}"
            logger.error(f"JSON解析失败 {file_path}: {e}")
        except UnicodeDecodeError as e:
            result.error = f"文件编码错误: {e}"
            logger.error(f"文件编码错误 {file_path}: {e}")
        except Exception as e:
            result.error = f"加载文件时发生错误: {e}"
            logger.error(f"加载JSON文件失败 {file_path}: {e}")

        return result

    @staticmethod
    @file_exception_handler
    def save_json_file(
        file_path: Union[str, Path],
        data: Dict[str, Any],
        encoding: str = "utf-8",
        indent: int = 2,
        ensure_ascii: bool = False,
        create_dirs: bool = True,
    ) -> bool:
        """
        安全地保存JSON文件

        Args:
            file_path: 文件路径
            data: 要保存的数据
            encoding: 文件编码
            indent: JSON缩进
            ensure_ascii: 是否确保ASCII编码
            create_dirs: 是否创建目录

        Returns:
            bool: 是否保存成功
        """
        file_path = Path(file_path)

        try:
            # 创建目录
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存文件 - 使用性能监控
            with profile_io(f"json_write_{file_path.name}"):
                with open(file_path, "w", encoding=encoding) as f:
                    json.dump(data, f, indent=indent,
                              ensure_ascii=ensure_ascii)

                # 清除相关的文件缓存
                from .cache_manager import global_cache_manager
                file_cache = global_cache_manager.get_cache("file")
                if file_cache:
                    # 清除可能存在的缓存条目
                    mtime = file_path.stat().st_mtime
                    cache_key = f"file:{file_path}:{mtime}:{encoding}"
                    file_cache.remove(cache_key)

            logger.debug(f"成功保存JSON文件: {file_path}")
            return True

        except Exception as e:
            logger.error(f"保存JSON文件失败 {file_path}: {e}")
            return False

    @staticmethod
    @cached(ttl=300)  # 缓存5分钟
    def get_json_value(
        file_path: Union[str, Path],
        key: str,
        default_value: Any | None = None,
        encoding: str = "utf-8",
    ) -> Any:
        """
        从JSON文件获取指定键的值

        Args:
            file_path: 文件路径
            key: 键名
            default_value: 默认值
            encoding: 文件编码

        Returns:
            Any: 键对应的值或默认值
        """
        result = JsonUtils.load_json_file(file_path, encoding)

        if not result.success or result.data is None:
            logger.warning(f"无法从 {file_path} 获取键 {key}，使用默认值")
            return default_value

        return result.data.get(key, default_value)

    @staticmethod
    def update_json_value(
        file_path: Union[str, Path], key: str, value: Any, encoding: str = "utf-8"
    ) -> bool:
        """
        更新JSON文件中指定键的值

        Args:
            file_path: 文件路径
            key: 键名
            value: 新值
            encoding: 文件编码

        Returns:
            bool: 是否更新成功
        """
        # 加载现有数据
        result = JsonUtils.load_json_file(
            file_path, encoding, create_if_missing=True, default_content={}
        )

        if not result.success or result.data is None:
            logger.error(f"无法加载文件进行更新: {file_path}")
            return False

        # 更新值
        result.data[key] = value

        # 保存文件
        # type: ignore
        return JsonUtils.save_json_file(file_path, result.data, encoding)

    @staticmethod
    def merge_json_files(
        source_path: Union[str, Path],
        target_path: Union[str, Path],
        encoding: str = "utf-8",
        deep_merge: bool = True,
    ) -> bool:
        """
        合并两个JSON文件

        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            encoding: 文件编码
            deep_merge: 是否深度合并

        Returns:
            bool: 是否合并成功
        """
        # 加载源文件
        source_result = JsonUtils.load_json_file(source_path, encoding)
        if not source_result.success or source_result.data is None:
            logger.error(f"无法加载源文件: {source_path}")
            return False

        # 加载目标文件
        target_result = JsonUtils.load_json_file(
            target_path, encoding, create_if_missing=True, default_content={}
        )
        if not target_result.success or target_result.data is None:
            logger.error(f"无法加载目标文件: {target_path}")
            return False

        # 合并数据
        if deep_merge:
            merged_data = JsonUtils._deep_merge(
                target_result.data, source_result.data)
        else:
            merged_data = {**target_result.data, **source_result.data}

        # 保存合并结果
        # type: ignore
        return JsonUtils.save_json_file(target_path, merged_data, encoding)

    @staticmethod
    def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并两个字典

        Args:
            dict1: 字典1
            dict2: 字典2

        Returns:
            Dict[str, Any]: 合并后的字典
        """
        result = dict1.copy()

        for key, value in dict2.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = JsonUtils._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def validate_json_schema(
        data: Dict[str, Any],
        required_keys: List[str],
        optional_keys: Optional[List[str]] = None,
    ) -> List[str]:
        """
        验证JSON数据结构

        Args:
            data: 要验证的数据
            required_keys: 必需的键
            optional_keys: 可选的键

        Returns:
            List[str]: 验证错误列表
        """
        errors = []

        # 检查必需键
        for key in required_keys:
            if key not in data:
                errors.append(f"缺少必需键: {key}")

        # 检查未知键
        if optional_keys is not None:
            allowed_keys = set(required_keys + optional_keys)
            for key in data.keys():
                if key not in allowed_keys:
                    errors.append(f"未知键: {key}")

        return errors


# 便捷函数
def load_config_json(
    file_path: Union[str, Path], default_config: Optional[Dict[str, Any]] = None
) -> JsonLoadResult:
    """加载配置JSON文件的便捷函数"""
    return JsonUtils.load_json_file(  # type: ignore
        file_path, create_if_missing=True, default_content=default_config or {}
    )


def save_config_json(file_path: Union[str, Path], config: Dict[str, Any]) -> bool:
    """保存配置JSON文件的便捷函数"""
    return JsonUtils.save_json_file(file_path, config)  # type: ignore


def get_config_value(
    file_path: Union[str, Path], key: str, default_value: Any | None = None
) -> Any:
    """从配置文件获取值的便捷函数"""
    return JsonUtils.get_json_value(file_path, key, default_value)


def update_config_value(file_path: Union[str, Path], key: str, value: Any) -> bool:
    """更新配置文件值的便捷函数"""
    return JsonUtils.update_json_value(file_path, key, value)


# 向后兼容的函数，替换原有的get_json函数
def get_json(file_path: Union[str, Path], key: str) -> Any:
    """
    向后兼容的get_json函数
    替换原有的简单实现，增加错误处理和验证
    """
    try:
        # 使用配置验证器验证文件
        from .config_validator import validate_config_file

        validation_result = validate_config_file(str(file_path), auto_fix=True)

        if not validation_result.is_valid:
            logger.error(f"配置文件验证失败: {file_path}")
            for error in validation_result.errors:
                logger.error(f"  错误: {error}")

        if validation_result.warnings:
            for warning in validation_result.warnings:
                logger.warning(f"  警告: {warning}")

        # 使用新的JSON工具加载文件
        result = JsonUtils.load_json_file(file_path)

        # Handle case where result is None (from exception handler)
        if result is None:
            raise Exception(f"Failed to load JSON file: {file_path}")

        if not result.success or result.data is None:
            raise Exception(result.error or "Failed to load JSON file")

        if key not in result.data:
            raise KeyError(f"键 '{key}' 不存在于配置文件 {file_path}")

        return result.data[key]

    except Exception as e:
        logger.error(f"加载配置文件失败 {file_path}: {e}")
        raise


class AsyncJsonUtils:
    """异步JSON工具类 - 提供高性能的异步JSON操作"""

    @staticmethod
    async def load_json_file_async(
        file_path: Union[str, Path],
        default_content: Optional[Dict[str, Any]] = None,
        encoding: str = "utf-8"
    ) -> JsonLoadResult:
        """异步加载JSON文件"""
        from .async_io_utils import global_async_file_manager

        result = JsonLoadResult(success=False)
        file_path = Path(file_path)

        try:
            # 使用异步文件管理器读取
            async_result = await global_async_file_manager.read_json_async(file_path)

            if async_result.success:
                result.data = async_result.data
                result.success = True
                logger.debug(f"异步加载JSON文件成功: {file_path}")
            else:
                if not file_path.exists() and default_content is not None:
                    # 异步创建默认文件
                    save_result = await global_async_file_manager.write_json_async(file_path, default_content)
                    if save_result.success:
                        result.data = default_content
                        result.success = True
                        result.warnings.append(f"文件不存在，已创建默认文件: {file_path}")
                    else:
                        result.error = f"创建默认文件失败: {save_result.error}"
                else:
                    result.error = async_result.error or f"文件不存在: {file_path}"

        except Exception as e:
            result.error = f"异步加载JSON文件时发生错误: {e}"
            logger.error(f"异步加载JSON文件失败 {file_path}: {e}")

        return result

    @staticmethod
    async def save_json_file_async(
        file_path: Union[str, Path],
        data: Dict[str, Any],
        encoding: str = "utf-8",
        indent: int = 2,
        create_dirs: bool = True,
    ) -> bool:
        """异步保存JSON文件"""
        from .async_io_utils import global_async_file_manager

        try:
            file_path = Path(file_path)

            # 创建目录
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # 使用异步文件管理器保存
            result = await global_async_file_manager.write_json_async(file_path, data)

            if result.success:
                logger.debug(f"异步保存JSON文件成功: {file_path}")
                return True
            else:
                logger.error(f"异步保存JSON文件失败 {file_path}: {result.error}")
                return False

        except Exception as e:
            logger.error(f"异步保存JSON文件失败 {file_path}: {e}")
            return False


# 异步便捷函数
async def load_config_json_async(
    file_path: Union[str, Path], default_config: Optional[Dict[str, Any]] = None
) -> JsonLoadResult:
    """异步加载配置JSON文件的便捷函数"""
    return await AsyncJsonUtils.load_json_file_async(
        file_path, default_content=default_config or {}
    )


async def save_config_json_async(file_path: Union[str, Path], config: Dict[str, Any]) -> bool:
    """异步保存配置JSON文件的便捷函数"""
    return await AsyncJsonUtils.save_json_file_async(file_path, config)
