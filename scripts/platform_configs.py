#!/usr/bin/env python3
"""
Platform-specific build configurations for HEAL application.
Contains detailed configurations for Windows, macOS, and Linux builds.
"""

import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PlatformConfig:
    """Platform-specific configuration manager."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src" / "heal"
        self.platform = platform.system().lower()
        self.architecture = platform.machine().lower()

    def get_pyinstaller_config(self, debug: bool = False) -> Dict[str, any]:
        """Get PyInstaller configuration for current platform."""
        base_config = self._get_base_config()

        if self.platform == "windows":
            return self._get_windows_config(base_config, debug)
        elif self.platform == "darwin":
            return self._get_macos_config(base_config, debug)
        elif self.platform == "linux":
            return self._get_linux_config(base_config, debug)
        else:
            return base_config

    def _get_base_config(self) -> Dict[str, any]:
        """Get base configuration common to all platforms."""
        return {
            "name": "HEAL",
            "main_script": self.project_root / "main.py",
            "clean": True,
            "noconfirm": True,
            "onedir": True,  # Create one-directory bundle
            "additional_data": [
                (self.src_dir / "resources", "src/heal/resources"),
                (self.project_root / "config", "config"),
            ],
            "hidden_imports": [
                "PySide6.QtCore",
                "PySide6.QtGui",
                "PySide6.QtWidgets",
                "PySide6.QtNetwork",
                "qfluentwidgets",
                "loguru",
                "psutil",
                "aiofiles",
                "jsonschema",
                "matplotlib",
                "requests",
            ],
            "exclude_modules": [
                "tkinter",
                "matplotlib.backends._backend_tk",
                "PIL.ImageTk",
                "PyQt5",
                "PyQt6",
            ],
            "collect_submodules": [
                "qfluentwidgets",
            ],
            "collect_data": [
                "qfluentwidgets",
            ],
        }

    def _get_windows_config(self, base_config: Dict, debug: bool) -> Dict[str, any]:
        """Get Windows-specific configuration."""
        config = base_config.copy()

        # Windows-specific settings
        config.update({
            "icon": self.src_dir / "resources" / "images" / "icon.ico",
            "windowed": not debug,  # No console window unless debug
            "uac_admin": False,  # Don't require admin privileges
            "version_file": self._create_version_file(),
        })

        # Windows-specific hidden imports
        config["hidden_imports"].extend([
            "win32api",
            "win32con",
            "win32gui",
            "pywintypes",
        ])

        # Windows-specific data files
        config["additional_data"].extend([
            (self.project_root / "icons", "icons"),
        ])

        return config

    def _get_macos_config(self, base_config: Dict, debug: bool) -> Dict[str, any]:
        """Get macOS-specific configuration."""
        config = base_config.copy()

        # macOS-specific settings
        config.update({
            "icon": self.src_dir / "resources" / "images" / "icon.icns",
            "windowed": not debug,
            "osx_bundle_identifier": "com.elementastro.heal",
            "codesign_identity": None,  # Set if code signing is available
        })

        # macOS-specific hidden imports
        config["hidden_imports"].extend([
            "Foundation",
            "AppKit",
        ])

        return config

    def _get_linux_config(self, base_config: Dict, debug: bool) -> Dict[str, any]:
        """Get Linux-specific configuration."""
        config = base_config.copy()

        # Linux-specific settings
        config.update({
            "icon": self.src_dir / "resources" / "images" / "icon.png",
            "strip": not debug,  # Strip debug symbols unless debug build
        })

        # Linux-specific hidden imports
        config["hidden_imports"].extend([
            "gi",
            "gi.repository.Gtk",
        ])

        return config

    def _create_version_file(self) -> Optional[Path]:
        """Create Windows version file."""
        if self.platform != "windows":
            return None

        version_content = """
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'ElementAstro'),
            StringStruct(u'FileDescription', u'HEAL - Hello ElementAstro Launcher'),
            StringStruct(u'FileVersion', u'1.0.0.0'),
            StringStruct(u'InternalName', u'HEAL'),
            StringStruct(u'LegalCopyright', u'Copyright (C) 2024 ElementAstro'),
            StringStruct(u'OriginalFilename', u'HEAL.exe'),
            StringStruct(u'ProductName', u'HEAL'),
            StringStruct(u'ProductVersion', u'1.0.0.0')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
        version_file = self.project_root / "version_info.py"
        version_file.write_text(version_content.strip())
        return version_file

    def get_nuitka_config(self, debug: bool = False) -> List[str]:
        """Get Nuitka configuration for current platform."""
        base_args = [
            "--standalone",
            "--assume-yes-for-downloads",
            f"--output-filename=HEAL",
            "--enable-plugin=pyside6",
        ]

        # Add data directories
        for src, _ in self._get_base_config()["additional_data"]:
            if src.exists():
                base_args.append(f"--include-data-dir={src}={src.name}")

        if self.platform == "windows":
            base_args.extend(self._get_nuitka_windows_args(debug))
        elif self.platform == "darwin":
            base_args.extend(self._get_nuitka_macos_args(debug))
        elif self.platform == "linux":
            base_args.extend(self._get_nuitka_linux_args(debug))

        return base_args

    def _get_nuitka_windows_args(self, debug: bool) -> List[str]:
        """Get Windows-specific Nuitka arguments."""
        args = []

        icon_path = self.src_dir / "resources" / "images" / "icon.ico"
        if icon_path.exists():
            args.append(f"--windows-icon-from-ico={icon_path}")

        if not debug:
            args.append("--windows-disable-console")

        return args

    def _get_nuitka_macos_args(self, debug: bool) -> List[str]:
        """Get macOS-specific Nuitka arguments."""
        args = ["--macos-create-app-bundle"]

        icon_path = self.src_dir / "resources" / "images" / "icon.icns"
        if icon_path.exists():
            args.append(f"--macos-app-icon={icon_path}")

        return args

    def _get_nuitka_linux_args(self, debug: bool) -> List[str]:
        """Get Linux-specific Nuitka arguments."""
        args = []

        if not debug:
            args.extend([
                "--optimize-for-size",
                "--remove-output",
            ])

        return args

    def get_resource_paths(self) -> Dict[str, Path]:
        """Get platform-specific resource paths."""
        resources = {
            "images": self.src_dir / "resources" / "images",
            "styles": self.src_dir / "resources" / "styles",
            "translations": self.src_dir / "resources" / "translations",
            "data": self.src_dir / "resources" / "data",
            "config": self.project_root / "config",
        }

        # Platform-specific icon
        if self.platform == "windows":
            resources["icon"] = self.src_dir / \
                "resources" / "images" / "icon.ico"
        elif self.platform == "darwin":
            resources["icon"] = self.src_dir / \
                "resources" / "images" / "icon.icns"
        else:
            resources["icon"] = self.src_dir / \
                "resources" / "images" / "icon.png"

        return resources
