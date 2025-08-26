# HEAL Troubleshooting Guide

This guide provides solutions to common issues encountered when developing, building, or running HEAL across different platforms.

## Quick Diagnostics

### System Information

```bash
# Get system information
python scripts/build.py --verbose

# Check Python environment
python --version
python -m pip list

# Verify HEAL installation
python main.py --version
python main.py --check-deps
```

### Log Analysis

```bash
# Enable debug logging
python main.py --debug --log-level DEBUG

# Check build logs
cat logs/heal-build.log
cat logs/heal-build-errors.log

# View JSON structured logs
python -m json.tool logs/heal-build.json
```

## Development Issues

### Environment Setup Problems

#### Issue: Python Version Conflicts

**Symptoms**: Import errors, syntax errors, or feature not available
**Solution**:

```bash
# Check Python version
python --version  # Should be 3.11+

# Use specific Python version
python3.11 -m venv venv
# or
py -3.11 -m venv venv  # Windows with Python Launcher
```

#### Issue: Virtual Environment Not Working

**Symptoms**: Packages not found, wrong Python version
**Solution**:

```bash
# Recreate virtual environment
rm -rf venv  # or rmdir /s venv on Windows
python -m venv venv

# Activate properly
source venv/bin/activate  # Unix
venv\Scripts\activate.bat  # Windows CMD
venv\Scripts\Activate.ps1  # Windows PowerShell

# Verify activation
which python  # Unix
where python  # Windows
```

#### Issue: Dependency Installation Failures

**Symptoms**: pip install errors, compilation failures
**Solution**:

```bash
# Update pip and setuptools
python -m pip install --upgrade pip setuptools wheel

# Install with verbose output
pip install -r requirements.txt -v

# Platform-specific solutions:
# Windows: Install Visual Studio Build Tools
# macOS: xcode-select --install
# Linux: sudo apt install build-essential python3-dev
```

### Import and Module Issues

#### Issue: ModuleNotFoundError

**Symptoms**: Cannot import HEAL modules or dependencies
**Solution**:

```bash
# Check PYTHONPATH
echo $PYTHONPATH  # Unix
echo %PYTHONPATH%  # Windows

# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Unix
set PYTHONPATH=%PYTHONPATH%;%CD%  # Windows

# Or run with proper path
python -m src.heal.main
```

#### Issue: Circular Import Errors

**Symptoms**: ImportError during startup
**Solution**:

1. Check import order in affected modules
2. Use lazy imports where possible
3. Restructure code to avoid circular dependencies

### GUI Development Issues

#### Issue: Qt/PySide6 Not Working

**Symptoms**: GUI doesn't start, Qt errors
**Solution**:

```bash
# Reinstall PySide6
pip uninstall PySide6
pip install PySide6==6.4.2

# Check Qt installation
python -c "from PySide6.QtWidgets import QApplication; print('Qt OK')"

# Platform-specific fixes:
# Linux: sudo apt install libxcb-xinerama0 libxcb-cursor0
# macOS: No additional packages needed
# Windows: Install Visual C++ Redistributable
```

#### Issue: High DPI Display Problems

**Symptoms**: Blurry interface, wrong scaling
**Solution**:

```python
# Add to main.py before QApplication creation
import os
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
os.environ['QT_SCALE_FACTOR'] = '1'

# Or set in application
app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
```

## Build Issues

### PyInstaller Problems

#### Issue: Build Fails with Import Errors

**Symptoms**: PyInstaller can't find modules
**Solution**:

```bash
# Clear PyInstaller cache
python -m PyInstaller --clean heal.spec

# Add missing imports to spec file
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'qfluentwidgets',
    # Add other missing modules
]

# Use hook files for complex packages
# Create pyi_hooks/hook-mypackage.py
```

#### Issue: Resources Not Found in Executable

**Symptoms**: FileNotFoundError for images, configs
**Solution**:

```python
# Use proper resource path detection
import sys
from pathlib import Path

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle
        return Path(sys._MEIPASS) / relative_path
    else:
        # Development
        return Path(__file__).parent / relative_path

# Update spec file data section
datas = [
    ('src/heal/resources', 'src/heal/resources'),
    ('config', 'config'),
]
```

#### Issue: Executable Too Large

**Symptoms**: Multi-GB executable files
**Solution**:

```bash
# Use onedir instead of onefile
# In spec file: onefile=False

# Exclude unnecessary modules
excludes = [
    'tkinter',
    'matplotlib.backends._backend_tk',
    'PIL.ImageTk',
    'unittest',
    'test',
]

# Use UPX compression (Windows/Linux)
upx=True  # In spec file
```

### Nuitka Build Issues

#### Issue: Nuitka Compilation Errors

**Symptoms**: C++ compilation failures
**Solution**:

```bash
# Install proper C++ compiler
# Windows: Visual Studio Build Tools
# macOS: Xcode Command Line Tools
# Linux: build-essential

# Use specific Nuitka options
python -m nuitka \
    --standalone \
    --enable-plugin=pyside6 \
    --assume-yes-for-downloads \
    main.py
```

### Cross-Platform Build Issues

#### Issue: Different Behavior Across Platforms

**Symptoms**: Works on one platform, fails on others
**Solution**:

1. Use platform-specific spec files
2. Test on all target platforms
3. Use conditional imports and code paths
4. Check file path separators and case sensitivity

## Runtime Issues

### Application Startup Problems

#### Issue: Application Won't Start

