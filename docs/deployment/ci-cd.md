# CI/CD and Build System Guide

This document describes the continuous integration, continuous deployment, and build system for the HEAL project.

## Overview

The HEAL project uses GitHub Actions for CI/CD with a comprehensive multi-platform build and testing pipeline.

## Workflows

### 1. Continuous Integration (`ci.yml`)

**Triggers:**

- Push to main, develop, or feature branches
- Pull requests to main or develop
- Daily scheduled runs at 2 AM UTC
- Manual dispatch

**Jobs:**

- **Quality**: Code formatting, linting, type checking, security scanning
- **Test**: Cross-platform testing on Ubuntu, Windows, macOS with Python 3.11, 3.12, 3.13-dev
- **Performance**: Benchmark testing (scheduled or on-demand)
- **Docs**: Documentation build verification
- **Security**: Dependency vulnerability scanning
- **Build Test**: Quick build verification without packaging

### 2. Build and Release (`build-and-release.yml`)

**Triggers:**

- Push to main or develop branches
- Tags starting with 'v'
- Pull requests to main or develop
- Manual dispatch with release option

**Jobs:**

- **Test**: Multi-platform testing (prerequisite)
- **Build**: Cross-platform executable creation and packaging
- **Release**: Automated GitHub release creation for tags

### 3. Cache Cleanup (`cache-cleanup.yml`)

**Triggers:**

- Weekly schedule (Sundays at 3 AM UTC)
- Manual dispatch

**Purpose:**

- Clean up old build artifacts
- Manage cache storage

## Caching Strategy

### Dependency Caching

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

**Benefits:**

- Reduces build time by 60-80%
- Saves bandwidth and GitHub Actions minutes
- Improves reliability by reducing external dependency failures

### Build Artifact Caching

**Artifacts are cached for:**

- Build outputs: 30 days
- Test reports: 30 days
- Security reports: 30 days
- Documentation: 30 days
- Benchmark results: 30 days
- Build logs (on failure): 7 days

### Cache Keys

Cache keys are generated based on:

- Operating system (`${{ runner.os }}`)
- Dependency file hashes (`${{ hashFiles('**/requirements*.txt') }}`)
- Python version (when relevant)

## Build Matrix

### Testing Matrix

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: ['3.11', '3.12']
    include:
      - os: ubuntu-latest
        python-version: '3.13-dev'
```

### Build Matrix

```yaml
strategy:
  fail-fast: false
  matrix:
    include:
      - os: windows-latest
        platform: windows
        package_formats: "zip,msi"
      - os: macos-latest
        platform: macos
        package_formats: "zip,dmg"
      - os: ubuntu-latest
        platform: linux
        package_formats: "tar.gz,appimage,deb"
```

## Package Formats

### Windows

- **ZIP**: Portable archive
- **MSI**: Windows installer (requires WiX Toolset)

### macOS

- **ZIP**: Portable archive
- **DMG**: macOS disk image

### Linux

- **TAR.GZ**: Portable archive
- **AppImage**: Universal Linux application
- **DEB**: Debian/Ubuntu package

## Environment Variables

### Global Variables

- `APP_NAME`: Application name (HEAL)
- `PYTHON_VERSION`: Default Python version (3.11)

### Platform-Specific Variables

- `PYTHONPATH`: Set to workspace for imports
- `DISPLAY`: Virtual display for Linux GUI testing
- `QT_QPA_PLATFORM`: Qt platform for headless testing

## Secrets and Security

### Required Secrets

- `GITHUB_TOKEN`: Automatically provided by GitHub
- `CODECOV_TOKEN`: For coverage reporting (optional)

### Security Measures

- Dependency vulnerability scanning with `safety` and `pip-audit`
- Code security scanning with `bandit`
- Automated security report generation
- Regular dependency updates

## Performance Optimizations

### Build Time Optimizations

1. **Parallel Jobs**: Multiple jobs run concurrently
2. **Dependency Caching**: Pip cache reduces installation time
3. **Fail-Fast Disabled**: Continue testing other platforms if one fails
4. **Conditional Steps**: Platform-specific steps only run when needed

### Resource Usage

- **CPU**: Utilizes GitHub's multi-core runners efficiently
- **Memory**: Optimized for 7GB RAM limit
- **Storage**: Efficient artifact management with automatic cleanup
- **Network**: Cached dependencies reduce bandwidth usage

## Monitoring and Debugging

### Build Status

- Status badges in README.md
- Email notifications on failure
- Slack/Discord integration (configurable)

### Debugging Failed Builds

1. Check the workflow run logs
2. Download build artifacts for analysis
3. Use the manual workflow dispatch for testing
4. Enable debug logging with `ACTIONS_STEP_DEBUG=true`

### Log Artifacts

- Build logs uploaded on failure
- Test reports with detailed output
- Coverage reports with line-by-line analysis
- Security scan results

## Local Development

### Running CI Checks Locally

```bash
# Code quality checks
python scripts/dev_utils.py quality-check

# Run tests with coverage
python scripts/dev_utils.py test --coverage

# Build application
python scripts/build.py --test

# Security scan
pip install safety bandit
safety check
bandit -r src/
```

### Pre-commit Hooks

Install pre-commit hooks to run checks before committing:

```bash
pip install pre-commit
pre-commit install
```

## Troubleshooting

### Common Issues

1. **Cache Miss**: Dependencies reinstalled every time
   - Check if requirements files have changed
   - Verify cache key generation

2. **Build Failure on Specific Platform**
   - Check platform-specific dependencies
   - Review error logs in artifacts

3. **Test Failures**
   - GUI tests may fail without proper display setup
   - Check environment variables and dependencies

4. **Package Creation Failure**
   - Verify platform-specific tools are available
   - Check fallback to basic packaging formats

### Performance Issues

1. **Slow Builds**
   - Check cache hit rates
   - Review dependency installation logs
   - Consider reducing test matrix for development branches

2. **High Resource Usage**
   - Monitor memory usage in logs
   - Optimize test parallelization
   - Review artifact sizes

## Future Improvements

### Planned Enhancements

1. **Docker-based builds** for consistent environments
2. **Cross-compilation** to reduce build matrix
3. **Incremental builds** for faster development cycles
4. **Advanced caching** with build dependency tracking
5. **Performance regression detection** with benchmark comparisons

### Metrics and Analytics

- Build time tracking
- Success rate monitoring
- Resource usage analysis
- Dependency update impact assessment
