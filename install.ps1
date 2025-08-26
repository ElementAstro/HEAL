# HEAL - Hello ElementAstro Launcher
# Windows PowerShell installation script
# Copyright (C) 2024 ElementAstro

param(
    [switch]$Force,
    [string]$InstallPath = "$env:LOCALAPPDATA\HEAL",
    [switch]$NoDesktopShortcut,
    [switch]$NoStartMenu,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Configuration
$HealVersion = "1.0.0"
$StartMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$DesktopPath = [Environment]::GetFolderPath("Desktop")

# Colors for output (if supported)
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

# Logging functions
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check system requirements
function Test-Requirements {
    Write-Status "Checking system requirements..."
    
    # Check Windows version
    $osVersion = [System.Environment]::OSVersion.Version
    if ($osVersion.Major -lt 10) {
        Write-Warning "Windows 10 or later is recommended. Current version: $($osVersion.ToString())"
    } else {
        Write-Success "Windows version: $($osVersion.ToString()) (compatible)"
    }
    
    # Check PowerShell version
    $psVersion = $PSVersionTable.PSVersion
    if ($psVersion.Major -lt 5) {
        Write-Error "PowerShell 5.0 or later is required. Current version: $($psVersion.ToString())"
        exit 1
    } else {
        Write-Success "PowerShell version: $($psVersion.ToString()) (compatible)"
    }
    
    # Check for Python (optional)
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion) {
            Write-Success "Python detected: $pythonVersion"
        }
    } catch {
        Write-Warning "Python not found. Some features may require Python 3.11+"
    }
    
    # Check available disk space
    $drive = (Get-Item $InstallPath).PSDrive.Name
    $freeSpace = (Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='${drive}:'").FreeSpace
    $requiredSpace = 500MB  # Estimated requirement
    
    if ($freeSpace -lt $requiredSpace) {
        Write-Error "Insufficient disk space. Required: $($requiredSpace/1MB)MB, Available: $($freeSpace/1MB)MB"
        exit 1
    }
}

# Create installation directories
function New-InstallDirectories {
    Write-Status "Creating installation directories..."
    
    try {
        if (Test-Path $InstallPath) {
            if ($Force) {
                Write-Warning "Removing existing installation at $InstallPath"
                Remove-Item $InstallPath -Recurse -Force
            } else {
                Write-Error "Installation directory already exists: $InstallPath"
                Write-Status "Use -Force to overwrite existing installation"
                exit 1
            }
        }
        
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
        Write-Success "Installation directory created: $InstallPath"
        
    } catch {
        Write-Error "Failed to create installation directory: $($_.Exception.Message)"
        exit 1
    }
}

# Install HEAL application
function Install-Heal {
    Write-Status "Installing HEAL application..."
    
    try {
        # Check if we're in the source directory
        if (Test-Path "main.py" -and Test-Path "src\heal") {
            Write-Status "Installing from source directory..."
            
            # Copy application files
            Copy-Item -Path "." -Destination $InstallPath -Recurse -Force
            
            # Install Python dependencies if requirements.txt exists
            if (Test-Path "requirements.txt") {
                Write-Status "Installing Python dependencies..."
                try {
                    python -m pip install --user -r requirements.txt
                    Write-Success "Python dependencies installed"
                } catch {
                    Write-Warning "Failed to install Python dependencies: $($_.Exception.Message)"
                }
            }
            
            # Build the application if build script exists
            if (Test-Path "scripts\build.py") {
                Write-Status "Building HEAL application..."
                Set-Location $InstallPath
                try {
                    python scripts\build.py --no-clean
                    Write-Success "HEAL application built successfully"
                } catch {
                    Write-Warning "Build failed: $($_.Exception.Message)"
                }
            }
            
        } elseif (Test-Path "HEAL.exe" -or Test-Path "HEAL") {
            Write-Status "Installing from pre-built package..."
            
            # Copy pre-built files
            Copy-Item -Path "." -Destination $InstallPath -Recurse -Force
            
        } else {
            Write-Error "HEAL application files not found in current directory"
            Write-Status "Please run this script from the HEAL source or distribution directory"
            exit 1
        }
        
        Write-Success "HEAL application installed successfully"
        
    } catch {
        Write-Error "Installation failed: $($_.Exception.Message)"
        exit 1
    }
}

# Create launcher script
function New-Launcher {
    Write-Status "Creating launcher script..."
    
    try {
        $launcherScript = @"
@echo off
cd /d "$InstallPath"

REM Try to run the built executable first
if exist "dist\HEAL\HEAL.exe" (
    start "" "dist\HEAL\HEAL.exe" %*
) else if exist "HEAL.exe" (
    start "" "HEAL.exe" %*
) else if exist "main.py" (
    python main.py %*
) else (
    echo Error: HEAL executable not found
    pause
    exit /b 1
)
"@
        
        $launcherPath = "$InstallPath\heal.bat"
        $launcherScript | Out-File -FilePath $launcherPath -Encoding ASCII
        
        Write-Success "Launcher script created: $launcherPath"
        
    } catch {
        Write-Error "Failed to create launcher script: $($_.Exception.Message)"
    }
}

