# HEAL Deployment Guide

This guide covers deployment strategies, distribution methods, and best practices for deploying HEAL across different platforms and environments.

## Deployment Overview

HEAL supports multiple deployment strategies to accommodate different use cases:

- **Standalone Executables**: Self-contained applications for end users
- **Package Managers**: Integration with system package managers
- **Container Deployment**: Docker and container orchestration
- **Enterprise Deployment**: Large-scale organizational deployment
- **Cloud Deployment**: Cloud-based hosting and distribution

## Standalone Executables

### Build Process

#### Automated Building

```bash
# Build for current platform
python scripts/build.py

# Build with specific package format
python scripts/build.py --package-format zip,msi  # Windows
python scripts/build.py --package-format zip,dmg  # macOS
python scripts/build.py --package-format tar.gz,appimage,deb  # Linux

# Cross-platform build (requires CI/CD)
# See .github/workflows/build-and-release.yml
```

#### Manual Building

```bash
# Clean build environment
python scripts/build.py --clean

# Install build dependencies
pip install -r requirements-build.txt

# Build with debugging enabled
python scripts/build.py --debug --verbose

# Test the built executable
./dist/HEAL/HEAL  # Unix
dist\HEAL\HEAL.exe  # Windows
```

### Distribution Packages

#### Windows Distribution

```
HEAL-windows-x64.zip
├── HEAL.exe                 # Main executable
├── _internal/               # PyInstaller dependencies
├── config/                  # Default configuration
├── README.md               # Installation instructions
├── LICENSE                 # License file
└── heal.bat               # Launcher script (optional)

HEAL-windows-x64.msi        # Windows installer (if available)
```

#### macOS Distribution

```
HEAL-macos-x64.zip
├── HEAL.app/               # macOS application bundle
│   ├── Contents/
│   │   ├── MacOS/HEAL     # Executable
│   │   ├── Resources/     # Resources and icons
│   │   └── Info.plist     # App metadata
├── README.md
└── LICENSE

HEAL-macos-x64.dmg         # macOS disk image (if available)
```

#### Linux Distribution

```
HEAL-linux-x64.tar.gz
├── HEAL                    # Main executable
├── _internal/              # Dependencies
├── config/                 # Default configuration
├── heal.desktop           # Desktop entry
├── heal.png              # Application icon
├── README.md
└── LICENSE

HEAL-linux-x64.AppImage    # Universal Linux app (if available)
HEAL-linux-x64.deb        # Debian package (if available)
```

### Installation Scripts

#### Windows Installation

```powershell
# install.ps1 - Windows PowerShell installer
param(
    [string]$InstallPath = "$env:LOCALAPPDATA\HEAL",
    [switch]$NoDesktopShortcut,
    [switch]$NoStartMenu
)

# Extract and install HEAL
# Create shortcuts and file associations
# Register with Windows Programs and Features
```

#### Unix Installation

```bash
#!/bin/bash
# install.sh - Unix installer script

INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/share/heal}"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"

# Extract application
# Create launcher scripts
# Install desktop entries
# Set up PATH integration
```

## Package Manager Integration

### Windows Package Managers

#### Chocolatey Package

```xml
<!-- heal.nuspec -->
<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>heal</id>
    <version>1.0.0</version>
    <title>HEAL - Hello ElementAstro Launcher</title>
    <authors>ElementAstro</authors>
    <description>Astronomical software launcher and management system</description>
    <projectUrl>https://github.com/ElementAstro/HEAL</projectUrl>
    <licenseUrl>https://github.com/ElementAstro/HEAL/blob/main/LICENSE</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <tags>astronomy astrophotography launcher</tags>
  </metadata>
</package>
```

#### Winget Package

```yaml
# winget-manifest.yaml
PackageIdentifier: ElementAstro.HEAL
PackageVersion: 1.0.0
PackageName: HEAL
Publisher: ElementAstro
License: MIT
ShortDescription: Hello ElementAstro Launcher
Installers:
- Architecture: x64
  InstallerType: zip
  InstallerUrl: https://github.com/ElementAstro/HEAL/releases/download/v1.0.0/HEAL-windows-x64.zip
  InstallerSha256: [SHA256_HASH]
```

### macOS Package Managers

#### Homebrew Cask

