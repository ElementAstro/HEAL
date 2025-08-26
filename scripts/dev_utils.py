#!/usr/bin/env python3
"""
Development utilities for HEAL project.
Provides common development tasks and project management commands.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class DevUtils:
    """Development utilities for HEAL project."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.src_dir = project_root / "src" / "heal"

    def run_tests(self, verbose: bool = False, coverage: bool = False) -> bool:
        """
        Run the test suite.

        Args:
            verbose: Enable verbose output
            coverage: Generate coverage report

        Returns:
            True if tests pass, False otherwise
        """
        print("Running tests...")

        cmd = [sys.executable, "-m", "pytest"]

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend(["--cov=src/heal", "--cov-report=term-missing"])

        cmd.append("tests/")

        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=True)
            print("All tests passed!")
            return True
        except subprocess.CalledProcessError:
            print("Some tests failed!")
            return False
        except FileNotFoundError:
            print("pytest not found. Install with: pip install pytest")
            return False

    def format_code(self, check_only: bool = False) -> bool:
        """
        Format code using black.

        Args:
            check_only: Only check formatting without making changes

        Returns:
            True if formatting is correct, False otherwise
        """
        print("Formatting code with black...")

        cmd = [sys.executable, "-m", "black"]

        if check_only:
            cmd.append("--check")

        cmd.extend(["src/", "scripts/", "tests/"])

        try:
            subprocess.run(cmd, cwd=self.project_root, check=True)
            print("Code formatting completed!")
            return True
        except subprocess.CalledProcessError:
            if check_only:
                print("Code formatting issues found!")
            else:
                print("Code formatting failed!")
            return False
        except FileNotFoundError:
            print("black not found. Install with: pip install black")
            return False

    def sort_imports(self, check_only: bool = False) -> bool:
        """
        Sort imports using isort.

        Args:
            check_only: Only check import sorting without making changes

        Returns:
            True if imports are correctly sorted, False otherwise
        """
        print("Sorting imports with isort...")

        cmd = [sys.executable, "-m", "isort"]

        if check_only:
            cmd.append("--check-only")

        cmd.extend(["src/", "scripts/", "tests/"])

        try:
            subprocess.run(cmd, cwd=self.project_root, check=True)
            print("Import sorting completed!")
            return True
        except subprocess.CalledProcessError:
            if check_only:
                print("Import sorting issues found!")
            else:
                print("Import sorting failed!")
            return False
        except FileNotFoundError:
            print("isort not found. Install with: pip install isort")
            return False

    def lint_code(self) -> bool:
        """
        Lint code using flake8.

        Returns:
            True if no linting issues, False otherwise
        """
        print("Linting code with flake8...")

        cmd = [sys.executable, "-m", "flake8", "src/", "scripts/", "tests/"]

        try:
            subprocess.run(cmd, cwd=self.project_root, check=True)
            print("No linting issues found!")
            return True
        except subprocess.CalledProcessError:
            print("Linting issues found!")
            return False
        except FileNotFoundError:
            print("flake8 not found. Install with: pip install flake8")
            return False

    def type_check(self) -> bool:
        """
        Type check code using mypy.

        Returns:
            True if no type issues, False otherwise
        """
        print("Type checking with mypy...")

        cmd = [sys.executable, "-m", "mypy", "src/heal/"]

        try:
            subprocess.run(cmd, cwd=self.project_root, check=True)
            print("No type checking issues found!")
            return True
        except subprocess.CalledProcessError:
            print("Type checking issues found!")
            return False
        except FileNotFoundError:
            print("mypy not found. Install with: pip install mypy")
            return False

    def run_quality_checks(self) -> bool:
        """
        Run all quality checks.

        Returns:
            True if all checks pass, False otherwise
        """
        print("Running all quality checks...")

        checks = [
            ("Format check", lambda: self.format_code(check_only=True)),
            ("Import sort check", lambda: self.sort_imports(check_only=True)),
            ("Linting", self.lint_code),
            ("Type checking", self.type_check),
        ]

        all_passed = True

        for check_name, check_func in checks:
            print(f"\n--- {check_name} ---")
            if not check_func():
                all_passed = False

        if all_passed:
            print("\n✅ All quality checks passed!")
        else:
            print("\n❌ Some quality checks failed!")

        return all_passed

    def fix_code_style(self) -> bool:
        """
        Fix code style issues automatically.

        Returns:
            True if successful, False otherwise
        """
        print("Fixing code style issues...")

        success = True

        # Format code
        if not self.format_code():
            success = False

        # Sort imports
        if not self.sort_imports():
            success = False

        if success:
            print("✅ Code style fixed!")
        else:
            print("❌ Some issues could not be fixed automatically!")

        return success

    def clean_project(self) -> None:
        """Clean project artifacts."""
        print("Cleaning project artifacts...")

        patterns_to_remove = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
            ".pytest_cache",
            ".coverage",
            "htmlcov",
            "build",
            "dist",
            "*.egg-info",
        ]

        import glob
        import shutil

        for pattern in patterns_to_remove:
            for path in glob.glob(str(self.project_root / pattern), recursive=True):
                path_obj = Path(path)
                try:
                    if path_obj.is_dir():
                        shutil.rmtree(path_obj)
                        print(f"  Removed directory: {path_obj}")
                    else:
                        path_obj.unlink()
                        print(f"  Removed file: {path_obj}")
                except Exception as e:
                    print(f"  Failed to remove {path_obj}: {e}")

        print("Project cleaned!")

    def install_dev_dependencies(self) -> bool:
        """Install development dependencies."""
        print("Installing development dependencies...")

        requirements_files = ["requirements.txt", "requirements-dev.txt"]

        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip",
                            "install", "-r", str(req_path)],
                        check=True,
                    )
                    print(f"Installed dependencies from {req_file}")
                except subprocess.CalledProcessError:
                    print(f"Failed to install dependencies from {req_file}")
                    return False

        print("Development dependencies installed!")
        return True


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="HEAL development utilities")
    parser.add_argument(
        "command",
        choices=[
            "test",
            "format",
            "sort-imports",
            "lint",
            "type-check",
            "quality-check",
            "fix-style",
            "clean",
            "install-deps",
        ],
        help="Command to run",
    )
    parser.add_argument("--verbose", "-v",
                        action="store_true", help="Verbose output")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report (for test command)",
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Check only, don't make changes"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    dev_utils = DevUtils(project_root)

    success = True

    if args.command == "test":
        success = dev_utils.run_tests(
            verbose=args.verbose, coverage=args.coverage)
    elif args.command == "format":
        success = dev_utils.format_code(check_only=args.check_only)
    elif args.command == "sort-imports":
        success = dev_utils.sort_imports(check_only=args.check_only)
    elif args.command == "lint":
        success = dev_utils.lint_code()
    elif args.command == "type-check":
        success = dev_utils.type_check()
    elif args.command == "quality-check":
        success = dev_utils.run_quality_checks()
    elif args.command == "fix-style":
        success = dev_utils.fix_code_style()
    elif args.command == "clean":
        dev_utils.clean_project()
    elif args.command == "install-deps":
        success = dev_utils.install_dev_dependencies()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
