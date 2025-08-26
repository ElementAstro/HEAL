#!/usr/bin/env python3
"""
Modern cross-platform build script for HEAL application.
Supports different build types, platforms, and packaging formats.
"""

import argparse
import logging
import os
import platform
import shutil
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Type, Literal

# Import logging configuration
try:
    from logging_config import setup_logging, log_operation, log_system_info, log_environment_info, ErrorHandler  # type: ignore
except ImportError:
    # Fallback if logging module is not available

    def setup_logging(name: str, level: str = "INFO", log_dir: Optional[Path] = None, enable_debug: bool = False) -> logging.Logger:
        logging.basicConfig(level=getattr(logging, level.upper()))
        return logging.getLogger(name)

    class _FallbackLogOperation:
        def __init__(self, logger: logging.Logger, operation: str, **context: Any) -> None:
            self.logger = logger
            self.operation = operation

        def __enter__(self) -> "_FallbackLogOperation":
            self.logger.info(f"Starting {self.operation}")
            return self

        def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Any) -> Literal[False]:
            if exc_type is None:
                self.logger.info(f"Completed {self.operation}")
            else:
                self.logger.error(f"Failed {self.operation}: {exc_val}")
            return False

    log_operation = _FallbackLogOperation

    def log_system_info(logger: logging.Logger) -> None:
        logger.info("System info logging not available")

    def log_environment_info(logger: logging.Logger) -> None:
        logger.info("Environment info logging not available")

    class _FallbackErrorHandler:
        def __init__(self, logger: logging.Logger) -> None:
            self.logger = logger

        def handle_subprocess_error(self, e: Exception, command: str, context: Optional[Dict[str, Any]] = None) -> None:
            self.logger.error(f"Command failed: {command} - {e}")

        def handle_file_error(self, e: Exception, file_path: str, operation: str) -> None:
            self.logger.error(f"File {operation} failed: {file_path} - {e}")

        def handle_build_error(self, e: Exception, stage: str, platform: Optional[str] = None) -> None:
            self.logger.error(f"Build failed at {stage}: {e}")

    ErrorHandler = _FallbackErrorHandler

# Import our custom modules
try:
    from .platform_configs import PlatformConfig
    from .resource_bundler import ResourceBundler
    from .package_builders import PackageBuilder
except ImportError:
    # Handle relative imports when run as script
    import sys
    sys.path.append(str(Path(__file__).parent))
    try:
        from platform_configs import PlatformConfig  # type: ignore
        from resource_bundler import ResourceBundler  # type: ignore
        from package_builders import PackageBuilder  # type: ignore
    except ImportError:
        # Fallback if modules are not available
        PlatformConfig = None  # type: ignore
        ResourceBundler = None  # type: ignore
        PackageBuilder = None  # type: ignore


