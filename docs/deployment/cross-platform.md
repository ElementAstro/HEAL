# Cross-Platform Development Guide

This comprehensive guide covers cross-platform development, building, and deployment for the HEAL project across Windows, macOS, and Linux.

## Overview

HEAL is designed to run seamlessly across multiple platforms with a unified codebase and consistent user experience. This guide provides developers and users with the knowledge needed to work with HEAL on any supported platform.

## Supported Platforms

### Primary Platforms

- **Windows 10/11** (x64)
- **macOS 10.14+** (x64, Apple Silicon)
- **Ubuntu 20.04+** (x64)

### Additional Linux Distributions

- **Debian 11+**
- **CentOS 8+** / **RHEL 8+**
- **Fedora 35+**
- **Arch Linux** (current)
- **openSUSE Leap 15.4+**

## Development Environment Setup

### Prerequisites

#### All Platforms

- **Python 3.11+** (recommended 3.11 or 3.12)
- **Git** for version control
- **Modern terminal** (PowerShell 7+ on Windows, Terminal.app on macOS, any on Linux)

#### Windows Specific

```powershell
# Install Python from python.org or Microsoft Store
# Install Git from git-scm.com
# Optional: Windows Terminal from Microsoft Store
# Optional: Visual Studio Code with Python extension

# Install build tools (optional, for native extensions)
# Visual Studio Build Tools or Visual Studio Community
```

#### macOS Specific

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
brew install python@3.11 git

# Install Xcode Command Line Tools
xcode-select --install

# Optional: Install additional tools
brew install create-dmg  # For DMG creation
```

#### Linux Specific

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip git build-essential

# CentOS/RHEL/Fedora
sudo dnf install python3.11 python3-pip git gcc gcc-c++ make

# Arch Linux
sudo pacman -S python python-pip git base-devel

# Additional GUI dependencies for development
sudo apt install libgl1-mesa-glx libxkbcommon-x11-0 libxcb-*  # Ubuntu/Debian
```

### Project Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/ElementAstro/HEAL.git
   cd HEAL
   ```

2. **Create Virtual Environment**

   ```bash
   # All platforms
   python -m venv venv
   
   # Activate virtual environment
   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   
   # Windows (Command Prompt)
   venv\Scripts\activate.bat
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   # Install development dependencies
   pip install -r requirements-dev.txt
   
   # Install build dependencies
   pip install -r requirements-build.txt
   ```

4. **Verify Installation**

   ```bash
   # Run tests to verify setup
   python scripts/build.py --test --no-package
   
   # Run the application
   python main.py
   ```

## Cross-Platform Development Practices

### Code Guidelines

#### Path Handling

```python
# ✅ Good - Use pathlib for cross-platform paths
from pathlib import Path

config_path = Path.home() / ".heal" / "config.json"
resource_path = Path(__file__).parent / "resources" / "icon.png"

# ❌ Bad - Platform-specific path separators
config_path = os.path.expanduser("~/.heal/config.json")  # Unix only
resource_path = "resources\\icon.png"  # Windows only
```

#### File Operations

```python
# ✅ Good - Cross-platform file operations
import shutil
from pathlib import Path

def safe_copy(src: Path, dst: Path) -> bool:
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        logger.error(f"Failed to copy {src} to {dst}: {e}")
        return False

# ❌ Bad - Platform-specific operations
os.system("copy src dst")  # Windows only
os.system("cp src dst")    # Unix only
```

#### Environment Variables

```python
# ✅ Good - Cross-platform environment handling
import os
from pathlib import Path

def get_config_dir() -> Path:
    if os.name == 'nt':  # Windows
        return Path(os.environ.get('APPDATA', '~')) / 'HEAL'
    elif sys.platform == 'darwin':  # macOS
        return Path.home() / 'Library' / 'Application Support' / 'HEAL'
    else:  # Linux
        return Path(os.environ.get('XDG_CONFIG_HOME', '~/.config')) / 'heal'

