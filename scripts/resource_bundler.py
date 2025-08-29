#!/usr/bin/env python3
"""
Cross-platform resource bundling utilities for HEAL application.
Handles platform-specific resource management and path resolution.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ResourceBundler:
    """Cross-platform resource bundling manager."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src" / "heal"
        self.resources_dir = self.src_dir / "resources"

    def bundle_resources(self, output_dir: Path, platform: Optional[str] = None) -> None:
        """Bundle all resources for the target platform."""
        if platform is None:
            platform = sys.platform

        print(f"Bundling resources for {platform}...")

        # Create output directory structure
        self._create_directory_structure(output_dir)

        # Copy core resources
        self._copy_core_resources(output_dir)

        # Copy platform-specific resources
        self._copy_platform_resources(output_dir, platform)

        # Copy configuration files
        self._copy_configuration_files(output_dir)

        # Generate resource manifest
        self._generate_resource_manifest(output_dir)

        print("Resource bundling completed successfully")

    def _create_directory_structure(self, output_dir: Path) -> None:
        """Create the required directory structure."""
        directories = [
            "src/heal/resources/images",
            "src/heal/resources/styles",
            "src/heal/resources/translations",
            "src/heal/resources/data",
            "config",
            "icons",
            "logs",
        ]

        for directory in directories:
            dir_path = output_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)

    def _copy_core_resources(self, output_dir: Path) -> None:
        """Copy core application resources."""
        resource_mappings = [
            (self.resources_dir / "images", output_dir / "src/heal/resources/images"),
            (self.resources_dir / "styles", output_dir / "src/heal/resources/styles"),
            (self.resources_dir / "translations",
             output_dir / "src/heal/resources/translations"),
            (self.resources_dir / "data", output_dir / "src/heal/resources/data"),
        ]

        for src, dst in resource_mappings:
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"  Copied {src.name} resources")

    def _copy_platform_resources(self, output_dir: Path, platform: str) -> None:
        """Copy platform-specific resources."""
        # Platform-specific icons
        icons_src = self.project_root / "icons"
        icons_dst = output_dir / "icons"

        if icons_src.exists():
            if icons_dst.exists():
                shutil.rmtree(icons_dst)
            shutil.copytree(icons_src, icons_dst)
            print("  Copied platform icons")

        # Platform-specific patches/configurations
        patches_src = self.resources_dir / "patches"
        if patches_src.exists():
            patches_dst = output_dir / "src/heal/resources/patches"
            if patches_dst.exists():
                shutil.rmtree(patches_dst)
            shutil.copytree(patches_src, patches_dst)
            print("  Copied platform patches")

    def _copy_configuration_files(self, output_dir: Path) -> None:
        """Copy configuration files."""
        config_src = self.project_root / "config"
        config_dst = output_dir / "config"

        if config_src.exists():
            if config_dst.exists():
                shutil.rmtree(config_dst)
            shutil.copytree(config_src, config_dst)
            print("  Copied configuration files")

        # Copy important root files
        root_files = ["README.md", "LICENSE", "CHANGELOG.md"]
        for filename in root_files:
            src_file = self.project_root / filename
            if src_file.exists():
                dst_file = output_dir / filename
                shutil.copy2(src_file, dst_file)
                print(f"  Copied {filename}")

    def _generate_resource_manifest(self, output_dir: Path) -> None:
        """Generate a manifest of all bundled resources."""
        manifest_path = output_dir / "resource_manifest.txt"

        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write("HEAL Resource Manifest\n")
            f.write("=" * 50 + "\n\n")

            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if file == "resource_manifest.txt":
                        continue
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(output_dir)
                    file_size = file_path.stat().st_size
                    f.write(f"{relative_path} ({file_size} bytes)\n")

        print("  Generated resource manifest")

    def validate_resources(self, bundle_dir: Path) -> bool:
        """Validate that all required resources are present."""
        print("Validating resource bundle...")

        required_resources = [
            "src/heal/resources/images",
            "src/heal/resources/styles",
            "config",
        ]

        missing_resources = []
        for resource in required_resources:
            resource_path = bundle_dir / resource
            if not resource_path.exists():
                missing_resources.append(resource)

        if missing_resources:
            print("ERROR: Missing required resources:")
            for resource in missing_resources:
                print(f"  - {resource}")
            return False

        print("Resource validation passed")
        return True

    def optimize_resources(self, bundle_dir: Path) -> None:
        """Optimize resources for distribution."""
        print("Optimizing resources...")

        # Remove unnecessary files
        unnecessary_patterns = [
            "*.pyc",
            "*.pyo",
            "__pycache__",
            ".DS_Store",
            "Thumbs.db",
            "*.tmp",
            "*.log",
        ]

        removed_count = 0
        for pattern in unnecessary_patterns:
            for file_path in bundle_dir.rglob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    removed_count += 1
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    removed_count += 1

        print(f"  Removed {removed_count} unnecessary files")

        # Compress large text files (optional)
        self._compress_text_files(bundle_dir)

    def _compress_text_files(self, bundle_dir: Path) -> None:
        """Compress large text files to save space."""
        import gzip

        text_extensions = ['.txt', '.md', '.json', '.xml', '.css', '.js']
        min_size = 1024  # Only compress files larger than 1KB

        compressed_count = 0
        for ext in text_extensions:
            for file_path in bundle_dir.rglob(f"*{ext}"):
                if file_path.stat().st_size > min_size:
                    # Create compressed version
                    compressed_path = file_path.with_suffix(
                        file_path.suffix + '.gz')
                    with open(file_path, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # Replace original if compression is beneficial
                    if compressed_path.stat().st_size < file_path.stat().st_size * 0.8:
                        file_path.unlink()
                        compressed_count += 1
                    else:
                        compressed_path.unlink()

        if compressed_count > 0:
            print(f"  Compressed {compressed_count} text files")

    def create_installer_resources(self, bundle_dir: Path, platform: str) -> None:
        """Create platform-specific installer resources."""
        print(f"Creating installer resources for {platform}...")

        if platform.startswith('win'):
            self._create_windows_installer_resources(bundle_dir)
        elif platform == 'darwin':
            self._create_macos_installer_resources(bundle_dir)
        elif platform.startswith('linux'):
            self._create_linux_installer_resources(bundle_dir)

    def _create_windows_installer_resources(self, bundle_dir: Path) -> None:
        """Create Windows installer resources."""
        # Create batch file for easy launching
        batch_content = """@echo off
cd /d "%~dp0"
start "" "HEAL.exe"
"""
        batch_file = bundle_dir / "run_heal.bat"
        batch_file.write_text(batch_content)
        print("  Created Windows launcher script")

    def _create_macos_installer_resources(self, bundle_dir: Path) -> None:
        """Create macOS installer resources."""
        # Create shell script for launching
        script_content = """#!/bin/bash
cd "$(dirname "$0")"
open HEAL.app
"""
        script_file = bundle_dir / "run_heal.sh"
        script_file.write_text(script_content)
        script_file.chmod(0o755)
        print("  Created macOS launcher script")

    def _create_linux_installer_resources(self, bundle_dir: Path) -> None:
        """Create Linux installer resources."""
        # Create desktop entry
        desktop_content = """[Desktop Entry]
Version=1.0
Type=Application
Name=HEAL
Comment=Hello ElementAstro Launcher
Exec={bundle_dir}/HEAL
Icon={bundle_dir}/src/heal/resources/images/icon.png
Terminal=false
Categories=Science;Astronomy;
""".format(bundle_dir=bundle_dir.absolute())

        desktop_file = bundle_dir / "heal.desktop"
        desktop_file.write_text(desktop_content)

        # Create shell script for launching
        script_content = """#!/bin/bash
cd "$(dirname "$0")"
./HEAL
"""
        script_file = bundle_dir / "run_heal.sh"
        script_file.write_text(script_content)
        script_file.chmod(0o755)
        print("  Created Linux launcher resources")