class HEALBuilder:
    """Cross-platform builder for HEAL application."""

    def __init__(self, project_root: Path, enable_debug: bool = False) -> None:
        self.project_root = project_root
        self.src_dir = project_root / "src" / "heal"
        self.build_dir = project_root / "build"
        self.dist_dir = project_root / "dist"

        # Set up logging
        self.logger = setup_logging(
            "heal-build",
            level="DEBUG" if enable_debug else "INFO",
            log_dir=project_root / "logs",
            enable_debug=enable_debug
        )
        self.error_handler = ErrorHandler(self.logger)

        # Platform detection
        self.platform = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.is_windows = self.platform == "windows"
        self.is_macos = self.platform == "darwin"
        self.is_linux = self.platform == "linux"

        # Log system information
        log_system_info(self.logger)
        log_environment_info(self.logger)

        self.logger.info(
            f"Initializing HEAL builder for {self.platform} ({self.architecture})")

        # Platform-specific configurations
        self.platform_config = self._get_platform_config()

        # Initialize resource bundler and package builder
        try:
            self.resource_bundler: Optional[Any] = ResourceBundler(
                project_root) if ResourceBundler is not None else None
            self.package_builder: Optional[Any] = PackageBuilder(
                project_root) if PackageBuilder is not None else None
            if self.resource_bundler:
                self.logger.debug("Resource bundler initialized")
            if self.package_builder:
                self.logger.debug("Package builder initialized")
        except Exception as e:
            self.logger.warning(
                f"Failed to initialize optional components: {e}")
            self.resource_bundler = None
            self.package_builder = None

    def _get_platform_config(self) -> Dict[str, Any]:
        """Get platform-specific configuration."""
        base_config = {
            "executable_name": "HEAL",
            "icon_path": self.src_dir / "resources" / "images" / "icon.ico",
            "additional_data": [
                (self.src_dir / "resources", "src/heal/resources"),
                (self.project_root / "config", "config"),
            ],
            "hidden_imports": [
                "PySide6.QtCore",
                "PySide6.QtGui",
                "PySide6.QtWidgets",
                "qfluentwidgets",
                "loguru",
                "psutil",
                "aiofiles",
            ],
            "exclude_modules": [
                "tkinter",
                "matplotlib.backends._backend_tk",
            ],
        }

        if self.is_windows:
            base_config.update({
                "executable_extension": ".exe",
                "icon_path": self.src_dir / "resources" / "images" / "icon.ico",
                "additional_options": ["--windowed"],
                "package_formats": ["zip", "msi"],
            })
        elif self.is_macos:
            base_config.update({
                "executable_extension": "",
                "icon_path": self.src_dir / "resources" / "images" / "icon.icns",
                "additional_options": ["--windowed", "--osx-bundle-identifier", "com.elementastro.heal"],
                "package_formats": ["dmg", "zip"],
            })
        elif self.is_linux:
            base_config.update({
                "executable_extension": "",
                "icon_path": self.src_dir / "resources" / "images" / "icon.png",
                "additional_options": [],
                "package_formats": ["tar.gz", "appimage"],
            })

        return base_config

    def clean(self) -> None:
        """Clean build artifacts and cache files."""
        with log_operation(self.logger, "clean build artifacts"):
            # Remove build directories
            for dir_path in [self.build_dir, self.dist_dir]:
                if dir_path.exists():
                    try:
                        shutil.rmtree(dir_path)
                        self.logger.info(f"Removed {dir_path}")
                    except Exception as e:
                        self.error_handler.handle_file_error(
                            e, str(dir_path), "remove")
                        raise
                else:
                    self.logger.debug(
                        f"Directory {dir_path} does not exist, skipping")

            # Remove __pycache__ directories
            cache_count = 0
            for root, dirs, files in os.walk(self.project_root):
                for dir_name in dirs[:]:
                    if dir_name == "__pycache__":
                        cache_path = Path(root) / dir_name
                        try:
                            shutil.rmtree(cache_path)
                            cache_count += 1
                            dirs.remove(dir_name)
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to remove cache directory {cache_path}: {e}")

            if cache_count > 0:
                self.logger.info(
                    f"Removed {cache_count} __pycache__ directories")

            # Remove .pyc files
            pyc_count = 0
            for pyc_file in self.project_root.rglob("*.pyc"):
                try:
                    pyc_file.unlink()
                    pyc_count += 1
                except Exception as e:
                    self.logger.warning(
                        f"Failed to remove .pyc file {pyc_file}: {e}")

            if pyc_count > 0:
                self.logger.info(f"Removed {pyc_count} .pyc files")

    def install_dependencies(self, dev: bool = False) -> None:
        """Install project dependencies."""
        dep_type = "development" if dev else "build"
        with log_operation(self.logger, f"install {dep_type} dependencies"):
            requirements_file = (
                "requirements-build.txt" if not dev else "requirements-dev.txt"
            )

            try:
                # Upgrade pip first
                pip_cmd = [sys.executable, "-m", "pip",
                           "install", "--upgrade", "pip"]
                self.logger.debug(f"Upgrading pip: {' '.join(pip_cmd)}")
                subprocess.run(pip_cmd, check=True,
                               capture_output=True, text=True)
                self.logger.debug("pip upgraded successfully")

                # Install requirements
                req_cmd = [sys.executable, "-m", "pip",
                           "install", "-r", requirements_file]
                self.logger.debug(
                    f"Installing requirements: {' '.join(req_cmd)}")

                result = subprocess.run(
                    req_cmd, check=True, capture_output=True, text=True)

                self.logger.info(
                    f"{dep_type.capitalize()} dependencies installed successfully")
                if result.stdout:
                    self.logger.debug(
                        f"pip install output: {result.stdout[:500]}...")

            except subprocess.CalledProcessError as e:
                self.error_handler.handle_subprocess_error(e, ' '.join(req_cmd if 'req_cmd' in locals() else pip_cmd), {
                    'requirements_file': requirements_file,
                    'dependency_type': dep_type
                })
                raise

    def build_executable(self, debug: bool = False, use_nuitka: bool = False) -> None:
        """Build executable using PyInstaller or Nuitka."""
        print(f"Building executable for {self.platform}...")

        if use_nuitka:
            self._build_with_nuitka(debug)
        else:
            self._build_with_pyinstaller(debug)

    def _build_with_pyinstaller(self, debug: bool = False) -> None:
        """Build executable using PyInstaller with platform-specific spec files."""
        # Determine the appropriate spec file
        spec_file = self._get_platform_spec_file()

        if spec_file and spec_file.exists():
            # Use platform-specific spec file
            cmd = ["pyinstaller", "--clean", "--noconfirm", str(spec_file)]

            if debug:
                cmd.extend(["--debug", "all"])
        else:
            # Fallback to command-line arguments
            self._build_with_pyinstaller_args(debug)
            return

        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            print(
                f"Executable built successfully with PyInstaller using {spec_file.name}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to build executable with PyInstaller: {e}")
            sys.exit(1)

    def _get_platform_spec_file(self) -> Optional[Path]:
        """Get the platform-specific PyInstaller spec file."""
        if self.is_windows:
            return self.project_root / "pyinstaller-windows.spec"
        elif self.is_macos:
            return self.project_root / "pyinstaller-macos.spec"
        elif self.is_linux:
            return self.project_root / "pyinstaller-linux.spec"
        return None

    def _build_with_pyinstaller_args(self, debug: bool = False) -> None:
        """Fallback PyInstaller build using command-line arguments."""
        main_script = self.project_root / "main.py"
        config = self.platform_config

        cmd = [
            "pyinstaller",
            "--name", config["executable_name"],
            "--clean",
            "--noconfirm",
        ]

        # Add icon if it exists
        if config["icon_path"].exists():
            cmd.extend(["--icon", str(config["icon_path"])])

        # Add data files with platform-specific separators
        separator = ";" if self.is_windows else ":"
        for src, dst in config["additional_data"]:
            if src.exists():
                cmd.extend(["--add-data", f"{src}{separator}{dst}"])

        # Add hidden imports
        for import_name in config["hidden_imports"]:
            cmd.extend(["--hidden-import", import_name])

        # Add excluded modules
        for module in config["exclude_modules"]:
            cmd.extend(["--exclude-module", module])

        # Add platform-specific options
        if not debug:
            cmd.extend(config["additional_options"])

        # Add debug options
        if debug:
            cmd.extend(["--debug", "all", "--console"])

        cmd.append(str(main_script))

        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            print("Executable built successfully with PyInstaller")
        except subprocess.CalledProcessError as e:
            print(f"Failed to build executable with PyInstaller: {e}")
            sys.exit(1)

    def _build_with_nuitka(self, debug: bool = False) -> None:
        """Build executable using Nuitka for better performance."""
        main_script = self.project_root / "main.py"
        config = self.platform_config

        cmd = [
            "python", "-m", "nuitka",
            "--standalone",
            "--assume-yes-for-downloads",
            f"--output-filename={config['executable_name']}{config['executable_extension']}",
        ]

        # Add icon if it exists
        if config["icon_path"].exists():
            cmd.append(f"--windows-icon-from-ico={config['icon_path']}")

        # Include data directories
        for src, _ in config["additional_data"]:
            if src.exists():
                cmd.append(f"--include-data-dir={src}={src.name}")

        # Platform-specific options
        if self.is_windows and not debug:
            cmd.append("--windows-disable-console")
        elif self.is_macos:
            cmd.append("--macos-create-app-bundle")

        # Optimization options
        if not debug:
            cmd.extend([
                "--optimize-for-size",
                "--remove-output",
            ])

        cmd.append(str(main_script))

        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            print("Executable built successfully with Nuitka")
        except subprocess.CalledProcessError as e:
            print(f"Failed to build executable with Nuitka: {e}")
            sys.exit(1)

    def package_application(self, output_dir: Optional[Path] = None) -> None:
        """Package the application with all resources using cross-platform bundler."""
        print("Packaging application with cross-platform resource bundling...")

        if output_dir is None:
            output_dir = self.project_root / "HEAL-Package"

        # Clean output directory
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)

        # Copy executable
        exe_source = self.dist_dir / "HEAL"
        if exe_source.exists():
            shutil.copytree(exe_source, output_dir / "HEAL")
            print("  Copied executable")

        # Use resource bundler if available
        if self.resource_bundler:
            try:
                self.resource_bundler.bundle_resources(
                    output_dir, self.platform)
                self.resource_bundler.optimize_resources(output_dir)
                self.resource_bundler.create_installer_resources(
                    output_dir, self.platform)

                # Validate the bundle
                if self.resource_bundler.validate_resources(output_dir):
                    print("  Resource bundle validation passed")
                else:
                    print("  WARNING: Resource bundle validation failed")

            except Exception as e:
                print(f"  WARNING: Resource bundling failed: {e}")
                self._fallback_resource_copy(output_dir)
        else:
            # Fallback to basic resource copying
            self._fallback_resource_copy(output_dir)

        print(f"Application packaged in {output_dir}")

    def _fallback_resource_copy(self, output_dir: Path) -> None:
        """Fallback resource copying method."""
        print("  Using fallback resource copying...")

        resources_to_copy = [
            ("config", "config"),
            ("icons", "icons"),
            ("README.md", "README.md"),
            ("LICENSE", "LICENSE"),
            ("INSTALL.md", "INSTALL.md"),
        ]

        for src_name, dst_name in resources_to_copy:
            src_path = self.project_root / src_name
            dst_path = output_dir / dst_name

            if src_path.exists():
                if src_path.is_dir():
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
                print(f"    Copied {src_name}")

    def run_tests(self) -> bool:
        """Run the test suite."""
        print("Running tests...")

        try:
            subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v"],
                check=True,
                cwd=self.project_root,
            )
            print("All tests passed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Tests failed: {e}")
            return False

    def create_platform_package(self, package_format: str = "auto") -> List[Path]:
        """Create platform-specific package formats."""
        print(f"Creating {package_format} package for {self.platform}...")

        if package_format == "auto":
            formats = self.platform_config.get("package_formats", ["zip"])
        else:
            formats = [package_format]

        created_packages = []
        source_dir = self.project_root / "HEAL-Package"

        for fmt in formats:
            try:
                # Try advanced package builder first
                package_path = self._create_platform_package_advanced(
                    fmt, source_dir)
                if package_path and package_path.exists():
                    created_packages.append(package_path)
                    print(
                        f"Successfully created {fmt} package: {package_path.name}")
                else:
                    print(f"Failed to create {fmt} package")
            except Exception as e:
                print(f"Error creating {fmt} package: {e}")

        if not created_packages:
            # Fallback to ZIP if nothing was created
            print("No packages created successfully. Creating fallback ZIP package...")
            zip_package = self._create_zip_package()
            created_packages.append(zip_package)

        return created_packages

    def _create_platform_package_advanced(self, package_format: str, source_dir: Path) -> Optional[Path]:
        """Create platform-specific package using advanced builders."""
        if self.package_builder:
            output_dir = self.project_root
            result = self.package_builder.build_package(source_dir, output_dir, package_format)
            return result if isinstance(result, Path) else None
        else:
            # Fallback to basic packaging
            if package_format in ["zip"]:
                return self._create_zip_package()
            elif package_format in ["tar.gz"]:
                return self._create_tarball_package()
            else:
                print(
                    f"Advanced package builder not available. Creating ZIP package instead.")
                return self._create_zip_package()

    def _create_zip_package(self) -> Path:
        """Create ZIP package."""
        import zipfile

        package_name = f"HEAL-{self.platform}-{self.architecture}.zip"
        package_path = self.project_root / package_name

        source_dir = self.project_root / "HEAL-Package"
        if not source_dir.exists():
            source_dir = self.dist_dir / "HEAL"

        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(source_dir.parent)
                    zipf.write(file_path, arcname)

        print(f"Created ZIP package: {package_path}")
        return package_path

    def _create_tarball_package(self) -> Path:
        """Create tar.gz package."""
        import tarfile

        package_name = f"HEAL-{self.platform}-{self.architecture}.tar.gz"
        package_path = self.project_root / package_name

        source_dir = self.project_root / "HEAL-Package"
        if not source_dir.exists():
            source_dir = self.dist_dir / "HEAL"

        with tarfile.open(package_path, 'w:gz') as tar:
            tar.add(source_dir, arcname="HEAL")

        print(f"Created tarball package: {package_path}")
        return package_path

    def build(
        self,
        clean: bool = True,
        debug: bool = False,
        run_tests: bool = False,
        package: bool = True,
        use_nuitka: bool = False,
        package_format: str = "auto",
    ) -> None:
        """Complete cross-platform build process."""
        print(f"Starting HEAL build process for {self.platform}...")
        print(f"Architecture: {self.architecture}")
        print(f"Configuration: {self.platform_config}")

        if clean:
            self.clean()

        self.install_dependencies()

        if run_tests:
            if not self.run_tests():
                print("Build aborted due to test failures")
                sys.exit(1)

        self.build_executable(debug=debug, use_nuitka=use_nuitka)

        if package:
            self.package_application()
            created_packages = self.create_platform_package(package_format)

            print("\nPackaging Summary:")
            print("=" * 50)
            for package_path in created_packages:
                size_mb = package_path.stat().st_size / (1024 * 1024)
                print(f"  {package_path.name} ({size_mb:.1f} MB)")

        print("\nBuild completed successfully!")


