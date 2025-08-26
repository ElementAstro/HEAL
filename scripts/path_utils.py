#!/usr/bin/env python3
"""
Cross-platform path utilities for HEAL application.
Provides consistent path handling across Windows, macOS, and Linux.
"""

import os
import platform
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union


class CrossPlatformPaths:
    """Cross-platform path resolution utilities."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.platform = platform.system().lower()
        self.is_windows = self.platform == "windows"
        self.is_macos = self.platform == "darwin"
        self.is_linux = self.platform == "linux"

    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize path for current platform."""
        path = Path(path)

        # Resolve relative paths
        if not path.is_absolute():
            path = self.project_root / path

        # Normalize path separators and resolve
        return path.resolve()

    def get_executable_name(self, base_name: str) -> str:
        """Get platform-specific executable name."""
        if self.is_windows:
            return f"{base_name}.exe"
        return base_name

    def get_library_extension(self) -> str:
        """Get platform-specific library extension."""
        if self.is_windows:
            return ".dll"
        elif self.is_macos:
            return ".dylib"
        else:
            return ".so"

    def get_icon_path(self, base_path: Path) -> Path:
        """Get platform-specific icon path."""
        if self.is_windows:
            return base_path / "icon.ico"
        elif self.is_macos:
            return base_path / "icon.icns"
        else:
            return base_path / "icon.png"

    def get_data_separator(self) -> str:
        """Get platform-specific data separator for PyInstaller."""
        return ";" if self.is_windows else ":"

    def get_user_data_dir(self, app_name: str = "HEAL") -> Path:
        """Get platform-specific user data directory."""
        if self.is_windows:
            base = Path(os.environ.get("LOCALAPPDATA", "~\\AppData\\Local"))
        elif self.is_macos:
            base = Path("~/Library/Application Support")
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share"))

        return (base / app_name).expanduser()

    def get_user_config_dir(self, app_name: str = "HEAL") -> Path:
        """Get platform-specific user config directory."""
        if self.is_windows:
            base = Path(os.environ.get("APPDATA", "~\\AppData\\Roaming"))
        elif self.is_macos:
            base = Path("~/Library/Preferences")
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config"))

        return (base / app_name).expanduser()

    def get_user_cache_dir(self, app_name: str = "HEAL") -> Path:
        """Get platform-specific user cache directory."""
        if self.is_windows:
            base = Path(os.environ.get("LOCALAPPDATA", "~\\AppData\\Local"))
            return (base / app_name / "Cache").expanduser()
        elif self.is_macos:
            base = Path("~/Library/Caches")
        else:
            base = Path(os.environ.get("XDG_CACHE_HOME", "~/.cache"))

        return (base / app_name).expanduser()

    def get_temp_dir(self) -> Path:
        """Get platform-specific temporary directory."""
        import tempfile
        return Path(tempfile.gettempdir())

    def create_pyinstaller_data_args(self, data_mappings: List[tuple]) -> List[str]:
        """Create PyInstaller --add-data arguments for current platform."""
        args = []
        separator = self.get_data_separator()

        for src, dst in data_mappings:
            src_path = self.normalize_path(src)
            if src_path.exists():
                args.extend(["--add-data", f"{src_path}{separator}{dst}"])

        return args

    def get_resource_paths(self) -> Dict[str, Path]:
        """Get standard resource paths for the application."""
        src_dir = self.project_root / "src" / "heal"
        resources_dir = src_dir / "resources"

        return {
            "src": src_dir,
            "resources": resources_dir,
            "images": resources_dir / "images",
            "styles": resources_dir / "styles",
            "translations": resources_dir / "translations",
            "data": resources_dir / "data",
            "config": self.project_root / "config",
            "docs": self.project_root / "docs",
            "tests": self.project_root / "tests",
            "scripts": self.project_root / "scripts",
            "build": self.project_root / "build",
            "dist": self.project_root / "dist",
        }

    def get_build_paths(self, build_name: str = "HEAL") -> Dict[str, Path]:
        """Get build-related paths."""
        return {
            "build_dir": self.project_root / "build",
            "dist_dir": self.project_root / "dist",
            "package_dir": self.project_root / f"{build_name}-Package",
            "executable": self.project_root / "dist" / build_name / self.get_executable_name(build_name),
        }

    def ensure_directories(self, paths: List[Path]) -> None:
        """Ensure directories exist, creating them if necessary."""
        for path in paths:
            path = self.normalize_path(path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)

    def safe_copy(self, src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """Safely copy files/directories with error handling."""
        import shutil

        try:
            src_path = self.normalize_path(src)
            dst_path = self.normalize_path(dst)

            if not src_path.exists():
                return False

            # Ensure destination directory exists
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            if src_path.is_dir():
                if dst_path.exists():
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)

            return True

        except Exception as e:
            print(f"Error copying {src} to {dst}: {e}")
            return False

    def get_python_executable(self) -> str:
        """Get the current Python executable path."""
        return sys.executable

    def get_platform_info(self) -> Dict[str, str]:
        """Get detailed platform information."""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
        }

    def is_virtual_env(self) -> bool:
        """Check if running in a virtual environment."""
        return (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        )

    def get_environment_info(self) -> Dict[str, str]:
        """Get environment information for debugging."""
        info = {
            "platform": self.platform,
            "python_executable": self.get_python_executable(),
            "virtual_env": str(self.is_virtual_env()),
            "project_root": str(self.project_root),
        }

        # Add platform-specific environment variables
        if self.is_windows:
            info.update({
                "LOCALAPPDATA": os.environ.get("LOCALAPPDATA", "Not set"),
                "APPDATA": os.environ.get("APPDATA", "Not set"),
                "USERPROFILE": os.environ.get("USERPROFILE", "Not set"),
            })
        else:
            info.update({
                "HOME": os.environ.get("HOME", "Not set"),
                "XDG_DATA_HOME": os.environ.get("XDG_DATA_HOME", "Not set"),
                "XDG_CONFIG_HOME": os.environ.get("XDG_CONFIG_HOME", "Not set"),
                "XDG_CACHE_HOME": os.environ.get("XDG_CACHE_HOME", "Not set"),
            })

        return info


# Convenience functions
def get_cross_platform_paths(project_root: Optional[Path] = None) -> CrossPlatformPaths:
    """Get a CrossPlatformPaths instance."""
    return CrossPlatformPaths(project_root)


def normalize_path(path: Union[str, Path], project_root: Optional[Path] = None) -> Path:
    """Normalize a path for the current platform."""
    cpp = get_cross_platform_paths(project_root)
    return cpp.normalize_path(path)


def get_executable_name(base_name: str) -> str:
    """Get platform-specific executable name."""
    cpp = get_cross_platform_paths()
    return cpp.get_executable_name(base_name)


def get_icon_path(base_path: Path) -> Path:
    """Get platform-specific icon path."""
    cpp = get_cross_platform_paths()
    return cpp.get_icon_path(base_path)
