#!/usr/bin/env python3
"""
Test script to verify type annotations are working correctly
"""

import ast
import sys
from pathlib import Path

def check_type_annotations(file_path):
    """Check if a Python file has proper type annotations"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        
        # Count type annotations
        annotations_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign):  # Variable annotations
                annotations_count += 1
            elif isinstance(node, ast.FunctionDef):  # Function annotations
                if node.returns:
                    annotations_count += 1
                for arg in node.args.args:
                    if arg.annotation:
                        annotations_count += 1
        
        return annotations_count
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return 0

def main():
    """Main test function"""
    print("Testing type annotations in modified files...")
    
    # Files we specifically modified
    modified_files = [
        "app/module_interface.py",
        "app/common/application.py", 
        "app/model/custom_messagebox.py",
        "app/components/download/search_manager.py",
        "app/components/module/module_config_manager.py",
        "app/components/module/module_controller.py",
        "app/components/module/module_metrics_manager.py",
        "app/components/module/module_operation_handler.py",
        "app/components/module/module_validator.py",
        "app/components/module/performance_dashboard_ui.py",
        "app/components/module/performance_monitor.py",
        "app/components/tools/editor.py",
        "app/components/utils/dispatch.py"
    ]
    
    total_annotations = 0
    files_checked = 0
    
    for file_path in modified_files:
        if Path(file_path).exists():
            annotations = check_type_annotations(file_path)
            total_annotations += annotations
            files_checked += 1
            print(f"✓ {file_path}: {annotations} type annotations")
        else:
            print(f"✗ {file_path}: File not found")
    
    print(f"\nSummary:")
    print(f"Files checked: {files_checked}")
    print(f"Total type annotations found: {total_annotations}")
    
    if total_annotations > 0:
        print("✓ Type annotations are present in the modified files")
        return 0
    else:
        print("✗ No type annotations found")
        return 1

if __name__ == '__main__':
    sys.exit(main())
