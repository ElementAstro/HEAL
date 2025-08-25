#!/usr/bin/env python3
"""
Enhanced script to update import statements for the new package structure.
This script will systematically update all Python files to use the new src/heal package structure.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


class ImportAnalyzer:
    """Analyze and update import statements in Python files."""

    def __init__(self) -> None:
        self.import_mappings = {
            # Old app imports to new structure
            "app.common": "src.heal.common",
            "app.model": "src.heal.models",
            "app.components": "src.heal.components",
            "app.interfaces": "src.heal.interfaces",
        }

        self.resource_path_mappings = {
            # Resource path updates
            r"src[/\\]translate[/\\]": "src/heal/resources/translations/",
            r"src[/\\]qss[/\\]": "src/heal/resources/styles/",
            r"src[/\\]image[/\\]": "src/heal/resources/images/",
            r"src[/\\]icon[/\\]": "src/heal/resources/icons/",
            r"src[/\\]data[/\\]": "src/heal/resources/data/",
            r"src[/\\]audio[/\\]": "src/heal/resources/audio/",
            r"src[/\\]patch[/\\]": "src/heal/resources/patches/",
            r"src[/\\]warp[/\\]": "src/heal/resources/warp/",
        }

    def get_relative_import_level(self, file_path: Path, target_module: str) -> str:
        """Determine the correct relative import for a file."""
        file_parts = file_path.relative_to(Path("src/heal")).parts[
            :-1
        ]  # Remove filename

        # Determine relative path based on file location
        if "interfaces" in file_parts:
            if target_module.startswith("src.heal.common"):
                return target_module.replace("src.heal.common", "..common")
            elif target_module.startswith("src.heal.models"):
                return target_module.replace("src.heal.models", "..models")
            elif target_module.startswith("src.heal.components"):
                return target_module.replace("src.heal.components", "..components")
        elif "components" in file_parts:
            if target_module.startswith("src.heal.common"):
                return target_module.replace("src.heal.common", "..common")
            elif target_module.startswith("src.heal.models"):
                return target_module.replace("src.heal.models", "..models")
            elif target_module.startswith("src.heal.interfaces"):
                return target_module.replace("src.heal.interfaces", "..interfaces")
        elif "models" in file_parts:
            if target_module.startswith("src.heal.common"):
                return target_module.replace("src.heal.common", "..common")
            elif target_module.startswith("src.heal.components"):
                return target_module.replace("src.heal.components", "..components")
        elif "common" in file_parts:
            # Common modules typically don't import from other packages
            pass

        return target_module


def update_imports_in_file(file_path: Path) -> bool:
    """Update import statements in a single file using AST analysis."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        analyzer = ImportAnalyzer()

        # Update basic app imports to src.heal
        for old_import, new_import in analyzer.import_mappings.items():
            content = re.sub(
                rf"\bfrom {re.escape(old_import)}\.", f"from {new_import}.", content
            )
            content = re.sub(
                rf"\bimport {re.escape(old_import)}\.", f"import {new_import}.", content
            )
            content = re.sub(
                rf"\bfrom {re.escape(old_import)}\b", f"from {new_import}", content
            )

        # Update resource paths in strings
        for old_path, new_path in analyzer.resource_path_mappings.items():
            content = re.sub(old_path, new_path, content)

        # Convert to relative imports if file is within src/heal
        if "src/heal" in str(file_path) or "src\\heal" in str(file_path):
            # Convert absolute src.heal imports to relative imports
            content = re.sub(r"\bfrom src\.heal\.", "from .", content)
            content = re.sub(r"\bimport src\.heal\.", "import .", content)

            # Fix relative import levels based on file location
            file_location = str(file_path).replace("\\", "/")

            if "/interfaces/" in file_location:
                content = re.sub(r"\bfrom \.common\.", "from ..common.", content)
                content = re.sub(r"\bfrom \.models\.", "from ..models.", content)
                content = re.sub(
                    r"\bfrom \.components\.", "from ..components.", content
                )
            elif "/components/" in file_location:
                content = re.sub(r"\bfrom \.common\.", "from ..common.", content)
                content = re.sub(r"\bfrom \.models\.", "from ..models.", content)
                content = re.sub(
                    r"\bfrom \.interfaces\.", "from ..interfaces.", content
                )
            elif "/models/" in file_location:
                content = re.sub(r"\bfrom \.common\.", "from ..common.", content)
                content = re.sub(
                    r"\bfrom \.components\.", "from ..components.", content
                )

        # Write back if changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in the directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    return python_files


def main() -> None:
    """Main function to update all imports."""
    project_root = Path(__file__).parent.parent

    # Directories to process
    directories_to_process = [
        project_root / "src" / "heal",
        project_root / "tests",
        project_root / "tools",
        project_root / "scripts",
    ]

    # Also process main.py
    main_files = [project_root / "main.py"]

    total_updated = 0

    # Process directories
    for directory in directories_to_process:
        if directory.exists():
            print(f"Processing directory: {directory}")
            python_files = find_python_files(directory)

            for file_path in python_files:
                if update_imports_in_file(file_path):
                    print(f"  Updated: {file_path}")
                    total_updated += 1

    # Process individual files
    for file_path in main_files:
        if file_path.exists():
            if update_imports_in_file(file_path):
                print(f"Updated: {file_path}")
                total_updated += 1

    print(f"\nTotal files updated: {total_updated}")


if __name__ == "__main__":
    main()
