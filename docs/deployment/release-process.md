# Release Guide

This guide describes the release process for the HEAL project, including version management, changelog generation, and automated distribution.

## Release Process Overview

The HEAL project uses an automated release process with the following components:

1. **Version Management**: Automatic versioning with setuptools-scm
2. **Changelog Generation**: Automated changelog updates
3. **Multi-Platform Builds**: Cross-platform executable creation
4. **Package Distribution**: Multiple package formats per platform
5. **GitHub Releases**: Automated release creation with artifacts

## Release Types

### Patch Release (1.0.0 → 1.0.1)

- Bug fixes
- Security patches
- Documentation updates
- Minor improvements

### Minor Release (1.0.0 → 1.1.0)

- New features
- API additions (backward compatible)
- Significant improvements
- New platform support

### Major Release (1.0.0 → 2.0.0)

- Breaking changes
- Major architectural changes
- API removals or changes
- Significant feature overhauls

## Automated Release Process

### 1. Triggering a Release

Releases are automatically triggered by creating and pushing a git tag:

```bash
# Create and push a tag
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3
```

### 2. Automated Workflow

When a tag is pushed, the GitHub Actions workflow automatically:

1. **Runs Tests**: Full test suite across all platforms
2. **Builds Executables**: Creates platform-specific executables
3. **Creates Packages**: Generates distribution packages
4. **Uploads Artifacts**: Stores build artifacts
5. **Creates Release**: Publishes GitHub release with artifacts
6. **Generates Changelog**: Updates release notes

### 3. Release Artifacts

Each release includes the following artifacts:

#### Windows

- `HEAL-windows-x64.zip` - Portable version
- `HEAL-windows-x64.msi` - Windows installer (if WiX available)

#### macOS

- `HEAL-macos-x64.zip` - Portable version
- `HEAL-macos-x64.dmg` - macOS disk image (if tools available)

#### Linux

- `HEAL-linux-x64.tar.gz` - Portable version
- `HEAL-linux-x64.AppImage` - Universal Linux application
- `HEAL-linux-x64.deb` - Debian/Ubuntu package

## Manual Release Process

### Using the Release Manager Script

The project includes a release manager script for manual release preparation:

```bash
# Check current version
python scripts/release_manager.py version

# List existing releases
python scripts/release_manager.py list

# Prepare a patch release
python scripts/release_manager.py prepare --bump patch

# Prepare a minor release
python scripts/release_manager.py prepare --bump minor

# Prepare a major release
python scripts/release_manager.py prepare --bump major

# Dry run (preview changes)
python scripts/release_manager.py prepare --bump patch --dry-run
```

### Manual Steps

1. **Prepare the Release**:

   ```bash
   # Update version and changelog
   python scripts/release_manager.py prepare --bump minor
   ```

2. **Review Changes**:
   - Check the generated changelog entry
   - Verify version bump is correct
   - Review any uncommitted changes

3. **Push the Release**:

   ```bash
   # Push changes and tag
   git push origin main
   git push origin v1.2.3
   ```

4. **Monitor the Build**:
   - Watch the GitHub Actions workflow
   - Verify all platforms build successfully
   - Check that artifacts are uploaded

## Version Management

### Automatic Versioning

The project uses setuptools-scm for automatic version management:

- **Development versions**: `1.2.3.dev4+g1234567` (based on commits since last tag)
- **Release versions**: `1.2.3` (exact tag match)
- **Dirty versions**: `1.2.3.dev4+g1234567.d20240101` (uncommitted changes)

### Version Configuration

Version settings in `pyproject.toml`:

```toml
[tool.setuptools_scm]
write_to = "src/heal/_version.py"
version_scheme = "post-release"
local_scheme = "dirty-tag"
fallback_version = "0.0.0"
```

## Changelog Management

### Automatic Generation

The release manager automatically generates changelog entries based on:

- **Commit messages**: Categorized by keywords
- **Time range**: Changes since the last tag
- **Format**: Follows Keep a Changelog format

### Commit Message Conventions

For better changelog generation, use these prefixes:

- `feat:` or `feature:` - New features
- `fix:` or `bug:` - Bug fixes
- `docs:` or `doc:` - Documentation changes
- `perf:` - Performance improvements
- `refactor:` - Code refactoring
- `test:` - Test additions or changes
- `chore:` - Maintenance tasks

### Manual Changelog Editing

You can manually edit `CHANGELOG.md` before creating a release:

1. Update the `[Unreleased]` section
2. Add detailed descriptions for major changes
3. Include breaking change notices
4. Add migration guides if needed

## Release Validation

### Pre-Release Checklist

Before creating a release:

- [ ] All tests pass on all platforms
- [ ] Documentation is up to date
- [ ] Breaking changes are documented
- [ ] Migration guides are provided (if needed)
- [ ] Security vulnerabilities are addressed
- [ ] Performance regressions are investigated

### Post-Release Validation

After a release is created:

- [ ] Download and test artifacts from each platform
- [ ] Verify installation instructions work
- [ ] Check that the release appears in GitHub
- [ ] Monitor for user feedback and issues
- [ ] Update documentation if needed

## Hotfix Process

For critical bug fixes that need immediate release:

1. **Create Hotfix Branch**:

   ```bash
   git checkout -b hotfix/1.2.4 v1.2.3
   ```

2. **Apply Fix**:

   ```bash
   # Make necessary changes
   git commit -m "fix: critical security vulnerability"
   ```

3. **Create Hotfix Release**:

   ```bash
   python scripts/release_manager.py prepare --bump patch
   git push origin hotfix/1.2.4
   git push origin v1.2.4
   ```

4. **Merge Back**:

   ```bash
   git checkout main
   git merge hotfix/1.2.4
   git push origin main
   ```

## Rollback Process

If a release has critical issues:

1. **Create Rollback Tag**:

   ```bash
   git tag -d v1.2.3  # Delete locally
   git push origin :refs/tags/v1.2.3  # Delete remotely
   ```

2. **Delete GitHub Release**:
   - Go to GitHub Releases page
   - Delete the problematic release
   - Remove associated artifacts

3. **Create Fixed Release**:

   ```bash
   # Fix issues and create new release
   python scripts/release_manager.py prepare --bump patch
   ```

## Troubleshooting

### Common Issues

1. **Build Failure on Specific Platform**:
   - Check platform-specific dependencies
   - Review build logs in GitHub Actions
   - Test locally with the same environment

2. **Package Creation Failure**:
   - Verify platform-specific tools are available
   - Check fallback to basic packaging formats
   - Review error messages in build logs

3. **Version Conflicts**:
   - Ensure setuptools-scm is properly configured
   - Check that git tags are properly formatted
   - Verify working directory is clean

4. **Changelog Generation Issues**:
   - Check git log format and commit messages
   - Verify tag history is correct
   - Manually edit changelog if needed

### Getting Help

- Check the [CI/CD Guide](ci-cd-guide.md) for build system details
- Review GitHub Actions workflow logs
- Open an issue for release process problems
- Contact maintainers for urgent release issues

## Best Practices

1. **Regular Releases**: Release frequently with smaller changes
2. **Semantic Versioning**: Follow semver strictly for version numbers
3. **Clear Commit Messages**: Use conventional commit format
4. **Comprehensive Testing**: Ensure all platforms are tested
5. **Documentation**: Keep documentation in sync with releases
6. **Communication**: Announce releases to users and contributors
7. **Monitoring**: Watch for issues after releases
8. **Feedback**: Collect and respond to user feedback
