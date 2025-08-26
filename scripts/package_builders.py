#!/usr/bin/env python3
"""
Platform-specific package builders for HEAL application.
Supports MSI (Windows), DMG (macOS), AppImage/DEB (Linux).
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


class PackageBuilder:
    """Base class for platform-specific package builders."""

    def __init__(self, project_root: Path, app_name: str = "HEAL"):
        self.project_root = project_root
        self.app_name = app_name
        self.version = "1.0.0"  # TODO: Get from version file
        self.platform = platform.system().lower()
        self.architecture = platform.machine().lower()

    def build_package(self, source_dir: Path, output_dir: Path, package_format: str) -> Optional[Path]:
        """Build platform-specific package."""
        if package_format == "msi" and self.platform == "windows":
            return self._build_msi(source_dir, output_dir)
        elif package_format == "dmg" and self.platform == "darwin":
            return self._build_dmg(source_dir, output_dir)
        elif package_format == "appimage" and self.platform == "linux":
            return self._build_appimage(source_dir, output_dir)
        elif package_format == "deb" and self.platform == "linux":
            return self._build_deb(source_dir, output_dir)
        elif package_format == "rpm" and self.platform == "linux":
            return self._build_rpm(source_dir, output_dir)
        elif package_format == "zip":
            return self._build_zip(source_dir, output_dir)
        elif package_format == "tar.gz":
            return self._build_tarball(source_dir, output_dir)
        else:
            print(
                f"Package format '{package_format}' not supported on {self.platform}")
            return None

    def _build_zip(self, source_dir: Path, output_dir: Path) -> Path:
        """Build ZIP package (cross-platform)."""
        import zipfile

        package_name = f"{self.app_name}-{self.version}-{self.platform}-{self.architecture}.zip"
        package_path = output_dir / package_name

        print(f"Creating ZIP package: {package_name}")

        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)

        return package_path

    def _build_tarball(self, source_dir: Path, output_dir: Path) -> Path:
        """Build tar.gz package (Unix-like systems)."""
        import tarfile

        package_name = f"{self.app_name}-{self.version}-{self.platform}-{self.architecture}.tar.gz"
        package_path = output_dir / package_name

        print(f"Creating tarball package: {package_name}")

        with tarfile.open(package_path, 'w:gz') as tar:
            tar.add(source_dir, arcname=self.app_name)

        return package_path

    def _build_msi(self, source_dir: Path, output_dir: Path) -> Optional[Path]:
        """Build MSI package for Windows."""
        print("Building MSI package for Windows...")

        # Check if WiX Toolset is available
        if not self._check_wix_toolset():
            print("WiX Toolset not found. Creating ZIP package instead.")
            return self._build_zip(source_dir, output_dir)

        # Create WiX source file
        wxs_file = self._create_wix_source(source_dir, output_dir)
        if not wxs_file:
            return self._build_zip(source_dir, output_dir)

        # Build MSI
        try:
            package_name = f"{self.app_name}-{self.version}-{self.architecture}.msi"
            package_path = output_dir / package_name

            # Compile WiX source
            wixobj_file = wxs_file.with_suffix('.wixobj')
            subprocess.run([
                "candle.exe", str(wxs_file), "-out", str(wixobj_file)
            ], check=True)

            # Link to create MSI
            subprocess.run([
                "light.exe", str(wixobj_file), "-out", str(package_path)
            ], check=True)

            # Cleanup
            wixobj_file.unlink(missing_ok=True)
            wxs_file.unlink(missing_ok=True)

            print(f"MSI package created: {package_name}")
            return package_path

        except subprocess.CalledProcessError as e:
            print(f"MSI build failed: {e}")
            return self._build_zip(source_dir, output_dir)

    def _check_wix_toolset(self) -> bool:
        """Check if WiX Toolset is available."""
        try:
            subprocess.run(["candle.exe", "-?"],
                           capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _create_wix_source(self, source_dir: Path, output_dir: Path) -> Optional[Path]:
        """Create WiX source file for MSI generation."""
        wxs_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="{self.app_name}" Language="1033" Version="{self.version}" 
           Manufacturer="ElementAstro" UpgradeCode="{{12345678-1234-1234-1234-123456789012}}">
    
    <Package InstallerVersion="200" Compressed="yes" InstallScope="perUser" />
    
    <MajorUpgrade DowngradeErrorMessage="A newer version is already installed." />
    
    <MediaTemplate EmbedCab="yes" />
    
    <Feature Id="ProductFeature" Title="{self.app_name}" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
    </Feature>
    
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="LocalAppDataFolder">
        <Directory Id="INSTALLFOLDER" Name="{self.app_name}" />
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="ApplicationProgramsFolder" Name="{self.app_name}" />
      </Directory>
      <Directory Id="DesktopFolder" Name="Desktop" />
    </Directory>
    
    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
      <!-- Application files will be added here -->
      <Component Id="MainExecutable" Guid="*">
        <File Id="HealExe" Source="{source_dir}\\{self.app_name}\\{self.app_name}.exe" KeyPath="yes" />
      </Component>
    </ComponentGroup>
    
    <!-- Start Menu shortcut -->
    <DirectoryRef Id="ApplicationProgramsFolder">
      <Component Id="ApplicationShortcut" Guid="*">
        <Shortcut Id="ApplicationStartMenuShortcut" Name="{self.app_name}" 
                  Description="Hello ElementAstro Launcher" Target="[INSTALLFOLDER]{self.app_name}.exe" 
                  WorkingDirectory="INSTALLFOLDER" />
        <RemoveFolder Id="ApplicationProgramsFolder" On="uninstall" />
        <RegistryValue Root="HKCU" Key="Software\\ElementAstro\\{self.app_name}" 
                       Name="installed" Type="integer" Value="1" KeyPath="yes" />
      </Component>
    </DirectoryRef>
    
    <!-- Desktop shortcut -->
    <DirectoryRef Id="DesktopFolder">
      <Component Id="DesktopShortcut" Guid="*">
        <Shortcut Id="ApplicationDesktopShortcut" Name="{self.app_name}" 
                  Description="Hello ElementAstro Launcher" Target="[INSTALLFOLDER]{self.app_name}.exe" 
                  WorkingDirectory="INSTALLFOLDER" />
        <RegistryValue Root="HKCU" Key="Software\\ElementAstro\\{self.app_name}" 
                       Name="desktop" Type="integer" Value="1" KeyPath="yes" />
      </Component>
    </DirectoryRef>
    
    <Feature Id="ProductFeature" Title="{self.app_name}" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
      <ComponentRef Id="ApplicationShortcut" />
      <ComponentRef Id="DesktopShortcut" />
    </Feature>
    
  </Product>
</Wix>'''

        wxs_file = output_dir / f"{self.app_name}.wxs"
        try:
            wxs_file.write_text(wxs_content, encoding='utf-8')
            return wxs_file
        except Exception as e:
            print(f"Failed to create WiX source: {e}")
            return None

    def _build_dmg(self, source_dir: Path, output_dir: Path) -> Optional[Path]:
        """Build DMG package for macOS."""
        print("Building DMG package for macOS...")

        package_name = f"{self.app_name}-{self.version}.dmg"
        package_path = output_dir / package_name

        try:
            # Create temporary DMG directory
            dmg_dir = output_dir / "dmg_temp"
            dmg_dir.mkdir(exist_ok=True)

            # Copy app bundle
            app_bundle = source_dir / f"{self.app_name}.app"
            if app_bundle.exists():
                shutil.copytree(app_bundle, dmg_dir / f"{self.app_name}.app")
            else:
                # Create simple app structure
                app_dir = dmg_dir / f"{self.app_name}.app"
                app_dir.mkdir()
                shutil.copytree(source_dir, app_dir / "Contents")

            # Create DMG using hdiutil
            subprocess.run([
                "hdiutil", "create", "-volname", self.app_name,
                "-srcfolder", str(dmg_dir),
                "-ov", "-format", "UDZO",
                str(package_path)
            ], check=True)

            # Cleanup
            shutil.rmtree(dmg_dir)

            print(f"DMG package created: {package_name}")
            return package_path

        except subprocess.CalledProcessError as e:
            print(f"DMG build failed: {e}")
            return self._build_zip(source_dir, output_dir)
        except Exception as e:
            print(f"DMG build error: {e}")
            return self._build_zip(source_dir, output_dir)

    def _build_appimage(self, source_dir: Path, output_dir: Path) -> Optional[Path]:
        """Build AppImage package for Linux."""
        print("Building AppImage package for Linux...")

        # Check if appimagetool is available
        if not shutil.which("appimagetool"):
            print("appimagetool not found. Creating tarball instead.")
            return self._build_tarball(source_dir, output_dir)

        try:
            # Create AppDir structure
            appdir = output_dir / f"{self.app_name}.AppDir"
            appdir.mkdir(exist_ok=True)

            # Copy application files
            shutil.copytree(source_dir, appdir / "usr", dirs_exist_ok=True)

            # Create desktop file
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Comment=Hello ElementAstro Launcher
Exec={self.app_name}
Icon={self.app_name}
Categories=Science;Astronomy;
"""
            (appdir / f"{self.app_name}.desktop").write_text(desktop_content)

            # Copy icon
            icon_src = source_dir / "src" / "heal" / "resources" / "images" / "icon.png"
            if icon_src.exists():
                shutil.copy2(icon_src, appdir / f"{self.app_name}.png")

            # Create AppRun script
            apprun_content = f"""#!/bin/bash
cd "$(dirname "$0")"
exec ./usr/{self.app_name} "$@"
"""
            apprun_file = appdir / "AppRun"
            apprun_file.write_text(apprun_content)
            apprun_file.chmod(0o755)

            # Build AppImage
            package_name = f"{self.app_name}-{self.version}-{self.architecture}.AppImage"
            package_path = output_dir / package_name

            subprocess.run([
                "appimagetool", str(appdir), str(package_path)
            ], check=True)

            # Cleanup
            shutil.rmtree(appdir)

            print(f"AppImage created: {package_name}")
            return package_path

        except subprocess.CalledProcessError as e:
            print(f"AppImage build failed: {e}")
            return self._build_tarball(source_dir, output_dir)

    def _build_deb(self, source_dir: Path, output_dir: Path) -> Optional[Path]:
        """Build DEB package for Debian/Ubuntu."""
        print("Building DEB package for Linux...")

        # Check if dpkg-deb is available
        if not shutil.which("dpkg-deb"):
            print("dpkg-deb not found. Creating tarball instead.")
            return self._build_tarball(source_dir, output_dir)

        try:
            # Create package directory structure
            pkg_dir = output_dir / f"{self.app_name.lower()}-{self.version}"
            pkg_dir.mkdir(exist_ok=True)

            # Create DEBIAN directory
            debian_dir = pkg_dir / "DEBIAN"
            debian_dir.mkdir(exist_ok=True)

            # Create control file
            control_content = f"""Package: {self.app_name.lower()}
Version: {self.version}
Section: science
Priority: optional
Architecture: {self._get_deb_architecture()}
Maintainer: ElementAstro <astro_air@126.com>
Description: Hello ElementAstro Launcher
 A comprehensive launcher and management system for astronomical software.
 Supports various astronomical applications and provides an intuitive interface.
"""
            (debian_dir / "control").write_text(control_content)

            # Copy application files
            app_dir = pkg_dir / "opt" / self.app_name.lower()
            app_dir.mkdir(parents=True)
            shutil.copytree(source_dir, app_dir, dirs_exist_ok=True)

            # Create desktop file
            desktop_dir = pkg_dir / "usr" / "share" / "applications"
            desktop_dir.mkdir(parents=True)
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Comment=Hello ElementAstro Launcher
Exec=/opt/{self.app_name.lower()}/{self.app_name}
Icon={self.app_name.lower()}
Categories=Science;Astronomy;
"""
            (desktop_dir /
             f"{self.app_name.lower()}.desktop").write_text(desktop_content)

            # Build DEB package
            package_name = f"{self.app_name.lower()}-{self.version}-{self._get_deb_architecture()}.deb"
            package_path = output_dir / package_name

            subprocess.run([
                "dpkg-deb", "--build", str(pkg_dir), str(package_path)
            ], check=True)

            # Cleanup
            shutil.rmtree(pkg_dir)

            print(f"DEB package created: {package_name}")
            return package_path

        except subprocess.CalledProcessError as e:
            print(f"DEB build failed: {e}")
            return self._build_tarball(source_dir, output_dir)

    def _build_rpm(self, source_dir: Path, output_dir: Path) -> Optional[Path]:
        """Build RPM package for Red Hat/CentOS/Fedora."""
        print("Building RPM package for Linux...")

        # Check if rpmbuild is available
        if not shutil.which("rpmbuild"):
            print("rpmbuild not found. Creating tarball instead.")
            return self._build_tarball(source_dir, output_dir)

        # RPM building is complex and requires proper spec files
        # For now, fall back to tarball
        print("RPM building not fully implemented. Creating tarball instead.")
        return self._build_tarball(source_dir, output_dir)

    def _get_deb_architecture(self) -> str:
        """Get Debian package architecture."""
        arch_map = {
            "x86_64": "amd64",
            "amd64": "amd64",
            "i386": "i386",
            "i686": "i386",
            "aarch64": "arm64",
            "armv7l": "armhf",
        }
        return arch_map.get(self.architecture.lower(), "amd64")
