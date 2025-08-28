# HEAL - Hello ElementAstro Launcher

<div align="center">

![HEAL Logo](https://github.com/ElementAstro/HEAL/assets/77842352/2118e3a4-afa0-4683-9a1a-ca11084851a7)

**A comprehensive launcher and management system for astronomical software**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-GUI-green.svg)](https://doc.qt.io/qtforpython/)
[![GitHub release](https://img.shields.io/github/release/ElementAstro/HEAL.svg)](https://github.com/ElementAstro/HEAL/releases)
[![GitHub issues](https://img.shields.io/github/issues/ElementAstro/HEAL.svg)](https://github.com/ElementAstro/HEAL/issues)
[![GitHub stars](https://img.shields.io/github/stars/ElementAstro/HEAL.svg)](https://github.com/ElementAstro/HEAL/stargazers)

[English](README_EN.md) | [中文](README.md)

</div>

---

## 📖 Overview

HEAL (Hello ElementAstro Launcher) is a modern, feature-rich GUI launcher built on top of FireflyLauncher. It provides a comprehensive solution for managing and launching various astronomical software applications with an intuitive interface and powerful configuration system.

### ✨ Key Features

- 🚀 **Universal Launcher**: Support for multiple astronomical software types
- 🎨 **Modern UI**: Built with PySide6 and Fluent Design principles
- ⚙️ **Advanced Configuration**: Flexible configuration system with JSON schemas
- 🔧 **Proxy Management**: Built-in proxy support for network tools
- 📦 **Package Management**: Integrated download and installation system
- 🌐 **Multi-language**: Support for multiple languages
- 🔒 **Security**: Built-in security scanning and validation
- 📊 **Performance Monitoring**: Real-time performance tracking

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Windows, macOS, or Linux
- 4GB RAM minimum (8GB recommended)

### Installation

#### Option 1: Pre-built Releases (Recommended)

Download the latest stable release for your operating system:

[![Download Latest Release](https://img.shields.io/badge/Download-Latest%20Release-blue?style=for-the-badge)](https://github.com/ElementAstro/HEAL/releases/latest)

#### Option 2: Development Builds

For the latest features and bug fixes, download development builds from [GitHub Actions](https://github.com/ElementAstro/HEAL/actions/).

#### Option 3: Build from Source

```bash
# Clone the repository
git clone https://github.com/ElementAstro/HEAL.git
cd HEAL

# Set up development environment
python scripts/setup_dev.py

# Build the application
python scripts/build.py

# Alternative: Use batch script (Windows)
build.bat
```

### 🎯 Quick Setup

1. **Install Required Fonts**: Download and install the [Chinese font package](https://github.com/ElementAstro/HEAL/releases/download/v1.2.0/zh-cn.ttf) for proper text rendering.

2. **Configure Settings**:
   - Open HEAL → Settings → Configuration → Open Config File
   - Modify proxy ports, server names, and commands as needed
   - Default configuration: [config.json](https://github.com/ElementAstro/HEAL/blob/main/config/config.json)

3. **Set Up Proxy** (Optional):
   - Navigate to Settings → Proxy
   - Configure proxy settings based on your network requirements

## 📁 Project Structure

HEAL follows modern Python packaging standards (PEP 518/621) with a clean, modular architecture:

```text
HEAL/
├── src/heal/              # Main package
│   ├── common/            # Shared utilities and helpers
│   ├── components/        # Reusable UI components
│   ├── interfaces/        # Interface modules and definitions
│   ├── models/            # Data models and schemas
│   └── resources/         # Static resources (images, styles, translations)
├── tests/                 # Comprehensive test suite
├── docs/                  # Documentation and guides
├── scripts/               # Development and build scripts
├── config/                # Configuration files and schemas
├── main.py               # Application entry point
└── pyproject.toml        # Project configuration and dependencies
```

## 🎮 Usage

### Basic Operation

1. **Launch Application**: Run HEAL and select your preferred server configuration
2. **One-Click Start**: Click the launch button to start your astronomical software
3. **Proxy Management** (Optional): For tools requiring proxy (Fiddler, Mitmdump):
   - Navigate to Settings → Proxy
   - Select and enable the appropriate proxy software
4. **Clean Shutdown** (Optional): Use Settings → Proxy → Reset Proxy to clean up proxy settings

### Advanced Features

- **Custom Configurations**: Create and manage multiple server configurations
- **Download Manager**: Built-in download system for supported software
- **Performance Monitoring**: Real-time system performance tracking
- **Multi-language Support**: Switch between supported languages in settings

## 📚 Documentation

- **Quick Reference**: [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)
- **Migration Guide**: [docs/PACKAGE_STRUCTURE_MIGRATION.md](docs/PACKAGE_STRUCTURE_MIGRATION.md)
- **Restructuring Summary**: [docs/RESTRUCTURING_SUMMARY.md](docs/RESTRUCTURING_SUMMARY.md)
- **Developer Guide**: [docs/developer-guide/](docs/developer-guide/)
- **User Guide**: [docs/user-guide/](docs/user-guide/)

## 🛠️ Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/ElementAstro/HEAL.git
cd HEAL

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with development settings
python main.py
```

### Development Tools

- **Code Formatting**: Black, isort
- **Type Checking**: mypy
- **Linting**: flake8
- **Testing**: pytest with coverage
- **Documentation**: Sphinx

### Building

```bash
# Build for current platform
python scripts/build.py

# Build for specific platform
python scripts/build.py --platform windows
python scripts/build.py --platform macos
python scripts/build.py --platform linux
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built upon [FireflyLauncher](https://github.com/ElementAstro/FireflyLauncher)
- UI framework: [PySide6](https://doc.qt.io/qtforpython/)
- Design system: [PySide6-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ElementAstro/HEAL/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ElementAstro/HEAL/discussions)
- **Email**: astro_air@126.com

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ElementAstro/HEAL&type=Date)](https://star-history.com/#ElementAstro/HEAL&Date)

---

<div align="center">

**Made with ❤️ by the ElementAstro Team**

</div>
