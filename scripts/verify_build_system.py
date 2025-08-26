#!/usr/bin/env python3
"""
Build system verification script for HEAL.
Verifies that all components of the cross-platform build system are properly integrated.
"""

import sys
import traceback
from pathlib import Path


def test_imports():
    """Test that all build system modules can be imported."""
    print("Testing module imports...")

    modules_to_test = [
        'logging_config',
        'platform_configs',
        'resource_bundler',
        'package_builders',
        'path_utils',
        'security_scanner',
        'release_manager'
    ]

    failed_imports = []

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name}")
        except ImportError as e:
            print(f"  ❌ {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
        except Exception as e:
            print(f"  ⚠️  {module_name}: {e}")
            failed_imports.append((module_name, str(e)))

    return failed_imports


def test_build_script():
    """Test that the build script can be imported and initialized."""
    print("\nTesting build script integration...")

    try:
        # Add scripts directory to path
        scripts_dir = Path(__file__).parent
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        # Test build script import
        import build
        print("  ✅ build.py imported successfully")

        # Test HEALBuilder initialization
        project_root = scripts_dir.parent
        builder = build.HEALBuilder(project_root, enable_debug=True)
        print("  ✅ HEALBuilder initialized successfully")

        # Test platform detection
        print(f"  ℹ️  Platform: {builder.platform}")
        print(f"  ℹ️  Architecture: {builder.architecture}")
        print(f"  ℹ️  Windows: {builder.is_windows}")
        print(f"  ℹ️  macOS: {builder.is_macos}")
        print(f"  ℹ️  Linux: {builder.is_linux}")

        return True

    except Exception as e:
        print(f"  ❌ Build script test failed: {e}")
        traceback.print_exc()
        return False


def test_logging_system():
    """Test the logging system."""
    print("\nTesting logging system...")

    try:
        from logging_config import setup_logging, log_operation

        # Test logger creation
        logger = setup_logging("test-logger", "DEBUG")
        print("  ✅ Logger created successfully")

        # Test logging operations
        logger.info("Test info message")
        logger.debug("Test debug message")
        print("  ✅ Logging operations work")

        # Test context manager
        with log_operation(logger, "test operation"):
            logger.info("Inside context manager")
        print("  ✅ Log context manager works")

        return True

    except Exception as e:
        print(f"  ❌ Logging system test failed: {e}")
        traceback.print_exc()
        return False


def test_platform_configs():
    """Test platform configuration system."""
    print("\nTesting platform configuration system...")

    try:
        from platform_configs import PlatformConfig

        project_root = Path(__file__).parent.parent
        config = PlatformConfig(project_root)

        # Test PyInstaller config
        pyinstaller_config = config.get_pyinstaller_config()
        print(
            f"  ✅ PyInstaller config generated: {len(pyinstaller_config)} keys")

        # Test Nuitka config
        nuitka_config = config.get_nuitka_config()
        print(f"  ✅ Nuitka config generated: {len(nuitka_config)} args")

        # Test resource paths
        resource_paths = config.get_resource_paths()
        print(f"  ✅ Resource paths generated: {len(resource_paths)} paths")

        return True

    except Exception as e:
        print(f"  ❌ Platform config test failed: {e}")
        traceback.print_exc()
        return False


def test_path_utils():
    """Test cross-platform path utilities."""
    print("\nTesting path utilities...")

    try:
        from path_utils import CrossPlatformPaths, get_executable_name

        project_root = Path(__file__).parent.parent
        paths = CrossPlatformPaths(project_root)

        # Test platform detection
        platform_info = paths.get_platform_info()
        print(f"  ✅ Platform info: {platform_info['system']}")

        # Test executable name
        exe_name = get_executable_name("HEAL")
        print(f"  ✅ Executable name: {exe_name}")

        # Test config directory
        config_dir = paths.get_user_config_dir()
        print(f"  ✅ Config directory: {config_dir}")

        return True

    except Exception as e:
        print(f"  ❌ Path utils test failed: {e}")
        traceback.print_exc()
        return False


def test_file_structure():
    """Test that required files and directories exist."""
    print("\nTesting file structure...")

    project_root = Path(__file__).parent.parent

    required_files = [
        'main.py',
        'pyproject.toml',
        'requirements.txt',
        'requirements-dev.txt',
        'requirements-build.txt',
        'INSTALL.md',
        'CHANGELOG.md',
        'README_EN.md',
        'install.sh',
        'install.ps1',
    ]

    required_dirs = [
        'src/heal',
        'scripts',
        'docs',
        '.github/workflows',
    ]

    missing_files = []
    missing_dirs = []

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/")
            missing_dirs.append(dir_path)

    return len(missing_files) == 0 and len(missing_dirs) == 0


def main():
    """Run all verification tests."""
    print("HEAL Build System Verification")
    print("=" * 50)

    tests = [
        ("Module Imports", test_imports),
        ("Build Script", test_build_script),
        ("Logging System", test_logging_system),
        ("Platform Configs", test_platform_configs),
        ("Path Utils", test_path_utils),
        ("File Structure", test_file_structure),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))

        try:
            if test_name == "Module Imports":
                failed_imports = test_func()
                success = len(failed_imports) == 0
                if not success:
                    print(f"\nFailed imports: {failed_imports}")
            else:
                success = test_func()

            results.append((test_name, success))

        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if success:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All verification tests passed! Build system is ready.")
        return 0
    else:
        print("⚠️  Some verification tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