# ❌ Bad - Assuming Unix-like environment
config_dir = Path.home() / '.heal'  # Won't follow Windows conventions
```

#### Process Execution

```python
# ✅ Good - Cross-platform process execution
import subprocess
import sys

def run_command(cmd: list[str]) -> bool:
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            shell=False  # Avoid shell=True for security
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(cmd)} - {e}")
        return False

# ❌ Bad - Platform-specific commands
os.system("dir")   # Windows only
os.system("ls")    # Unix only
```

### GUI Considerations

#### Window Management

```python
# Handle platform-specific window behaviors
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_platform_specific()
    
    def setup_platform_specific(self):
        if sys.platform == 'darwin':  # macOS
            # macOS-specific menu bar handling
            self.setUnifiedTitleAndToolBarOnMac(True)
        elif os.name == 'nt':  # Windows
            # Windows-specific taskbar integration
            self.setWindowIcon(QIcon('resources/icon.ico'))
        else:  # Linux
            # Linux desktop integration
            self.setWindowIcon(QIcon('resources/icon.png'))
```

#### High DPI Support

```python
# Enable high DPI support across platforms
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
```

### Resource Management

#### Icons and Images

```
resources/
├── images/
│   ├── icon.ico     # Windows icon
│   ├── icon.icns    # macOS icon
│   ├── icon.png     # Linux icon
│   └── icon.svg     # Scalable icon
```

#### Configuration Files

```python
# Platform-appropriate configuration locations
def get_config_locations():
    locations = {
        'user_config': get_user_config_dir(),
        'system_config': get_system_config_dir(),
        'portable_config': Path.cwd() / 'config'
    }
    return locations
```

## Building and Packaging

### Build System Architecture

The HEAL build system supports multiple packaging formats:

```
Build Process Flow:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Source Code   │ -> │  Cross-Platform  │ -> │   Executables   │
│                 │    │   Build Script   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                v
                       ┌──────────────────┐
                       │   Package Types  │
                       │                  │
                       │ Windows: ZIP/MSI │
                       │ macOS: ZIP/DMG   │
                       │ Linux: TAR/DEB   │
                       └──────────────────┘
```

### Build Commands

#### Basic Build

```bash
# Standard build for current platform
python scripts/build.py

# Debug build with verbose logging
python scripts/build.py --debug --verbose

# Build without packaging
python scripts/build.py --no-package
```

#### Advanced Build Options

```bash
# Use Nuitka instead of PyInstaller
python scripts/build.py --use-nuitka

# Specific package format
python scripts/build.py --package-format zip
python scripts/build.py --package-format msi    # Windows only
python scripts/build.py --package-format dmg    # macOS only
python scripts/build.py --package-format deb    # Linux only

# Run tests before building
python scripts/build.py --test

# Development build with dev dependencies
python scripts/build.py --dev
```

### Platform-Specific Build Requirements

#### Windows

```powershell
# Optional: WiX Toolset for MSI creation
# Download from: https://wixtoolset.org/
# Or install via Chocolatey:
choco install wixtoolset

# Visual C++ Redistributable (usually pre-installed)
# Required for PyInstaller executables
```

#### macOS

```bash
# Code signing (optional, for distribution)
# Requires Apple Developer account
security find-identity -v -p codesigning

# DMG creation tools
brew install create-dmg

# Notarization (for App Store/Gatekeeper)
# Requires Apple Developer account and app-specific password
```

#### Linux

```bash
# AppImage creation tools
sudo apt install fuse libfuse2  # Ubuntu/Debian
sudo dnf install fuse fuse-libs  # CentOS/RHEL/Fedora

# DEB package creation
sudo apt install dpkg-dev  # Ubuntu/Debian

# RPM package creation (optional)
sudo dnf install rpm-build  # CentOS/RHEL/Fedora
```

## Testing Across Platforms

### Automated Testing

#### CI/CD Pipeline

The project uses GitHub Actions for cross-platform testing:

```yaml
# Runs on every push and pull request
- Ubuntu Latest (Python 3.11, 3.12)
- Windows Latest (Python 3.11, 3.12)  
- macOS Latest (Python 3.11, 3.12)
```

#### Local Testing

```bash
# Run full test suite
python -m pytest tests/ -v

