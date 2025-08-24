#!/usr/bin/env python3
"""
Final mypy check script
"""

import subprocess
import sys
from pathlib import Path

def run_mypy_check():
    """Run mypy on all Python files"""
    # Find all Python files
    python_files = []
    
    # Add main.py
    if Path('main.py').exists():
        python_files.append('main.py')
    
    # Add files from app directory
    app_dir = Path('app')
    if app_dir.exists():
        for py_file in app_dir.rglob('*.py'):
            # Skip files that cause module name conflicts
            file_path = str(py_file).replace('\\', '/')
            if ('app/components/main/' not in file_path and
                'app/components/setting/' not in file_path and
                file_path != 'app/components/utils/scaffold.py'):
                python_files.append(str(py_file))
    
    print(f"Running mypy on {len(python_files)} Python files...")
    
    # Run mypy on all files
    try:
        result = subprocess.run([
            'mypy'
        ] + python_files + [
            '--ignore-missing-imports',
            '--follow-imports=skip',
            '--no-strict-optional'
        ], capture_output=True, text=True, timeout=300)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("SUCCESS: All mypy checks passed!")
        else:
            print("FAILED: Some mypy errors remain")
            
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("ERROR: mypy check timed out")
        return -1
    except Exception as e:
        print(f"ERROR: {e}")
        return -1

if __name__ == '__main__':
    sys.exit(run_mypy_check())
