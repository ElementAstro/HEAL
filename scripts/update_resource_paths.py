#!/usr/bin/env python3
"""
Script to find and update hardcoded resource paths to use the new resource management system.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


class ResourcePathUpdater:
    """Updates hardcoded resource paths to use the new resource management system."""

    def __init__(self) -> None:
        self.patterns = {
            # QSS/Style paths
            r'["\']\.?/?src[/\\]qss[/\\]([^"\']+)["\']': r'resource_manager.load_stylesheet("\1")',
            r'["\']\.?/?src[/\\]heal[/\\]resources[/\\]styles[/\\]([^"\']+)["\']': r'resource_manager.load_stylesheet("\1")',
            # Image paths
            r'["\']\.?/?src[/\\]image[/\\]([^"\']+)["\']': r'str(resource_manager.get_resource_path("images", "\1"))',
            r'["\']\.?/?src[/\\]heal[/\\]resources[/\\]images[/\\]([^"\']+)["\']': r'str(resource_manager.get_resource_path("images", "\1"))',
            # Icon paths
            r'["\']\.?/?src[/\\]icon[/\\]([^"\']+)["\']': r'str(resource_manager.get_resource_path("icons", "\1"))',
            r'["\']\.?/?icons[/\\]([^"\']+)["\']': r'str(resource_manager.get_resource_path("app_icons", "\1"))',
            # Translation paths
            r'["\']\.?/?src[/\\]translate[/\\]([^"\']+)["\']': r'str(resource_manager.get_resource_path("translations", "\1"))',
            r'["\']\.?/?src[/\\]heal[/\\]resources[/\\]translations[/\\]([^"\']+)["\']': r'str(resource_manager.get_resource_path("translations", "\1"))',
            # Data paths
            r'["\']\.?/?src[/\\]data[/\\]([^"\']+)["\']': r'str(resource_manager.get_resource_path("data", "\1"))',
            r'["\']\.?/?src[/\\]heal[/\\]resources[/\\]data[/\\]([^"\']+)["\']': r'str(resource_manager.get_resource_path("data", "\1"))',
        }

        self.import_patterns = [
            # Check if resource_manager is already imported
            r"from\s+.*resources.*import.*resource_manager",
            r"from\s+src\.heal\.resources.*import.*resource_manager",
            r"import.*resource_manager",
        ]

    def needs_resource_manager_import(self, content: str) -> bool:
        """Check if the file needs resource_manager import."""
        # Check if resource_manager is used but not imported
        if "resource_manager" in content:
            for pattern in self.import_patterns:
                if re.search(pattern, content):
                    return False
            return True
        return False

    def add_resource_manager_import(self, content: str) -> str:
        """Add resource_manager import to the file."""
        # Find the best place to add the import
        lines = content.split("\n")

        # Look for existing imports from the same package
        heal_import_line = -1
        last_import_line = -1

        for i, line in enumerate(lines):
            if re.match(r"^\s*from\s+\.\..*import", line) or re.match(
                r"^\s*from\s+src\.heal", line
            ):
                heal_import_line = i
            elif re.match(r"^\s*(from|import)\s+", line):
                last_import_line = i

        # Determine where to insert the import
        if heal_import_line >= 0:
            # Add after existing heal imports
            insert_line = heal_import_line + 1
            import_statement = "from ..resources import resource_manager"
        elif last_import_line >= 0:
            # Add after last import
            insert_line = last_import_line + 1
            import_statement = "from src.heal.resources import resource_manager"
        else:
            # Add at the beginning after docstring
            insert_line = 0
            if lines and lines[0].strip().startswith('"""'):
                # Find end of docstring
                for i in range(1, len(lines)):
                    if '"""' in lines[i]:
                        insert_line = i + 1
                        break
            import_statement = "from src.heal.resources import resource_manager"

        # Insert the import
        lines.insert(insert_line, import_statement)
        return "\n".join(lines)

    def update_file(self, file_path: Path) -> bool:
        """Update resource paths in a single file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content
            updated = False

            # Apply path replacements
            for pattern, replacement in self.patterns.items():
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    updated = True

            # Add import if needed
            if updated and self.needs_resource_manager_import(content):
                content = self.add_resource_manager_import(content)

            # Write back if changed
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return True

            return False

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False

    def find_python_files(self, directory: Path) -> List[Path]:
        """Find all Python files in the directory."""
        python_files = []
        for root, dirs, files in os.walk(directory):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != "__pycache__"]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        return python_files

    def scan_for_hardcoded_paths(self, directory: Path) -> Dict[str, List[str]]:
        """Scan for hardcoded resource paths and report them."""
        results = {}
        python_files = self.find_python_files(directory)

        scan_patterns = [
            r'["\'][^"\']*src[/\\]qss[/\\][^"\']*["\']',
            r'["\'][^"\']*src[/\\]image[/\\][^"\']*["\']',
            r'["\'][^"\']*src[/\\]icon[/\\][^"\']*["\']',
            r'["\'][^"\']*src[/\\]translate[/\\][^"\']*["\']',
            r'["\'][^"\']*src[/\\]data[/\\][^"\']*["\']',
            r'["\'][^"\']*icons[/\\][^"\']*["\']',
        ]

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                file_matches = []
                for pattern in scan_patterns:
                    matches = re.findall(pattern, content)
                    file_matches.extend(matches)

                if file_matches:
                    results[str(file_path)] = file_matches

            except Exception as e:
                print(f"Error scanning {file_path}: {e}")

        return results

    def update_all_files(self, directories: List[Path]) -> None:
        """Update all Python files in the given directories."""
        total_updated = 0

        for directory in directories:
            if not directory.exists():
                print(f"Directory not found: {directory}")
                continue

            print(f"Processing directory: {directory}")
            python_files = self.find_python_files(directory)

            for file_path in python_files:
                if self.update_file(file_path):
                    print(f"  Updated: {file_path}")
                    total_updated += 1

        print(f"\nTotal files updated: {total_updated}")


def main() -> None:
    """Main function."""
    project_root = Path(__file__).parent.parent
    updater = ResourcePathUpdater()

    # Directories to process
    directories = [
        project_root / "src" / "heal",
        project_root / "tests",
    ]

    print("Scanning for hardcoded resource paths...")
    for directory in directories:
        if directory.exists():
            hardcoded_paths = updater.scan_for_hardcoded_paths(directory)
            if hardcoded_paths:
                print(f"\nFound hardcoded paths in {directory}:")
                for file_path, paths in hardcoded_paths.items():
                    print(f"  {file_path}:")
                    for path in paths:
                        print(f"    {path}")

    print("\nUpdating resource paths...")
    updater.update_all_files(directories)


if __name__ == "__main__":
    main()