# Run platform-specific tests
python -m pytest tests/test_platform.py -v

# Run GUI tests (requires display)
python -m pytest tests/test_gui.py -v --tb=short

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Manual Testing Checklist

#### Functionality Testing

- [ ] Application starts without errors
- [ ] All menu items work correctly
- [ ] File operations (open, save, import, export)
- [ ] Network connectivity features
- [ ] Plugin system functionality
- [ ] Configuration persistence

#### Platform Integration Testing

- [ ] Desktop shortcuts work
- [ ] File associations (if applicable)
- [ ] System tray integration
- [ ] Native dialogs (file picker, etc.)
- [ ] Keyboard shortcuts
- [ ] Window management (minimize, maximize, close)

#### Performance Testing

- [ ] Startup time < 5 seconds
- [ ] Memory usage reasonable
- [ ] CPU usage during idle
- [ ] Responsiveness during operations

## Deployment Strategies

### Distribution Methods

#### Direct Download

- GitHub Releases with platform-specific packages
- Automatic updates through built-in updater
- Checksums and digital signatures for security

#### Package Managers

```bash
# Windows (future)
winget install ElementAstro.HEAL
choco install heal

# macOS (future)
brew install --cask heal

# Linux (future)
sudo apt install heal          # Ubuntu/Debian
sudo dnf install heal          # Fedora
sudo pacman -S heal           # Arch Linux
flatpak install heal          # Universal
snap install heal             # Universal
```

#### Portable Versions

- ZIP archives for all platforms
- No installation required
- Suitable for USB drives or restricted environments

### Installation Verification

#### Post-Installation Checks

```bash
# Verify installation
heal --version

# Check dependencies
heal --check-deps

# Run diagnostic
heal --diagnose

# Test basic functionality
heal --test-mode
```

## Troubleshooting

### Common Issues

#### Python Environment Issues

```bash
# Problem: ModuleNotFoundError
# Solution: Verify virtual environment and dependencies
python -m pip list
python -m pip install -r requirements.txt

# Problem: Permission denied
# Solution: Check file permissions and user rights
# Windows: Run as Administrator if needed
# macOS/Linux: Check file ownership and permissions
```

#### Build Issues

```bash
# Problem: PyInstaller fails
# Solution: Clear cache and rebuild
python -m PyInstaller --clean --noconfirm heal.spec

# Problem: Missing dependencies in executable
# Solution: Add to hidden imports in build script
# Edit scripts/build.py or platform-specific .spec files
```

#### Runtime Issues

```bash
# Problem: Application won't start
# Solution: Check logs and run in debug mode
heal --debug --log-level DEBUG

# Problem: GUI issues on Linux
# Solution: Install additional packages
sudo apt install libxcb-xinerama0 libxcb-cursor0
```

### Platform-Specific Issues

#### Windows

- **Antivirus False Positives**: Add HEAL to antivirus exclusions
- **DLL Issues**: Install Visual C++ Redistributable
- **Path Length Limits**: Enable long path support in Windows 10+

#### macOS

- **Gatekeeper Warnings**: Right-click and "Open" for unsigned apps
- **Permission Issues**: Grant necessary permissions in System Preferences
- **Rosetta 2**: Required for Intel apps on Apple Silicon

#### Linux

- **Missing Libraries**: Install development packages
- **Display Issues**: Set QT_QPA_PLATFORM environment variable
- **Permission Issues**: Add user to necessary groups

### Getting Help

#### Documentation

- [Installation Guide](INSTALL.md)
- [User Manual](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)
- [API Reference](docs/api-reference.md)

#### Community Support

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: General questions and community support
- **Discord**: Real-time chat and support
- **Email**: Direct contact for sensitive issues

#### Professional Support

- **Commercial License**: Enterprise support available
- **Custom Development**: Tailored solutions and integrations
- **Training**: On-site or remote training sessions
- **Consulting**: Architecture and deployment consulting

## Best Practices Summary

### Development

