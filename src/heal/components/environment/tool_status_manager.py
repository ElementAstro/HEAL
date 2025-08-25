"""
Tool Status Management System
Checks installation status of development tools and provides status indicators
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, QTimer, Signal

from src.heal.common.logging_config import get_logger
from .platform_detector import PlatformType, get_current_platform_info


class ToolStatus(Enum):
    """工具状态枚举"""

    INSTALLED = "installed"  # 已安装
    NOT_INSTALLED = "not_installed"  # 未安装
    NEEDS_UPDATE = "needs_update"  # 需要更新
    CHECKING = "checking"  # 检查中
    ERROR = "error"  # 检查出错
    UNKNOWN = "unknown"  # 未知状态


@dataclass
class ToolInfo:
    """工具信息数据类"""

    name: str
    status: ToolStatus
    version: Optional[str] = None
    install_path: Optional[str] = None
    latest_version: Optional[str] = None
    error_message: Optional[str] = None

    def __str__(self) -> str:
        if self.version:
            return f"{self.name} {self.version} ({self.status.value})"
        return f"{self.name} ({self.status.value})"


class ToolStatusManager(QObject):
    """工具状态管理器"""

    # 信号
    status_updated = Signal(str, ToolInfo)  # tool_name, tool_info
    all_status_updated = Signal(dict)  # all_tools_status
    check_started = Signal(str)  # tool_name
    check_completed = Signal(str)  # tool_name

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.logger = get_logger("tool_status_manager", module="ToolStatusManager")
        self.platform_info = get_current_platform_info()

        # 工具状态缓存
        self.tool_status: Dict[str, ToolInfo] = {}

        # 工具检查配置
        self.tool_checkers = {
            "git": self._check_git_status,
            "java": self._check_java_status,
            "mongodb": self._check_mongodb_status,
            "nodejs": self._check_nodejs_status,
            "python": self._check_python_status,
        }

        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_status)
        self.refresh_timer.setInterval(30000)  # 30秒刷新一次

    def start_auto_refresh(self) -> None:
        """启动自动刷新"""
        self.refresh_timer.start()
        self.logger.info("工具状态自动刷新已启动")

    def stop_auto_refresh(self) -> None:
        """停止自动刷新"""
        self.refresh_timer.stop()
        self.logger.info("工具状态自动刷新已停止")

    def check_tool_status(self, tool_name: str) -> ToolInfo:
        """检查单个工具状态"""
        self.check_started.emit(tool_name)

        try:
            if tool_name.lower() in self.tool_checkers:
                checker = self.tool_checkers[tool_name.lower()]
                tool_info = checker()
            else:
                tool_info = ToolInfo(
                    name=tool_name,
                    status=ToolStatus.UNKNOWN,
                    error_message=f"未知工具: {tool_name}",
                )

            self.tool_status[tool_name] = tool_info
            self.status_updated.emit(tool_name, tool_info)
            self.check_completed.emit(tool_name)

            self.logger.debug(f"工具状态检查完成: {tool_info}")
            return tool_info

        except Exception as e:
            error_info = ToolInfo(
                name=tool_name, status=ToolStatus.ERROR, error_message=str(e)
            )
            self.tool_status[tool_name] = error_info
            self.status_updated.emit(tool_name, error_info)
            self.check_completed.emit(tool_name)

            self.logger.error(f"工具状态检查失败 {tool_name}: {e}")
            return error_info

    def refresh_all_status(self) -> None:
        """刷新所有工具状态"""
        self.logger.info("开始刷新所有工具状态")

        for tool_name in self.tool_checkers.keys():
            self.check_tool_status(tool_name)

        self.all_status_updated.emit(self.tool_status.copy())

    def get_tool_status(self, tool_name: str) -> Optional[ToolInfo]:
        """获取工具状态"""
        return self.tool_status.get(tool_name)

    def get_all_status(self) -> Dict[str, ToolInfo]:
        """获取所有工具状态"""
        return self.tool_status.copy()

    def _run_command(self, command: List[str]) -> Tuple[bool, str, str]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10,
                shell=self.platform_info.platform_type == PlatformType.WINDOWS,
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "命令执行超时"
        except Exception as e:
            return False, "", str(e)

    def _check_git_status(self) -> ToolInfo:
        """检查Git状态"""
        # 检查是否在PATH中
        if not shutil.which("git"):
            return ToolInfo(name="Git", status=ToolStatus.NOT_INSTALLED)

        # 获取版本信息
        success, stdout, stderr = self._run_command(["git", "--version"])
        if success and stdout:
            version = stdout.replace("git version ", "").strip()
            return ToolInfo(
                name="Git",
                status=ToolStatus.INSTALLED,
                version=version,
                install_path=shutil.which("git"),
            )

        return ToolInfo(
            name="Git",
            status=ToolStatus.ERROR,
            error_message=stderr or "无法获取版本信息",
        )

    def _check_java_status(self) -> ToolInfo:
        """检查Java状态"""
        if not shutil.which("java"):
            return ToolInfo(name="Java", status=ToolStatus.NOT_INSTALLED)

        success, stdout, stderr = self._run_command(["java", "-version"])
        if success or stderr:  # Java版本信息通常在stderr中
            version_output = stderr or stdout
            # 解析版本信息
            lines = version_output.split("\n")
            if lines:
                version_line = lines[0]
                if "version" in version_line:
                    version = (
                        version_line.split('"')[1] if '"' in version_line else "Unknown"
                    )
                    return ToolInfo(
                        name="Java",
                        status=ToolStatus.INSTALLED,
                        version=version,
                        install_path=shutil.which("java"),
                    )

        return ToolInfo(
            name="Java", status=ToolStatus.ERROR, error_message="无法获取版本信息"
        )

    def _check_mongodb_status(self) -> ToolInfo:
        """检查MongoDB状态"""
        # 检查mongod命令
        mongod_path = shutil.which("mongod")
        if not mongod_path:
            # 检查常见安装路径
            common_paths = [
                "C:\\Program Files\\MongoDB\\Server\\*\\bin\\mongod.exe",
                "/usr/local/bin/mongod",
                "/opt/homebrew/bin/mongod",
            ]

            for path_pattern in common_paths:
                if "*" in path_pattern:
                    # 处理通配符路径
                    import glob

                    matches = glob.glob(path_pattern)
                    if matches:
                        mongod_path = matches[0]
                        break
                elif os.path.exists(path_pattern):
                    mongod_path = path_pattern
                    break

        if not mongod_path:
            return ToolInfo(name="MongoDB", status=ToolStatus.NOT_INSTALLED)

        # 获取版本信息
        success, stdout, stderr = self._run_command([mongod_path, "--version"])
        if success and stdout:
            lines = stdout.split("\n")
            version_line = next(
                (line for line in lines if "version" in line.lower()), ""
            )
            if version_line:
                version = (
                    version_line.split()[-1] if version_line.split() else "Unknown"
                )
                return ToolInfo(
                    name="MongoDB",
                    status=ToolStatus.INSTALLED,
                    version=version,
                    install_path=mongod_path,
                )

        return ToolInfo(
            name="MongoDB", status=ToolStatus.ERROR, error_message="无法获取版本信息"
        )

    def _check_nodejs_status(self) -> ToolInfo:
        """检查Node.js状态"""
        if not shutil.which("node"):
            return ToolInfo(name="Node.js", status=ToolStatus.NOT_INSTALLED)

        success, stdout, stderr = self._run_command(["node", "--version"])
        if success and stdout:
            version = stdout.strip().lstrip("v")
            return ToolInfo(
                name="Node.js",
                status=ToolStatus.INSTALLED,
                version=version,
                install_path=shutil.which("node"),
            )

        return ToolInfo(
            name="Node.js",
            status=ToolStatus.ERROR,
            error_message=stderr or "无法获取版本信息",
        )

    def _check_python_status(self) -> ToolInfo:
        """检查Python状态"""
        import sys

        # 当前运行的Python
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        return ToolInfo(
            name="Python",
            status=ToolStatus.INSTALLED,
            version=version,
            install_path=sys.executable,
        )
