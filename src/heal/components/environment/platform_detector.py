"""
Platform Detection Utility
Automatically detects user's operating system and architecture for smart platform-specific options
"""

import platform
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from src.heal.common.logging_config import get_logger


class PlatformType(Enum):
    """支持的平台类型"""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


class ArchitectureType(Enum):
    """支持的架构类型"""

    X64 = "x64"
    X86 = "x86"
    ARM64 = "arm64"
    ARM = "arm"
    UNKNOWN = "unknown"


@dataclass
class PlatformInfo:
    """平台信息数据类"""

    platform_type: PlatformType
    architecture: ArchitectureType
    platform_name: str
    architecture_name: str
    python_version: str
    is_64bit: bool

    def __str__(self) -> str:
        return f"{self.platform_name} {self.architecture_name}"

    def get_platform_key(self) -> str:
        """获取平台键值，用于匹配下载选项"""
        if self.platform_type == PlatformType.WINDOWS:
            return f"windows_{self.architecture.value}"
        elif self.platform_type == PlatformType.MACOS:
            return "macos"
        elif self.platform_type == PlatformType.LINUX:
            return "linux"
        return "unknown"


class PlatformDetector:
    """平台检测器"""

    def __init__(self) -> None:
        self.logger = get_logger(
            "platform_detector", module="PlatformDetector")
        self._platform_info: Optional[PlatformInfo] = None
        self._detect_platform()

    def _detect_platform(self) -> None:
        """检测当前平台信息"""
        try:
            # 检测操作系统
            system = platform.system().lower()
            platform_type = self._get_platform_type(system)

            # 检测架构
            machine = platform.machine().lower()
            architecture = self._get_architecture_type(machine)

            # 获取详细信息
            platform_name = platform.platform()
            architecture_name = platform.machine()
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            is_64bit = sys.maxsize > 2**32

            self._platform_info = PlatformInfo(
                platform_type=platform_type,
                architecture=architecture,
                platform_name=platform_name,
                architecture_name=architecture_name,
                python_version=python_version,
                is_64bit=is_64bit,
            )

            self.logger.info(f"平台检测完成: {self._platform_info}")

        except Exception as e:
            self.logger.error(f"平台检测失败: {e}")
            self._platform_info = PlatformInfo(
                platform_type=PlatformType.UNKNOWN,
                architecture=ArchitectureType.UNKNOWN,
                platform_name="Unknown",
                architecture_name="Unknown",
                python_version="Unknown",
                is_64bit=False,
            )

    def _get_platform_type(self, system: str) -> PlatformType:
        """根据系统名称获取平台类型"""
        if "windows" in system:
            return PlatformType.WINDOWS
        elif "darwin" in system or "macos" in system:
            return PlatformType.MACOS
        elif "linux" in system:
            return PlatformType.LINUX
        else:
            return PlatformType.UNKNOWN

    def _get_architecture_type(self, machine: str) -> ArchitectureType:
        """根据机器类型获取架构类型"""
        if machine in ["x86_64", "amd64"]:
            return ArchitectureType.X64
        elif machine in ["i386", "i686", "x86"]:
            return ArchitectureType.X86
        elif machine in ["arm64", "aarch64"]:
            return ArchitectureType.ARM64
        elif machine.startswith("arm"):
            return ArchitectureType.ARM
        else:
            return ArchitectureType.UNKNOWN

    def get_platform_info(self) -> PlatformInfo:
        """获取平台信息"""
        if self._platform_info is None:
            raise RuntimeError("Platform information not detected")
        return self._platform_info

    def get_recommended_options(self, available_options: List[Dict]) -> List[Dict]:
        """根据当前平台推荐下载选项"""
        if not available_options or self._platform_info is None:
            return []

        platform_key = self._platform_info.get_platform_key()
        recommended = []
        others = []

        for option in available_options:
            option_key = option.get("key", "").lower()
            if platform_key in option_key:
                recommended.append(option)
            else:
                others.append(option)

        # 推荐选项在前，其他选项在后
        return recommended + others

    def is_platform_supported(self, option_key: str) -> bool:
        """检查选项是否支持当前平台"""
        if self._platform_info is None:
            return False
        platform_key = self._platform_info.get_platform_key()
        return platform_key in option_key.lower()

    def get_platform_display_name(self) -> str:
        """获取平台显示名称"""
        if self._platform_info is None:
            return "Unknown Platform"
        if self._platform_info.platform_type == PlatformType.WINDOWS:
            return f"Windows {self._platform_info.architecture.value.upper()}"
        elif self._platform_info.platform_type == PlatformType.MACOS:
            return "macOS"
        elif self._platform_info.platform_type == PlatformType.LINUX:
            return "Linux"
        else:
            return "Unknown Platform"

    def get_system_requirements_info(self) -> Dict[str, str]:
        """获取系统需求信息"""
        if self._platform_info is None:
            return {"platform": "Unknown", "architecture": "Unknown", "python_version": "Unknown", "is_64bit": "Unknown"}
        return {
            "platform": self.get_platform_display_name(),
            "architecture": self._platform_info.architecture_name,
            "python_version": self._platform_info.python_version,
            "64bit_support": "Yes" if self._platform_info.is_64bit else "No",
        }


# 全局实例
platform_detector = PlatformDetector()


def get_platform_detector() -> PlatformDetector:
    """获取平台检测器实例"""
    return platform_detector


def get_current_platform_info() -> PlatformInfo:
    """获取当前平台信息的便捷函数"""
    return platform_detector.get_platform_info()


def get_recommended_download_options(available_options: List[Dict]) -> List[Dict]:
    """获取推荐下载选项的便捷函数"""
    return platform_detector.get_recommended_options(available_options)