```ruby
# heal.rb - Homebrew cask formula
cask "heal" do
  version "1.0.0"
  sha256 "[SHA256_HASH]"

  url "https://github.com/ElementAstro/HEAL/releases/download/v#{version}/HEAL-macos-x64.zip"
  name "HEAL"
  desc "Hello ElementAstro Launcher"
  homepage "https://github.com/ElementAstro/HEAL"

  app "HEAL.app"

  zap trash: [
    "~/Library/Application Support/HEAL",
    "~/Library/Preferences/com.elementastro.heal.plist",
  ]
end
```

### Linux Package Managers

#### Debian/Ubuntu Package

```bash
# Create DEB package structure
mkdir -p heal-1.0.0/DEBIAN
mkdir -p heal-1.0.0/opt/heal
mkdir -p heal-1.0.0/usr/share/applications
mkdir -p heal-1.0.0/usr/share/icons/hicolor/256x256/apps

# Control file
cat > heal-1.0.0/DEBIAN/control << EOF
Package: heal
Version: 1.0.0
Section: science
Priority: optional
Architecture: amd64
Maintainer: ElementAstro <astro_air@126.com>
Description: Hello ElementAstro Launcher
 Astronomical software launcher and management system
EOF

# Build package
dpkg-deb --build heal-1.0.0
```

#### Flatpak Package

```yaml
# com.elementastro.HEAL.yaml
app-id: com.elementastro.HEAL
runtime: org.freedesktop.Platform
runtime-version: '22.08'
sdk: org.freedesktop.Sdk
command: heal

finish-args:
  - --share=ipc
  - --socket=x11
  - --socket=wayland
  - --device=dri
  - --filesystem=home

modules:
  - name: heal
    buildsystem: simple
    build-commands:
      - install -Dm755 HEAL /app/bin/heal
      - install -Dm644 heal.desktop /app/share/applications/com.elementastro.HEAL.desktop
      - install -Dm644 heal.png /app/share/icons/hicolor/256x256/apps/com.elementastro.HEAL.png
    sources:
      - type: archive
        url: https://github.com/ElementAstro/HEAL/releases/download/v1.0.0/HEAL-linux-x64.tar.gz
        sha256: [SHA256_HASH]
```

## Container Deployment

### Docker Image

#### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    libegl1-mesa \
    libfontconfig1 \
    libglib2.0-0 \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 heal

# Set working directory
WORKDIR /app

# Copy application
COPY --chown=heal:heal . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Switch to app user
USER heal

# Expose port (if applicable)
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["python", "main.py"]
```

#### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  heal:
    build: .
    container_name: heal
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - heal_data:/app/data
      - heal_config:/app/config
    environment:
      - HEAL_CONFIG_DIR=/app/config
      - HEAL_DATA_DIR=/app/data
    networks:
      - heal_network

volumes:
  heal_data:
  heal_config:

networks:
  heal_network:
    driver: bridge
```

### Kubernetes Deployment

#### Deployment Manifest

```yaml
# heal-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: heal
  labels:
    app: heal
spec:
  replicas: 1
  selector:
    matchLabels:
      app: heal
  template:
    metadata:
      labels:
        app: heal
    spec:
      containers:
      - name: heal
        image: elementastro/heal:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: HEAL_CONFIG_DIR
          value: "/app/config"
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        - name: data-volume
          mountPath: /app/data
      volumes:
      - name: config-volume
        configMap:
          name: heal-config
      - name: data-volume
        persistentVolumeClaim:
          claimName: heal-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: heal-service
spec:
  selector:
    app: heal
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

## Enterprise Deployment

### Group Policy Deployment (Windows)

#### MSI Deployment

```xml
<!-- heal-gpo.xml - Group Policy deployment -->
<GroupPolicyObject>
  <SoftwareInstallation>
    <Package>
      <Name>HEAL</Name>
      <Path>\\server\share\HEAL-1.0.0.msi</Path>
      <InstallationType>Assigned</InstallationType>
      <TargetUsers>Domain Users</TargetUsers>
    </Package>
  </SoftwareInstallation>
</GroupPolicyObject>
```

#### Configuration Management

```powershell
# deploy-heal-enterprise.ps1
param(
    [string]$ConfigServer = "config.company.com",
    [string]$LicenseKey = $env:HEAL_LICENSE_KEY
)

