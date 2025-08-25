#!/usr/bin/env python3
"""
Development environment setup script for HEAL.
Sets up the development environment with all necessary dependencies and tools.
"""

import os
import subprocess
import sys
import venv
from pathlib import Path
from typing import List, Optional


class DevEnvironmentSetup:
    """Setup development environment for HEAL."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.venv_dir = project_root / ".venv"

    def create_virtual_environment(self) -> None:
        """Create a virtual environment."""
        print("Creating virtual environment...")

        if self.venv_dir.exists():
            print(f"Virtual environment already exists at {self.venv_dir}")
            return

        venv.create(self.venv_dir, with_pip=True)
        print(f"Virtual environment created at {self.venv_dir}")

    def get_pip_executable(self) -> Path:
        """Get the pip executable path for the virtual environment."""
        if sys.platform == "win32":
            pip_path = self.venv_dir / "Scripts" / "pip.exe"
            if not pip_path.exists():
                # Try without .exe extension
                pip_path = self.venv_dir / "Scripts" / "pip"
            if not pip_path.exists():
                # Use system pip as fallback
                return Path(sys.executable).parent / "pip.exe"
            return pip_path
        else:
            return self.venv_dir / "bin" / "pip"

    def get_python_executable(self) -> Path:
        """Get the Python executable path for the virtual environment."""
        if sys.platform == "win32":
            python_path = self.venv_dir / "Scripts" / "python.exe"
            if not python_path.exists():
                # Use current Python as fallback
                return Path(sys.executable)
            return python_path
        else:
            return self.venv_dir / "bin" / "python"

    def install_dependencies(self) -> None:
        """Install development dependencies."""
        print("Installing development dependencies...")

        pip_exe = self.get_pip_executable()

        # Upgrade pip first
        subprocess.run([str(pip_exe), "install", "--upgrade", "pip"], check=True)

        # Install development requirements
        requirements_files = ["requirements.txt", "requirements-dev.txt"]

        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                print(f"Installing from {req_file}...")
                subprocess.run(
                    [str(pip_exe), "install", "-r", str(req_path)], check=True
                )

        # Install the package in development mode
        subprocess.run(
            [str(pip_exe), "install", "-e", "."], check=True, cwd=self.project_root
        )

        print("Dependencies installed successfully")

    def setup_pre_commit_hooks(self) -> None:
        """Setup pre-commit hooks for code quality."""
        print("Setting up pre-commit hooks...")

        pip_exe = self.get_pip_executable()

        try:
            # Install pre-commit
            subprocess.run([str(pip_exe), "install", "pre-commit"], check=True)

            # Create pre-commit config if it doesn't exist
            pre_commit_config = self.project_root / ".pre-commit-config.yaml"
            if not pre_commit_config.exists():
                config_content = """
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
"""
                with open(pre_commit_config, "w") as f:
                    f.write(config_content.strip())

            # Install the hooks
            python_exe = self.get_python_executable()
            subprocess.run(
                [str(python_exe), "-m", "pre_commit", "install"],
                check=True,
                cwd=self.project_root,
            )

            print("Pre-commit hooks installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to setup pre-commit hooks: {e}")

    def create_vscode_settings(self) -> None:
        """Create VS Code settings for the project."""
        print("Creating VS Code settings...")

        vscode_dir = self.project_root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)

        # Settings
        settings_file = vscode_dir / "settings.json"
        if not settings_file.exists():
            settings = {
                "python.defaultInterpreterPath": str(self.get_python_executable()),
                "python.linting.enabled": True,
                "python.linting.pylintEnabled": False,
                "python.linting.flake8Enabled": True,
                "python.formatting.provider": "black",
                "python.sortImports.args": ["--profile", "black"],
                "editor.formatOnSave": True,
                "editor.codeActionsOnSave": {"source.organizeImports": True},
                "files.exclude": {
                    "**/__pycache__": True,
                    "**/*.pyc": True,
                    ".venv": True,
                    "build": True,
                    "dist": True,
                },
            }

            import json

            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=2)

        # Launch configuration
        launch_file = vscode_dir / "launch.json"
        if not launch_file.exists():
            launch_config = {
                "version": "0.2.0",
                "configurations": [
                    {
                        "name": "HEAL Application",
                        "type": "python",
                        "request": "launch",
                        "program": "${workspaceFolder}/main.py",
                        "console": "integratedTerminal",
                        "cwd": "${workspaceFolder}",
                        "env": {"PYTHONPATH": "${workspaceFolder}/src"},
                    },
                    {
                        "name": "Run Tests",
                        "type": "python",
                        "request": "launch",
                        "module": "pytest",
                        "args": ["tests/", "-v"],
                        "console": "integratedTerminal",
                        "cwd": "${workspaceFolder}",
                    },
                ],
            }

            import json

            with open(launch_file, "w") as f:
                json.dump(launch_config, f, indent=2)

        print("VS Code settings created")

    def setup(self) -> None:
        """Complete development environment setup."""
        print("Setting up HEAL development environment...")

        self.create_virtual_environment()
        self.install_dependencies()
        self.setup_pre_commit_hooks()
        self.create_vscode_settings()

        print("\nDevelopment environment setup complete!")
        print(f"To activate the virtual environment:")
        if sys.platform == "win32":
            print(f"  {self.venv_dir}\\Scripts\\activate")
        else:
            print(f"  source {self.venv_dir}/bin/activate")
        print("\nTo run the application:")
        print("  python main.py")
        print("\nTo run tests:")
        print("  pytest tests/")


def main() -> None:
    """Main function."""
    project_root = Path(__file__).parent.parent
    setup = DevEnvironmentSetup(project_root)
    setup.setup()


if __name__ == "__main__":
    main()
