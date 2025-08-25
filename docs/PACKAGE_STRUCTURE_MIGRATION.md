# Package Structure Migration Guide

This document outlines the major changes made to reorganize the HEAL project structure to follow Python packaging best practices and standards.

## Overview

The project has been restructured to follow the **src-layout** pattern, which is considered a best practice for Python packages. This provides better separation of concerns, improved testability, and cleaner distribution.

## Major Changes

### 1. Directory Structure Changes

#### Before (Old Structure)
```
HEAL/
├── app/                    # Main application code
├── src/                    # Mixed resources and assets
├── tests/                  # Tests
├── docs/                   # Documentation
├── config/                 # Configuration files
├── main.py                 # Entry point
├── setup.py               # Legacy setup script
└── requirements.txt       # Dependencies
```

#### After (New Structure)
```
HEAL/
├── src/
│   └── heal/              # Main package
│       ├── __init__.py
│       ├── common/        # Shared utilities
│       ├── components/    # UI components
│       ├── interfaces/    # Interface modules
│       ├── models/        # Data models (renamed from 'model')
│       └── resources/     # All static resources
│           ├── data/
│           ├── images/
│           ├── icons/
│           ├── app_icons/
│           ├── styles/
│           ├── translations/
│           ├── patches/
│           └── warp/
├── tests/                 # Test suite
├── docs/                  # Documentation
│   ├── api/
│   ├── user-guide/
│   └── developer-guide/
├── scripts/               # Development scripts
├── tools/                 # Development tools
├── config/                # Configuration files
├── main.py               # Entry point
├── pyproject.toml        # Modern project configuration
├── requirements.txt      # Core dependencies
├── requirements-dev.txt  # Development dependencies
├── requirements-build.txt # Build dependencies
└── setup_legacy.py       # Renamed legacy setup script
```

### 2. Package Structure Changes

#### Main Package Reorganization
- **`app/` → `src/heal/`**: Main application code moved to proper package structure
- **`app/model/` → `src/heal/models/`**: Renamed to follow Python conventions
- **Interface files**: Moved to `src/heal/interfaces/` directory
- **Resources**: Consolidated under `src/heal/resources/`

#### Resource Organization
- **`src/qss/` → `src/heal/resources/styles/`**: Stylesheets
- **`src/image/` → `src/heal/resources/images/`**: Application images
- **`src/icon/` → `src/heal/resources/icons/`**: Code-related icons
- **`icons/` → `src/heal/resources/app_icons/`**: Application icons
- **`src/translate/` → `src/heal/resources/translations/`**: Translation files
- **`src/data/` → `src/heal/resources/data/`**: Data files
- **`src/patch/` → `src/heal/resources/patches/`**: Patch files
- **`src/warp/` → `src/heal/resources/warp/`**: Warp configuration

### 3. Configuration Changes

#### pyproject.toml (New)
- **PEP 518/621 compliant**: Modern Python project configuration
- **Build system**: Defined using setuptools
- **Dependencies**: Properly categorized (main, dev, test, docs)
- **Metadata**: Complete project information
- **Tool configurations**: Black, isort, mypy, pytest settings

#### Requirements Files
- **requirements.txt**: Core runtime dependencies
- **requirements-dev.txt**: Development dependencies
- **requirements-build.txt**: Build and packaging dependencies

### 4. Import Statement Changes

#### Before
```python
from app.common.logging_config import get_logger
from app.model.config import cfg
from app.components.main import WindowManager
```

#### After
```python
# From within the package (relative imports)
from ..common.logging_config import get_logger
from ..models.config import cfg
from ..components.main import WindowManager

# From outside the package (absolute imports)
from src.heal.common.logging_config import get_logger
from src.heal.models.config import cfg
from src.heal.components.main import WindowManager
```

### 5. Resource Path Changes

#### Before
```python
# Style sheets
f"./src/qss/{theme.value.lower()}/{self.value}.qss"

# Translations
Path("src/data/translations")

# Images
"src\\image\\icon.ico"
```

#### After
```python
# Style sheets
f"./src/heal/resources/styles/{theme.value.lower()}/{self.value}.qss"

# Translations
Path("src/heal/resources/data/translations")

# Images
"src\\heal\\resources\\images\\icon.ico"
```

## Migration Steps for Developers

### 1. Update Import Statements
- Replace `from app.` with `from src.heal.` for external imports
- Use relative imports within the package: `from ..common.` instead of `from app.common.`
- Update `app.model.` to `src.heal.models.`

### 2. Update Resource Paths
- Change `src/qss/` to `src/heal/resources/styles/`
- Change `src/image/` to `src/heal/resources/images/`
- Change `src/translate/` to `src/heal/resources/translations/`
- Update any hardcoded paths to use the new structure

### 3. Update Build Scripts
- Use the new `scripts/build.py` instead of `build.bat`
- Update PyInstaller configurations for new resource paths
- Use `requirements-build.txt` for build dependencies

### 4. Development Environment
- Run `python scripts/setup_dev.py` to set up the new development environment
- Use the new virtual environment structure
- Update IDE configurations for the new package structure

## Breaking Changes

### Import Changes
All imports from the `app` package need to be updated. This affects:
- Interface modules
- Component imports
- Model imports
- Common utility imports

### Resource Path Changes
Any code that references resource files directly needs path updates:
- QSS file loading
- Image file references
- Translation file paths
- Icon file paths

### Build Process Changes
- Old `build.bat` is updated for new structure
- New Python-based build script available
- PyInstaller configuration updated

## Benefits of New Structure

### 1. Standards Compliance
- Follows PEP 518/621 for modern Python packaging
- Uses src-layout pattern recommended by Python Packaging Authority
- Proper separation of source code and resources

### 2. Improved Development Experience
- Better IDE support and code navigation
- Cleaner import structure
- Enhanced testing capabilities

### 3. Better Distribution
- Proper package structure for PyPI distribution
- Clear separation of runtime and development dependencies
- Modern build system configuration

### 4. Maintainability
- Logical organization of components
- Clear resource management
- Better documentation structure

## Next Steps

1. **Update your development environment** using `scripts/setup_dev.py`
2. **Review and update any custom scripts** that reference the old structure
3. **Test the application** to ensure all functionality works correctly
4. **Update any documentation** that references the old structure

For questions or issues with the migration, please refer to the developer documentation or create an issue in the project repository.
