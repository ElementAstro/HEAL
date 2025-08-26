# HEAL Project Structure Quick Reference

## Directory Structure

```
HEAL/
├── src/heal/                    # Main package
│   ├── common/                  # Shared utilities
│   ├── components/              # UI components
│   ├── interfaces/              # Interface modules
│   ├── models/                  # Data models
│   └── resources/               # Static resources
├── tests/                       # Test suite
├── docs/                        # Documentation
├── scripts/                     # Development scripts
├── tools/                       # Development tools
├── config/                      # Configuration files
├── main.py                      # Entry point
└── pyproject.toml              # Project configuration
```

## Import Patterns

### Within Package (Relative Imports)

```python
# From interfaces to other packages
from ..common.logging_config import get_logger
from ..models.config import cfg
from ..components.main import WindowManager

# Within same package
from .module_manager import ModuleManager
```

### External Imports (Absolute)

```python
# From main.py or external scripts
from src.heal.common.logging_config import get_logger
from src.heal.models.config import cfg
from src.heal.interfaces.main_interface import Main
```

## Resource Paths

### Old → New Path Mappings

```python
# Stylesheets
"./src/qss/" → "./src/heal/resources/styles/"

# Images
"src\\image\\" → "src\\heal\\resources\\images\\"

# Icons
"icons/" → "src/heal/resources/app_icons/"

# Translations
"src/translate/" → "src/heal/resources/translations/"

# Data files
"src/data/" → "src/heal/resources/data/"
```

### Resource Access

```python
from src.heal.resources import get_resource_path, IMAGES_DIR

# Get resource path
icon_path = get_resource_path('images', 'icon.ico')

# Direct path access
image_dir = IMAGES_DIR
```

## Development Commands

### Setup Development Environment

```bash
python scripts/setup_dev.py
```

### Build Application

```bash
# Modern Python build
python scripts/build.py

# Legacy batch build
build.bat
```

### Run Application

```bash
python main.py
```

### Run Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Sort imports
isort src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## Package Structure

### Main Components

- **common/**: Shared utilities, logging, i18n, configuration
- **components/**: Modular UI components organized by feature
- **interfaces/**: Main interface modules (formerly *_interface.py)
- **models/**: Data models, configuration, business logic
- **resources/**: All static assets and resources

### Component Organization

```
components/
├── core/           # Core components
├── download/       # Download interface components
├── environment/    # Environment management
├── home/           # Home interface components
├── launcher/       # Launcher components
├── logging/        # Logging components
├── main/           # Main window components
├── module/         # Module management
├── proxy/          # Proxy components
├── setting/        # Settings components
├── tools/          # Tool components
└── utils/          # Utility components
```

## Configuration Files

### pyproject.toml

- Project metadata and dependencies
- Build system configuration
- Tool configurations (black, isort, mypy, pytest)

### Requirements Files

- **requirements.txt**: Runtime dependencies
- **requirements-dev.txt**: Development dependencies
- **requirements-build.txt**: Build dependencies

## Migration Checklist

### For Existing Code

- [ ] Update import statements (`app.` → `src.heal.` or relative)
- [ ] Update resource paths (see mappings above)
- [ ] Test functionality after changes
- [ ] Update any custom scripts or tools

### For New Development

- [ ] Use relative imports within package
- [ ] Use resource utilities for asset access
- [ ] Follow new directory structure
- [ ] Add proper **init**.py files for new packages

## Common Issues and Solutions

### Import Errors

```python
# Problem: ModuleNotFoundError for app.*
from app.common.logging_config import get_logger

# Solution: Update to new structure
from ..common.logging_config import get_logger  # Relative
# or
from src.heal.common.logging_config import get_logger  # Absolute
```

### Resource Not Found

```python
# Problem: File not found for old paths
icon_path = "src/image/icon.ico"

# Solution: Use new resource structure
from src.heal.resources import get_resource_path
icon_path = get_resource_path('images', 'icon.ico')
```

### Build Issues

```python
# Problem: PyInstaller can't find resources
# Solution: Use updated build script
python scripts/build.py
```

## Useful Scripts

### Update Imports (Automated)

```bash
python scripts/update_imports.py
```

### Quality Assurance

```bash
python scripts/quality_assurance.py
```

### I18n Checking

```bash
python tools/i18n_checker.py
```

## Documentation

- **PACKAGE_STRUCTURE_MIGRATION.md**: Detailed migration guide
- **RESTRUCTURING_SUMMARY.md**: Complete summary of changes
- **migration_guide.md**: Modular architecture migration (existing)

## Support

For questions or issues:

1. Check the migration documentation
2. Review the quick reference (this document)
3. Create an issue in the project repository
4. Consult the developer team
