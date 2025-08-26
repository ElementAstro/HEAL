#!/bin/bash
# HEAL - Hello ElementAstro Launcher
# Cross-platform installation script for Unix-like systems (Linux, macOS)
# Copyright (C) 2024 ElementAstro

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HEAL_VERSION="1.0.0"
INSTALL_DIR="$HOME/.local/share/heal"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        DISTRO=$(lsb_release -si 2>/dev/null || echo "Unknown")
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macOS"
    else
        OS="unknown"
        DISTRO="Unknown"
    fi
}

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check for required commands
    local missing_commands=()
    
    if ! command_exists "python3"; then
        missing_commands+=("python3")
    fi
    
    if ! command_exists "pip3"; then
        missing_commands+=("python3-pip")
    fi
    
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        print_error "Missing required packages: ${missing_commands[*]}"
        print_status "Please install them using your package manager:"
        
        if [[ "$OS" == "linux" ]]; then
            case "$DISTRO" in
                "Ubuntu"|"Debian")
                    echo "  sudo apt update && sudo apt install ${missing_commands[*]}"
                    ;;
                "CentOS"|"RHEL"|"Fedora")
                    echo "  sudo dnf install ${missing_commands[*]}"
                    ;;
                "Arch")
                    echo "  sudo pacman -S ${missing_commands[*]}"
                    ;;
                *)
                    echo "  Use your distribution's package manager to install: ${missing_commands[*]}"
                    ;;
            esac
        elif [[ "$OS" == "macos" ]]; then
            echo "  brew install python3"
        fi
        
        exit 1
    fi
    
    # Check Python version
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local required_version="3.11"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
        print_warning "Python $python_version detected. Python $required_version or higher is recommended."
    else
        print_success "Python $python_version detected (compatible)"
    fi
}

# Create directories
create_directories() {
    print_status "Creating installation directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"
    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$ICON_DIR"
    
    print_success "Directories created"
}

# Install HEAL
install_heal() {
    print_status "Installing HEAL application..."
    
    # Check if we're in the source directory
    if [[ -f "main.py" && -d "src/heal" ]]; then
        print_status "Installing from source directory..."
        
        # Copy application files
        cp -r . "$INSTALL_DIR/"
        
        # Install Python dependencies
        print_status "Installing Python dependencies..."
        pip3 install --user -r requirements.txt
        
        # Build the application if build script exists
        if [[ -f "scripts/build.py" ]]; then
            print_status "Building HEAL application..."
            cd "$INSTALL_DIR"
            python3 scripts/build.py --no-clean
        fi
        
    elif [[ -f "HEAL" || -f "HEAL.exe" ]]; then
        print_status "Installing from pre-built package..."
        
        # Copy pre-built files
        cp -r . "$INSTALL_DIR/"
        
    else
        print_error "HEAL application files not found in current directory"
        print_status "Please run this script from the HEAL source or distribution directory"
        exit 1
    fi
    
    print_success "HEAL application installed"
}

# Create launcher script
create_launcher() {
    print_status "Creating launcher script..."
    
    local launcher_script="$BIN_DIR/heal"
    
    cat > "$launcher_script" << EOF
#!/bin/bash
# HEAL Launcher Script
cd "$INSTALL_DIR"

# Try to run the built executable first
if [[ -f "dist/HEAL/HEAL" ]]; then
    exec "./dist/HEAL/HEAL" "\$@"
elif [[ -f "HEAL" ]]; then
    exec "./HEAL" "\$@"
elif [[ -f "main.py" ]]; then
    exec python3 main.py "\$@"
else
    echo "Error: HEAL executable not found"
    exit 1
fi
EOF
    
    chmod +x "$launcher_script"
    print_success "Launcher script created at $launcher_script"
}

# Create desktop entry (Linux only)
create_desktop_entry() {
    if [[ "$OS" != "linux" ]]; then
        return
    fi
    
    print_status "Creating desktop entry..."
    
    local desktop_file="$DESKTOP_DIR/heal.desktop"
    local icon_path="$INSTALL_DIR/src/heal/resources/images/icon.png"
    
    # Copy icon if it exists
    if [[ -f "$icon_path" ]]; then
        cp "$icon_path" "$ICON_DIR/heal.png"
        icon_path="$ICON_DIR/heal.png"
    else
        icon_path="applications-science"  # Fallback icon
    fi
    
    cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=HEAL
Comment=Hello ElementAstro Launcher - Astronomical software launcher
Exec=$BIN_DIR/heal
Icon=$icon_path
Terminal=false
Categories=Science;Astronomy;Education;
Keywords=astronomy;telescope;astrophotography;launcher;
StartupNotify=true
EOF
    
    chmod +x "$desktop_file"
    
    # Update desktop database if available
    if command_exists "update-desktop-database"; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    fi
    
    print_success "Desktop entry created"
}

# Add to PATH
setup_path() {
    print_status "Setting up PATH..."
    
    local shell_rc=""
    if [[ -n "$BASH_VERSION" ]]; then
        shell_rc="$HOME/.bashrc"
    elif [[ -n "$ZSH_VERSION" ]]; then
        shell_rc="$HOME/.zshrc"
    else
        shell_rc="$HOME/.profile"
    fi
    
    # Check if BIN_DIR is already in PATH
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$shell_rc"
        print_success "Added $BIN_DIR to PATH in $shell_rc"
        print_warning "Please restart your terminal or run: source $shell_rc"
    else
        print_success "PATH already configured"
    fi
}

# Cleanup function
cleanup() {
    if [[ $? -ne 0 ]]; then
        print_error "Installation failed. Cleaning up..."
        rm -rf "$INSTALL_DIR" 2>/dev/null || true
        rm -f "$BIN_DIR/heal" 2>/dev/null || true
        rm -f "$DESKTOP_DIR/heal.desktop" 2>/dev/null || true
        rm -f "$ICON_DIR/heal.png" 2>/dev/null || true
    fi
}

# Main installation function
main() {
    echo "HEAL - Hello ElementAstro Launcher Installer"
    echo "============================================="
    echo
    
    detect_os
    print_status "Detected OS: $DISTRO ($OS)"
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    check_requirements
    create_directories
    install_heal
    create_launcher
    create_desktop_entry
    setup_path
    
    echo
    print_success "HEAL installation completed successfully!"
    echo
    print_status "You can now run HEAL using:"
    echo "  heal                    # From command line (after PATH setup)"
    echo "  $BIN_DIR/heal          # Direct path"
    
    if [[ "$OS" == "linux" ]]; then
        echo "  Or find it in your applications menu"
    fi
    
    echo
    print_status "Installation directory: $INSTALL_DIR"
    print_status "For uninstallation, run: rm -rf '$INSTALL_DIR' '$BIN_DIR/heal' '$DESKTOP_DIR/heal.desktop' '$ICON_DIR/heal.png'"
}

# Run main function
main "$@"
