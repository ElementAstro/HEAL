#!/usr/bin/env python3
"""
Modern build script for HEAL application.
Supports different build types and platforms.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class HEALBuilder:
    """Builder for HEAL application."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.src_dir = project_root / "src" / "heal"
        self.build_dir = project_root / "build"
        self.dist_dir = project_root / "dist"

    def clean(self) -> None:
        """Clean build artifacts and cache files."""
        print("Cleaning build artifacts...")

        # Remove build directories
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  Removed {dir_path}")

        # Remove __pycache__ directories
        for root, dirs, files in os.walk(self.project_root):
            for dir_name in dirs[:]:
                if dir_name == "__pycache__":
                    cache_path = Path(root) / dir_name
                    shutil.rmtree(cache_path)
                    print(f"  Removed {cache_path}")
                    dirs.remove(dir_name)

        # Remove .pyc files
        for pyc_file in self.project_root.rglob("*.pyc"):
            pyc_file.unlink()
            print(f"  Removed {pyc_file}")

    def install_dependencies(self, dev: bool = False) -> None:
        """Install project dependencies."""
        print("Installing dependencies...")

        requirements_file = (
            "requirements-build.txt" if not dev else "requirements-dev.txt"
        )

        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True
            )

            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                check=True,
            )

            print("Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install dependencies: {e}")
            sys.exit(1)

    def build_executable(self, debug: bool = False) -> None:
        """Build executable using PyInstaller."""
        print("Building executable...")

        main_script = self.project_root / "main.py"
        icon_path = self.src_dir / "resources" / "images" / "icon.ico"

        cmd = [
            "pyinstaller",
            "--name",
            "HEAL",
            "--icon",
            str(icon_path),
            "--add-data",
            f"{self.src_dir / 'resources'};src/heal/resources",
            "--add-data",
            f"{self.project_root / 'config'};config",
        ]

        if not debug:
            cmd.append("--windowed")

        cmd.append(str(main_script))

        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            print("Executable built successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to build executable: {e}")
            sys.exit(1)

    def package_application(self, output_dir: Optional[Path] = None) -> None:
        """Package the application with all resources."""
        print("Packaging application...")

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

        # Copy additional resources
        resources_to_copy = [
            ("config", "config"),
            ("icons", "icons"),
            ("README.md", "README.md"),
            ("LICENSE", "LICENSE"),
        ]

        for src_name, dst_name in resources_to_copy:
            src_path = self.project_root / src_name
            dst_path = output_dir / dst_name

            if src_path.exists():
                if src_path.is_dir():
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
                print(f"  Copied {src_name}")

        print(f"Application packaged in {output_dir}")

    def run_tests(self) -> None:
        """Run the test suite."""
        print("Running tests...")

        try:
            subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v"],
                check=True,
                cwd=self.project_root,
            )
            print("All tests passed")
        except subprocess.CalledProcessError as e:
            print(f"Tests failed: {e}")
            return False
        return True

    def build(
        self,
        clean: bool = True,
        debug: bool = False,
        run_tests: bool = False,
        package: bool = True,
    ):
        """Complete build process."""
        print("Starting HEAL build process...")

        if clean:
            self.clean()

        self.install_dependencies()

        if run_tests:
            if not self.run_tests():
                print("Build aborted due to test failures")
                sys.exit(1)

        self.build_executable(debug=debug)

        if package:
            self.package_application()

        print("Build completed successfully!")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Build HEAL application")
    parser.add_argument("--no-clean", action="store_true", help="Skip cleaning step")
    parser.add_argument("--debug", action="store_true", help="Build debug version")
    parser.add_argument("--test", action="store_true", help="Run tests before building")
    parser.add_argument("--no-package", action="store_true", help="Skip packaging step")
    parser.add_argument(
        "--dev", action="store_true", help="Install development dependencies"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    builder = HEALBuilder(project_root)

    builder.build(
        clean=not args.no_clean,
        debug=args.debug,
        run_tests=args.test,
        package=not args.no_package,
    )


if __name__ == "__main__":
    main()
