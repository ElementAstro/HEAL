# HEAL - Hello ElementAstro Launcher

[![Build Status](https://github.com/ElementAstro/HEAL/workflows/Cross-Platform%20Build%20and%20Release/badge.svg)](https://github.com/ElementAstro/HEAL/actions)
[![Security Scan](https://github.com/ElementAstro/HEAL/workflows/Security%20Scan/badge.svg)](https://github.com/ElementAstro/HEAL/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Cross-Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/ElementAstro/HEAL)

HEAL (Hello ElementAstro Launcher) is a comprehensive, cross-platform launcher and management system for astronomical software, designed to streamline the workflow of astrophotographers and astronomers.

## ✨ Features

- **🖥️ Cross-Platform**: Native support for Windows, macOS, and Linux
- **🎯 Unified Interface**: Centralized control for multiple astronomical applications
- **⚙️ Server Management**: Start, stop, and monitor astronomical servers
- **🔌 Plugin System**: Extensible architecture for custom functionality
- **📊 Configuration Management**: Centralized configuration for all connected software
- **📈 Real-time Monitoring**: Live status updates and system monitoring
- **🚀 Modern UI**: Built with PySide6 and Fluent Design principles
- **🔒 Security**: Comprehensive security scanning and vulnerability management
- **📦 Easy Distribution**: Multiple package formats for each platform

## 🚀 Quick Start

### 📥 Download

**Latest Release**: [Download from GitHub Releases](https://github.com/ElementAstro/HEAL/releases/latest)

Choose the appropriate package for your operating system:

| Platform | Package Types | Description |
|----------|---------------|-------------|
| **Windows** | `.zip`, `.msi` | Portable version or Windows installer |
| **macOS** | `.zip`, `.dmg` | Portable version or macOS disk image |
| **Linux** | `.tar.gz`, `.AppImage`, `.deb` | Portable, universal, or Debian package |

### 🛠️ Installation

#### Windows
```powershell
# Using PowerShell installer
.\install.ps1

# Or extract ZIP and run
HEAL.exe
```

#### macOS
```bash
# Using installer script
chmod +x install.sh
./install.sh

# Or run directly
./HEAL.app/Contents/MacOS/HEAL
```

#### Linux
```bash
# Using installer script
chmod +x install.sh
./install.sh

# Or run directly
./HEAL
```

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

## 🏗️ Development

### Prerequisites

- **Python 3.11+** (recommended 3.11 or 3.12)
- **Git** for version control
- **Virtual environment** support

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ElementAstro/HEAL.git
   cd HEAL
   ```

2. **Set up development environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate  # Unix/macOS
   venv\Scripts\activate.bat  # Windows
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

4. **Run tests**:
   ```bash
   # Run all tests
   python -m pytest tests/ -v
   
   # Run with coverage
   python -m pytest tests/ --cov=src --cov-report=html
   ```

### Building from Source

```bash
# Standard build
python scripts/build.py

# Debug build with verbose output
python scripts/build.py --debug --verbose

# Build with tests
python scripts/build.py --test

# Build specific package format
python scripts/build.py --package-format zip
```

For comprehensive build instructions, see [docs/cross-platform-guide.md](docs/cross-platform-guide.md).

## 📁 Project Structure

```
HEAL/
├── 📂 src/heal/              # Main application source code
│   ├── 📂 components/        # UI components and widgets
│   ├── 📂 core/             # Core application logic
│   ├── 📂 plugins/          # Plugin system
│   ├── 📂 resources/        # Images, styles, translations
│   └── 📂 utils/            # Utility functions
├── 📂 config/               # Configuration files and templates
├── 📂 scripts/              # Build, deployment, and utility scripts
│   ├── 📄 build.py          # Cross-platform build script
│   ├── 📄 security_scanner.py # Security analysis tools
│   └── 📄 release_manager.py  # Release management
├── 📂 tests/                # Comprehensive test suite
├── 📂 docs/                 # Documentation
│   ├── 📄 cross-platform-guide.md
│   ├── 📄 troubleshooting-guide.md
│   ├── 📄 deployment-guide.md
│   └── 📄 security-guide.md
├── 📂 .github/workflows/    # CI/CD pipelines
├── 📄 requirements.txt      # Production dependencies
├── 📄 requirements-dev.txt  # Development dependencies
├── 📄 requirements-build.txt # Build dependencies
└── 📄 pyproject.toml       # Project configuration
```

## 🔧 Configuration

HEAL uses a hierarchical configuration system:

1. **Default configuration**: Built-in defaults
2. **System configuration**: System-wide settings
3. **User configuration**: User-specific settings
4. **Runtime configuration**: Command-line overrides

Configuration files are located in platform-appropriate directories:
- **Windows**: `%LOCALAPPDATA%\HEAL\config\`
- **macOS**: `~/Library/Application Support/HEAL/config/`
- **Linux**: `~/.config/heal/`

## 🧪 Testing

### Automated Testing

The project includes comprehensive automated testing:

- **Unit Tests**: Component-level testing
- **Integration Tests**: Cross-component testing
- **GUI Tests**: User interface testing
- **Cross-Platform Tests**: Platform-specific functionality
- **Security Tests**: Vulnerability and security scanning
- **Performance Tests**: Benchmarking and profiling

### CI/CD Pipeline

- **Continuous Integration**: Automated testing on every push
- **Cross-Platform Builds**: Windows, macOS, and Linux
- **Security Scanning**: Daily vulnerability assessments
- **Automated Releases**: Tagged releases with artifacts
- **Quality Gates**: Code quality and security requirements

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](INSTALL.md) | Detailed installation instructions |
| [Cross-Platform Guide](docs/cross-platform-guide.md) | Development and deployment across platforms |
| [Troubleshooting Guide](docs/troubleshooting-guide.md) | Common issues and solutions |
| [Deployment Guide](docs/deployment-guide.md) | Enterprise and cloud deployment |
| [Security Guide](docs/security-guide.md) | Security practices and scanning |
| [Release Guide](docs/release-guide.md) | Release process and version management |
| [CI/CD Guide](docs/ci-cd-guide.md) | Build system and automation |

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Ways to Contribute

- 🐛 **Bug Reports**: Report issues and bugs
- 💡 **Feature Requests**: Suggest new features
- 🔧 **Code Contributions**: Submit pull requests
- 📖 **Documentation**: Improve documentation
- 🧪 **Testing**: Help test new features
- 🌐 **Translations**: Localize the application

### Development Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please read our [Contributing Guidelines](CONTRIBUTING.md) for detailed information.

### Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Community Support

- **🐛 Issues**: [GitHub Issues](https://github.com/ElementAstro/HEAL/issues) - Bug reports and feature requests
- **💬 Discussions**: [GitHub Discussions](https://github.com/ElementAstro/HEAL/discussions) - General questions and community support
- **💬 Discord**: [Join our Discord](https://discord.gg/elementastro) - Real-time chat and support
- **📧 Email**: astro_air@126.com - Direct contact for sensitive issues

### Professional Support

- **🏢 Enterprise Support**: Commercial support and consulting available
- **🎓 Training**: On-site or remote training sessions
- **🔧 Custom Development**: Tailored solutions and integrations

## 🏆 Acknowledgments

- **ElementAstro Team** for core development and vision
- **Contributors** and community members for their valuable input
- **Open Source Community** for the amazing libraries and frameworks
- **Astronomical Community** for feedback and feature requests

## 📊 Project Status

- **Development Status**: Active development
- **Stability**: Beta (approaching stable release)
- **Platform Support**: Windows ✅ | macOS ✅ | Linux ✅
- **Python Support**: 3.11+ ✅
- **Security**: Regular security scans and updates ✅
- **Documentation**: Comprehensive and up-to-date ✅

---

<div align="center">

**[⬆ Back to Top](#heal---hello-elementastro-launcher)**

Made with ❤️ by the ElementAstro team

</div>