1. **Use pathlib** for all path operations
2. **Test on all platforms** regularly
3. **Handle platform differences** gracefully
4. **Follow platform conventions** for UI/UX
5. **Use virtual environments** consistently

### Building

1. **Automate builds** with CI/CD
2. **Test packages** before release
3. **Sign executables** when possible
4. **Provide multiple formats** per platform
5. **Document dependencies** clearly

### Deployment

1. **Use semantic versioning**
2. **Provide clear installation instructions**
3. **Include troubleshooting guides**
4. **Maintain backward compatibility**
5. **Plan for updates and migrations**

This guide provides the foundation for successful cross-platform development with HEAL. For specific technical details, refer to the individual component documentation and API references.

## Appendix

### Platform Detection Utilities

```python
# scripts/platform_utils.py - Platform detection and utilities
import platform
import sys
from pathlib import Path

def get_platform_info():
    """Get comprehensive platform information."""
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'is_windows': platform.system() == 'Windows',
        'is_macos': platform.system() == 'Darwin',
        'is_linux': platform.system() == 'Linux',
    }

def get_executable_name(base_name: str) -> str:
    """Get platform-specific executable name."""
    if platform.system() == 'Windows':
        return f"{base_name}.exe"
    return base_name

def get_config_dir(app_name: str = 'HEAL') -> Path:
    """Get platform-specific configuration directory."""
    if platform.system() == 'Windows':
        base = Path(os.environ.get('APPDATA', '~'))
    elif platform.system() == 'Darwin':
        base = Path.home() / 'Library' / 'Application Support'
    else:
        base = Path(os.environ.get('XDG_CONFIG_HOME', '~/.config'))

    return (base / app_name).expanduser()
```

### Build Script Examples

#### Windows Batch Script

```batch
@echo off
REM build-windows.bat - Windows build script
echo Building HEAL for Windows...

python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements-build.txt
python scripts\build.py --package-format zip,msi
echo Build complete!
pause
```

#### macOS Shell Script

```bash
#!/bin/bash
# build-macos.sh - macOS build script
set -e

echo "Building HEAL for macOS..."

python3 -m venv venv
source venv/bin/activate
pip install -r requirements-build.txt
python scripts/build.py --package-format zip,dmg

echo "Build complete!"
```

#### Linux Shell Script

```bash
#!/bin/bash
# build-linux.sh - Linux build script
set -e

echo "Building HEAL for Linux..."

python3 -m venv venv
source venv/bin/activate
pip install -r requirements-build.txt
python scripts/build.py --package-format tar.gz,appimage,deb

echo "Build complete!"
```

### Environment Setup Scripts

#### Windows PowerShell Setup

```powershell
# setup-dev-windows.ps1
Write-Host "Setting up HEAL development environment on Windows..."

# Check Python installation
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found. Please install Python 3.11+ from python.org"
    exit 1
}

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt

# Verify installation
python scripts/build.py --test --no-package

Write-Host "Development environment setup complete!"
```

#### Unix Setup Script

```bash
#!/bin/bash
# setup-dev-unix.sh - Setup script for macOS and Linux
set -e

echo "Setting up HEAL development environment..."

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt

# Verify installation
python scripts/build.py --test --no-package

echo "Development environment setup complete!"
```

### Testing Utilities

#### Cross-Platform Test Runner

```python
# scripts/test_runner.py
import subprocess
import sys
import platform
from pathlib import Path

def run_tests():
    """Run tests with platform-specific configurations."""
    env = os.environ.copy()

    # Platform-specific test environment
    if platform.system() == 'Linux':
        env['QT_QPA_PLATFORM'] = 'offscreen'
        env['DISPLAY'] = ':99'

    # Run test suite
    cmd = [sys.executable, '-m', 'pytest', 'tests/', '-v']

    if platform.system() == 'Windows':
        # Windows-specific test options
        cmd.extend(['--tb=short'])

    result = subprocess.run(cmd, env=env)
    return result.returncode == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
```

This comprehensive guide covers all aspects of cross-platform development, building, and deployment for the HEAL project.