# Create desktop shortcut
function New-DesktopShortcut {
    if ($NoDesktopShortcut) {
        return
    }
    
    Write-Status "Creating desktop shortcut..."
    
    try {
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$DesktopPath\HEAL.lnk")
        $Shortcut.TargetPath = "$InstallPath\heal.bat"
        $Shortcut.WorkingDirectory = $InstallPath
        $Shortcut.Description = "Hello ElementAstro Launcher"
        
        # Set icon if available
        $iconPath = "$InstallPath\src\heal\resources\images\icon.ico"
        if (Test-Path $iconPath) {
            $Shortcut.IconLocation = $iconPath
        }
        
        $Shortcut.Save()
        Write-Success "Desktop shortcut created"
        
    } catch {
        Write-Warning "Failed to create desktop shortcut: $($_.Exception.Message)"
    }
}

# Create Start Menu shortcut
function New-StartMenuShortcut {
    if ($NoStartMenu) {
        return
    }
    
    Write-Status "Creating Start Menu shortcut..."
    
    try {
        $startMenuDir = "$StartMenuPath\HEAL"
        New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
        
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$startMenuDir\HEAL.lnk")
        $Shortcut.TargetPath = "$InstallPath\heal.bat"
        $Shortcut.WorkingDirectory = $InstallPath
        $Shortcut.Description = "Hello ElementAstro Launcher"
        
        # Set icon if available
        $iconPath = "$InstallPath\src\heal\resources\images\icon.ico"
        if (Test-Path $iconPath) {
            $Shortcut.IconLocation = $iconPath
        }
        
        $Shortcut.Save()
        
        # Create uninstaller shortcut
        $UninstallShortcut = $WshShell.CreateShortcut("$startMenuDir\Uninstall HEAL.lnk")
        $UninstallShortcut.TargetPath = "powershell.exe"
        $UninstallShortcut.Arguments = "-ExecutionPolicy Bypass -File `"$InstallPath\uninstall.ps1`""
        $UninstallShortcut.WorkingDirectory = $InstallPath
        $UninstallShortcut.Description = "Uninstall HEAL"
        $UninstallShortcut.Save()
        
        Write-Success "Start Menu shortcuts created"
        
    } catch {
        Write-Warning "Failed to create Start Menu shortcuts: $($_.Exception.Message)"
    }
}

# Create uninstaller
function New-Uninstaller {
    Write-Status "Creating uninstaller..."
    
    try {
        $uninstallScript = @"
# HEAL Uninstaller
param([switch]`$Silent)

if (-not `$Silent) {
    `$result = [System.Windows.Forms.MessageBox]::Show(
        "Are you sure you want to uninstall HEAL?",
        "Uninstall HEAL",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    
    if (`$result -eq [System.Windows.Forms.DialogResult]::No) {
        exit 0
    }
}

Write-Host "Uninstalling HEAL..." -ForegroundColor Yellow

# Remove installation directory
Remove-Item "$InstallPath" -Recurse -Force -ErrorAction SilentlyContinue

# Remove shortcuts
Remove-Item "$DesktopPath\HEAL.lnk" -Force -ErrorAction SilentlyContinue
Remove-Item "$StartMenuPath\HEAL" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "HEAL has been uninstalled successfully." -ForegroundColor Green

if (-not `$Silent) {
    Read-Host "Press Enter to exit"
}
"@
        
        $uninstallPath = "$InstallPath\uninstall.ps1"
        $uninstallScript | Out-File -FilePath $uninstallPath -Encoding UTF8
        
        Write-Success "Uninstaller created: $uninstallPath"
        
    } catch {
        Write-Warning "Failed to create uninstaller: $($_.Exception.Message)"
    }
}

# Cleanup function
function Invoke-Cleanup {
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Installation failed. Cleaning up..."
        try {
            Remove-Item $InstallPath -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item "$DesktopPath\HEAL.lnk" -Force -ErrorAction SilentlyContinue
            Remove-Item "$StartMenuPath\HEAL" -Recurse -Force -ErrorAction SilentlyContinue
        } catch {
            # Ignore cleanup errors
        }
    }
}

# Main installation function
function Install-Main {
    Write-Host "HEAL - Hello ElementAstro Launcher Installer" -ForegroundColor Cyan
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Status "Installation path: $InstallPath"
    
    if (Test-Administrator) {
        Write-Warning "Running as Administrator. This is not required for user installation."
    }
    
    try {
        Test-Requirements
        New-InstallDirectories
        Install-Heal
        New-Launcher
        New-DesktopShortcut
        New-StartMenuShortcut
        New-Uninstaller
        
        Write-Host ""
        Write-Success "HEAL installation completed successfully!"
        Write-Host ""
        Write-Status "You can now run HEAL using:"
        Write-Host "  - Desktop shortcut (if created)"
        Write-Host "  - Start Menu > HEAL > HEAL"
        Write-Host "  - Command: $InstallPath\heal.bat"
        Write-Host ""
        Write-Status "Installation directory: $InstallPath"
        Write-Status "To uninstall, run: $InstallPath\uninstall.ps1"
        
    } catch {
        Write-Error "Installation failed: $($_.Exception.Message)"
        Invoke-Cleanup
        exit 1
    }
}

# Run main installation
Install-Main