**Symptoms**: No window appears, immediate exit
**Solution**:

```bash
# Run with debug output
python main.py --debug

# Check for missing dependencies
python -c "import sys; print(sys.path)"
python -c "from src.heal import main"

# Verify Qt display
export QT_DEBUG_PLUGINS=1  # Unix
set QT_DEBUG_PLUGINS=1     # Windows
```

#### Issue: Slow Startup

**Symptoms**: Long delay before window appears
**Solution**:

1. Profile startup with `python -m cProfile main.py`
2. Lazy load heavy modules
3. Cache expensive operations
4. Optimize import statements

### GUI Runtime Issues

#### Issue: Interface Freezing

**Symptoms**: Unresponsive GUI, spinning cursor
**Solution**:

```python
# Use QThread for long operations
from PySide6.QtCore import QThread, Signal

class WorkerThread(QThread):
    finished = Signal(object)
    
    def run(self):
        result = self.long_running_operation()
        self.finished.emit(result)

# Process events during loops
from PySide6.QtWidgets import QApplication

for item in large_list:
    process_item(item)
    QApplication.processEvents()  # Keep GUI responsive
```

#### Issue: Memory Leaks

**Symptoms**: Increasing memory usage over time
**Solution**:

1. Use memory profiler: `python -m memory_profiler main.py`
2. Check for circular references
3. Properly delete Qt objects
4. Use weak references where appropriate

### File and Permission Issues

#### Issue: Permission Denied Errors

**Symptoms**: Cannot read/write files or directories
**Solution**:

```bash
# Check file permissions
ls -la file.txt  # Unix
icacls file.txt  # Windows

# Fix permissions
chmod 644 file.txt  # Unix
icacls file.txt /grant Users:F  # Windows

# Run with elevated privileges if needed
sudo python main.py  # Unix (not recommended)
# Right-click "Run as Administrator" on Windows
```

#### Issue: Configuration Not Persisting

**Symptoms**: Settings reset on restart
**Solution**:

1. Check config directory permissions
2. Verify config file format (JSON syntax)
3. Handle write failures gracefully
4. Use atomic writes for config updates

## Platform-Specific Issues

### Windows Issues

#### Issue: Antivirus False Positives

**Symptoms**: Executable deleted or quarantined
**Solution**:

1. Add exclusion to antivirus software
2. Sign executable with code signing certificate
3. Submit false positive report to antivirus vendor
4. Use installer instead of portable executable

#### Issue: DLL Loading Errors

**Symptoms**: ImportError for native modules
**Solution**:

```bash
# Install Visual C++ Redistributable
# Download from Microsoft website

# Check DLL dependencies
# Use Dependency Walker or similar tool

# Bundle DLLs with application
# Add to PyInstaller binaries section
```

### macOS Issues

#### Issue: Gatekeeper Blocking App

**Symptoms**: "App can't be opened" dialog
**Solution**:

1. Right-click and select "Open"
2. Go to System Preferences > Security & Privacy
3. Click "Open Anyway" for the blocked app
4. For distribution: Sign and notarize the app

#### Issue: App Not Appearing in Applications

**Symptoms**: .app bundle not recognized
**Solution**:

1. Ensure proper .app bundle structure
2. Include Info.plist with correct metadata
3. Set executable permissions on main binary
4. Use proper file associations

### Linux Issues

#### Issue: Missing System Libraries

**Symptoms**: ImportError for system dependencies
**Solution**:

```bash
# Install common dependencies
sudo apt install libxcb-xinerama0 libxcb-cursor0 libgl1-mesa-glx

# Check library dependencies
ldd executable_name

# Use AppImage for better compatibility
# Or provide distribution-specific packages
```

#### Issue: Desktop Integration Not Working

**Symptoms**: No application menu entry, wrong icon
**Solution**:

```bash
# Install desktop file
cp heal.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/

# Install icon
cp icon.png ~/.local/share/icons/hicolor/256x256/apps/heal.png
gtk-update-icon-cache ~/.local/share/icons/hicolor/
```

## Performance Issues

### Memory Usage

#### Issue: High Memory Consumption

**Symptoms**: System slowdown, out of memory errors
**Solution**:

1. Profile with `memory_profiler`
2. Use generators instead of lists for large datasets
3. Implement proper cleanup in destructors
4. Consider using memory-mapped files for large data

### CPU Usage

#### Issue: High CPU Usage

**Symptoms**: Fan noise, system slowdown
**Solution**:

1. Profile with `cProfile`
2. Optimize hot code paths
3. Use threading for I/O operations
4. Implement proper sleep/wait mechanisms

## Getting Help

### Information to Provide

When reporting issues, include:

1. **System Information**:

   ```bash
   python scripts/build.py --verbose
   ```

2. **Error Messages**: Full traceback and error output

3. **Steps to Reproduce**: Minimal example that triggers the issue

4. **Environment Details**:
   - Operating system and version
   - Python version
   - Virtual environment status
   - Installed package versions

5. **Log Files**: Relevant log entries from `logs/` directory

### Support Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and help
- **Discord**: Real-time community support
- **Email**: Direct contact for sensitive issues

### Self-Help Resources

- Check existing GitHub issues for similar problems
- Search the documentation for relevant information
- Review the changelog for recent changes
- Test with a clean virtual environment
- Try the latest development version

This troubleshooting guide covers the most common issues. For specific problems not covered here, please create a GitHub issue with detailed information about your environment and the problem you're experiencing.