# Download and install HEAL
# Configure enterprise settings
# Set up centralized logging
# Register with management system
```

### Linux Enterprise Deployment

#### Ansible Playbook

```yaml
# heal-deployment.yml
---
- name: Deploy HEAL to Linux systems
  hosts: workstations
  become: yes
  
  vars:
    heal_version: "1.0.0"
    heal_url: "https://github.com/ElementAstro/HEAL/releases/download/v{{ heal_version }}/HEAL-linux-x64.tar.gz"
    
  tasks:
    - name: Create HEAL user
      user:
        name: heal
        system: yes
        shell: /bin/false
        
    - name: Download HEAL
      get_url:
        url: "{{ heal_url }}"
        dest: "/tmp/heal-{{ heal_version }}.tar.gz"
        
    - name: Extract HEAL
      unarchive:
        src: "/tmp/heal-{{ heal_version }}.tar.gz"
        dest: /opt/
        owner: heal
        group: heal
        
    - name: Create systemd service
      template:
        src: heal.service.j2
        dest: /etc/systemd/system/heal.service
        
    - name: Enable and start HEAL service
      systemd:
        name: heal
        enabled: yes
        state: started
```

### Configuration Management

#### Centralized Configuration

```json
{
  "enterprise": {
    "config_server": "https://config.company.com/heal",
    "license_key": "${HEAL_LICENSE_KEY}",
    "update_server": "https://updates.company.com/heal",
    "logging": {
      "remote_endpoint": "https://logs.company.com/heal",
      "level": "INFO"
    },
    "policies": {
      "auto_update": true,
      "telemetry": false,
      "user_config_override": false
    }
  }
}
```

## Cloud Deployment

### AWS Deployment

#### EC2 Instance

```bash
#!/bin/bash
# aws-deploy.sh - AWS EC2 deployment script

# Install dependencies
sudo yum update -y
sudo yum install -y python3 python3-pip

# Download and install HEAL
wget https://github.com/ElementAstro/HEAL/releases/download/v1.0.0/HEAL-linux-x64.tar.gz
tar -xzf HEAL-linux-x64.tar.gz
sudo mv HEAL /opt/

# Create systemd service
sudo tee /etc/systemd/system/heal.service > /dev/null <<EOF
[Unit]
Description=HEAL Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/HEAL
ExecStart=/opt/HEAL/HEAL
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable heal
sudo systemctl start heal
```

#### ECS Task Definition

```json
{
  "family": "heal-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "heal",
      "image": "elementastro/heal:1.0.0",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "HEAL_CONFIG_DIR",
          "value": "/app/config"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/heal",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Azure Deployment

#### Container Instance

```yaml
# azure-container-instance.yaml
apiVersion: 2019-12-01
location: eastus
name: heal-container
properties:
  containers:
  - name: heal
    properties:
      image: elementastro/heal:1.0.0
      resources:
        requests:
          cpu: 0.5
          memoryInGb: 1
      ports:
      - port: 8080
        protocol: TCP
      environmentVariables:
      - name: HEAL_CONFIG_DIR
        value: /app/config
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8080
  restartPolicy: Always
tags:
  app: heal
  environment: production
```

### Google Cloud Deployment

#### Cloud Run Service

```yaml
# cloudrun-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: heal
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 1000
      containers:
      - image: gcr.io/project-id/heal:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: HEAL_CONFIG_DIR
          value: /app/config
        resources:
          limits:
            cpu: 1000m
            memory: 1Gi
```

## Deployment Best Practices

### Security Considerations

1. **Code Signing**: Sign executables for Windows and macOS
2. **Checksums**: Provide SHA256 checksums for all packages
3. **HTTPS**: Use HTTPS for all download URLs
4. **Vulnerability Scanning**: Regular security scans of dependencies
5. **Access Control**: Limit deployment access to authorized personnel

### Version Management

1. **Semantic Versioning**: Use semver for all releases
2. **Release Notes**: Detailed changelog for each version
3. **Rollback Plan**: Ability to rollback to previous versions
4. **Testing**: Comprehensive testing before deployment
5. **Staged Rollout**: Gradual deployment to minimize risk

### Monitoring and Logging

1. **Health Checks**: Implement application health endpoints
2. **Metrics Collection**: Monitor performance and usage
3. **Log Aggregation**: Centralized logging for troubleshooting
4. **Alerting**: Automated alerts for critical issues
5. **Analytics**: Usage analytics for product improvement

### Update Management

1. **Automatic Updates**: Built-in update mechanism
2. **Update Channels**: Stable, beta, and development channels
3. **Differential Updates**: Minimize download size
4. **Offline Updates**: Support for air-gapped environments
5. **Update Verification**: Verify update integrity

This deployment guide provides comprehensive coverage of deployment strategies for HEAL across different platforms and environments. Choose the appropriate deployment method based on your specific requirements and infrastructure.
