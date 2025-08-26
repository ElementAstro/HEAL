# HEAL Installation Guide

This guide provides instructions for installing HEAL (Hello ElementAstro Launcher) on different platforms.

## Quick Installation

### Windows

1. **Using PowerShell (Recommended)**:
   ```powershell
   # Run PowerShell as regular user (not Administrator)
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\install.ps1
   ```

2. **Manual Installation**:
   - Extract the HEAL package to a folder (e.g., `C:\Users\YourName\AppData\Local\HEAL`)
   - Run `HEAL.exe` or `heal.bat`

### Linux / macOS

1. **Using the install script**:
   ```bash
   # Make the script executable
   chmod +x install.sh
   
   # Run the installer
   ./install.sh
   ```

2. **Manual Installation**:
   ```bash
   # Copy to local directory
   mkdir -p ~/.local/share/heal
   cp -r . ~/.local/share/heal/
   
   # Create launcher
   mkdir -p ~/.local/bin
   echo '#!/bin/bash' > ~/.local/bin/heal
   echo 'cd ~/.local/share/heal && ./HEAL' >> ~/.local/bin/heal
   chmod +x ~/.local/bin/heal
   ```

## System Requirements

### All Platforms
- **Python**: 3.11 or higher (recommended)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB free space
- **Display**: 1024x768 minimum resolution

### Windows Specific
- **OS**: Windows 10 or later
- **PowerShell**: 5.0 or later
- **Visual C++ Redistributable**: 2019 or later (usually pre-installed)

### Linux Specific
- **Distribution**: Ubuntu 20.04+, Debian 11+, CentOS 8+, or equivalent
- **Desktop Environment**: GNOME, KDE, XFCE, or similar
- **Dependencies**: 
  ```bash
  # Ubuntu/Debian
  sudo apt install python3 python3-pip python3-venv
  
  # CentOS/RHEL/Fedora
  sudo dnf install python3 python3-pip
  
  # Arch Linux
  sudo pacman -S python python-pip
  ```

### macOS Specific
- **OS**: macOS 10.14 (Mojave) or later
- **Xcode Command Line Tools**: `xcode-select --install`
- **Homebrew** (recommended): 
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  brew install python3
  ```

## Installation Options

### Standard Installation
Installs HEAL to the default user directory with desktop integration.

**Windows**: `%LOCALAPPDATA%\HEAL`
**Linux/macOS**: `~/.local/share/heal`

### Custom Installation Path

**Windows**:
```powershell
.\install.ps1 -InstallPath "C:\MyPrograms\HEAL"
```

**Linux/macOS**:
```bash
INSTALL_DIR="/opt/heal" ./install.sh
```

### Development Installation

For developers who want to run HEAL from source:

```bash
# Clone the repository
git clone https://github.com/ElementAstro/HEAL.git
cd HEAL

# Set up development environment
python3 scripts/setup_dev.py

# Build the application
python3 scripts/build.py

# Run from source
python3 main.py
```

## Post-Installation

### Verify Installation

**Windows**:
- Check Start Menu for "HEAL" folder
- Look for desktop shortcut (if created)
- Run from Command Prompt: `%LOCALAPPDATA%\HEAL\heal.bat`

**Linux**:
- Check applications menu for "HEAL"
- Run from terminal: `heal` (if PATH is configured)
- Run directly: `~/.local/bin/heal`

**macOS**:
- Check Applications folder or Launchpad
- Run from terminal: `heal`
- Run directly: `~/.local/bin/heal`

### Configuration

1. **First Run**: HEAL will create configuration files in:
   - Windows: `%LOCALAPPDATA%\HEAL\config\`
   - Linux/macOS: `~/.local/share/heal/config/`

2. **Logging**: Application logs are stored in:
   - Windows: `%LOCALAPPDATA%\HEAL\logs\`
   - Linux/macOS: `~/.local/share/heal/logs/`

## Troubleshooting

### Common Issues

1. **"Python not found"**:
   - Install Python 3.11+ from python.org
   - Ensure Python is in your system PATH

2. **"Permission denied" (Linux/macOS)**:
   - Make sure install.sh is executable: `chmod +x install.sh`
   - Don't run with sudo unless installing system-wide

3. **"Execution Policy" error (Windows)**:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Missing dependencies**:
   - Run: `pip3 install -r requirements.txt`
   - Or use the development setup: `python3 scripts/setup_dev.py`

5. **Application won't start**:
   - Check logs in the logs directory
   - Try running from terminal to see error messages
   - Verify all dependencies are installed

### Getting Help

- **Documentation**: Check the `docs/` directory
- **Issues**: Report bugs on GitHub Issues
- **Community**: Join our Discord server (link in README.md)

## Uninstallation

### Windows
Run the uninstaller: `%LOCALAPPDATA%\HEAL\uninstall.ps1`

Or manually:
1. Delete the installation directory
2. Remove desktop shortcut
3. Remove Start Menu folder

### Linux/macOS
```bash
# Remove installation
rm -rf ~/.local/share/heal

# Remove launcher
rm -f ~/.local/bin/heal

# Remove desktop entry (Linux)
rm -f ~/.local/share/applications/heal.desktop
rm -f ~/.local/share/icons/heal.png
```

## Advanced Installation

### System-wide Installation (Linux)

```bash
# Install to /opt/heal (requires sudo)
sudo mkdir -p /opt/heal
sudo cp -r . /opt/heal/
sudo ln -s /opt/heal/HEAL /usr/local/bin/heal

# Create system-wide desktop entry
sudo cp heal.desktop /usr/share/applications/
```

### Portable Installation

For a portable installation that doesn't modify the system:

1. Extract HEAL to any folder
2. Run directly from that folder
3. Configuration will be stored in the same folder

### Docker Installation

```bash
# Build Docker image
docker build -t heal:latest .

# Run HEAL in container
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  heal:latest
```

## Building from Source

See [docs/developer-guide/building.md](docs/developer-guide/building.md) for detailed build instructions.
