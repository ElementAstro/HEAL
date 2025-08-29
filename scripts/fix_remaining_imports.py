#!/usr/bin/env python3
"""
Batch Import Fixer
Systematically converts remaining absolute imports to relative imports
across all component packages.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict


def calculate_relative_import(source_file: Path, target_module: str) -> str:
    """Calculate the correct relative import path"""
    # Convert src.heal.x.y.z to path components
    target_parts = target_module.replace('src.heal.', '').split('.')
    
    # Get source file's package path
    source_parts = source_file.relative_to(Path('src/heal')).parts[:-1]  # Exclude filename
    
    # Calculate relative path
    if not source_parts:
        # Source is in src/heal root
        return f"from .{'.'.join(target_parts)}"
    
    # Find common prefix
    common_length = 0
    for i, (s, t) in enumerate(zip(source_parts, target_parts)):
        if s == t:
            common_length = i + 1
        else:
            break
    
    # Calculate dots needed to go up
    dots_needed = len(source_parts) - common_length
    
    # Build relative import
    if dots_needed == 0:
        # Same package
        remaining_parts = target_parts[common_length:]
        if remaining_parts:
            return f"from .{'.'.join(remaining_parts)}"
        else:
            return "from ."
    else:
        # Different package
        dots = "." * (dots_needed + 1)
        remaining_parts = target_parts[common_length:]
        if remaining_parts:
            return f"from {dots}{'.'.join(remaining_parts)}"
        else:
            return f"from {dots[:-1]}"


def fix_imports_in_file(file_path: Path) -> List[str]:
    """Fix imports in a single file"""
    changes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
            # Match "from src.heal.xxx import yyy" patterns
            match = re.match(r'^(\s*)from (src\.heal\.[^\s]+) import (.+)$', line)
            if match:
                indent, old_module, imports = match.groups()
                
                # Calculate new relative import
                try:
                    new_import_base = calculate_relative_import(file_path, old_module)
                    new_line = f"{indent}{new_import_base} import {imports}"
                    
                    if new_line != line:
                        lines[i] = new_line
                        modified = True
                        changes.append(f"Line {i+1}: {line.strip()} -> {new_line.strip()}")
                        
                except Exception as e:
                    print(f"Error calculating relative import for {old_module} in {file_path}: {e}")
        
        # Write back if modified
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
    
    return changes


def main() -> None:
    """Main function to fix all remaining imports"""
    print("Starting batch import fixing...")
    
    # Find all Python files in src/heal
    python_files = []
    for root, dirs, files in os.walk('src/heal'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    print(f"Found {len(python_files)} Python files to process")
    
    total_changes = 0
    files_modified = 0
    
    for file_path in python_files:
        changes = fix_imports_in_file(file_path)
        if changes:
            files_modified += 1
            total_changes += len(changes)
            print(f"\nFixed {len(changes)} imports in {file_path}:")
            for change in changes[:5]:  # Show first 5 changes
                print(f"  {change}")
            if len(changes) > 5:
                print(f"  ... and {len(changes) - 5} more")
    
    print(f"\n=== BATCH IMPORT FIXING COMPLETE ===")
    print(f"Files processed: {len(python_files)}")
    print(f"Files modified: {files_modified}")
    print(f"Total imports fixed: {total_changes}")
    
    # Verify no remaining absolute imports
    remaining_issues = []
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'from src.heal.' in line and not line.strip().startswith('#'):
                    remaining_issues.append(f"{file_path}:{i} - {line.strip()}")
        except Exception:
            pass
    
    if remaining_issues:
        print(f"\nWARNING: {len(remaining_issues)} imports still need manual review:")
        for issue in remaining_issues[:10]:
            print(f"  {issue}")
        if len(remaining_issues) > 10:
            print(f"  ... and {len(remaining_issues) - 10} more")
    else:
        print("\n✅ All absolute imports successfully converted to relative imports!")


if __name__ == "__main__":
    main()