def main() -> None:
    """Main function with enhanced cross-platform options."""
    parser = argparse.ArgumentParser(
        description="Cross-platform build script for HEAL application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/build.py                    # Standard build
  python scripts/build.py --debug           # Debug build
  python scripts/build.py --use-nuitka      # Build with Nuitka
  python scripts/build.py --package-format zip  # Create ZIP package only
  python scripts/build.py --test --no-package  # Test only, no packaging
        """
    )

    parser.add_argument("--no-clean", action="store_true",
                        help="Skip cleaning step")
    parser.add_argument("--debug", action="store_true",
                        help="Build debug version")
    parser.add_argument("--test", action="store_true",
                        help="Run tests before building")
    parser.add_argument("--no-package", action="store_true",
                        help="Skip packaging step")
    parser.add_argument("--dev", action="store_true",
                        help="Install development dependencies")
    parser.add_argument("--use-nuitka", action="store_true",
                        help="Use Nuitka instead of PyInstaller")
    parser.add_argument(
        "--package-format",
        choices=["auto", "zip", "msi", "dmg", "appimage", "tar.gz"],
        default="auto",
        help="Package format to create (default: auto-detect based on platform)"
    )
    parser.add_argument("--verbose", "-v",
                        action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Set up logging level based on arguments
    enable_debug = args.debug or args.verbose

    project_root = Path(__file__).parent.parent

    try:
        builder = HEALBuilder(project_root, enable_debug=enable_debug)

        if args.verbose:
            builder.logger.info(f"Platform: {platform.system()}")
            builder.logger.info(f"Architecture: {platform.machine()}")
            builder.logger.info(f"Python version: {sys.version}")

        builder.build(
            clean=not args.no_clean,
            debug=args.debug,
            run_tests=args.test,
            package=not args.no_package,
            use_nuitka=args.use_nuitka,
            package_format=args.package_format,
        )

    except Exception as e:
        # If builder was created, use its logger, otherwise use basic logging
        if 'builder' in locals():
            builder.logger.critical(f"Build failed with critical error: {e}")
            builder.logger.debug("Full traceback:", exc_info=True)
        else:
            print(f"CRITICAL ERROR: Build failed during initialization: {e}")
            traceback.print_exc()

        sys.exit(1)


if __name__ == "__main__":
    main()
