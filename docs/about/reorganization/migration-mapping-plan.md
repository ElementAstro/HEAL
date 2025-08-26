# Documentation Migration Mapping Plan

This document provides a detailed mapping of how existing documentation files will be moved to the new organizational structure.

## Migration Strategy

### Phase 1: Direct Migrations (Minimal Changes)

Files that can be moved directly with minimal content changes.

### Phase 2: Consolidations (Multiple → Single)

Multiple related files that will be merged into single comprehensive documents.

### Phase 3: New Content Creation

New files that need to be created to fill identified gaps.

### Phase 4: Link Updates

Update all references and cross-links after migration.

## Detailed Migration Mapping

### Phase 1: Direct Migrations

#### User Guide Section

| Current File | New Location | Rename Required | Content Changes |
|--------------|--------------|-----------------|-----------------|
| `troubleshooting-guide.md` | `user-guide/troubleshooting.md` | No | Minimal formatting |
| `I18N_GUIDE.md` | `user-guide/internationalization.md` | Yes | Standardize headers |
| `module_interface_user_guide.md` | `user-guide/interface-guide.md` | Yes | Update cross-references |

#### Developer Guide Section

| Current File | New Location | Rename Required | Content Changes |
|--------------|--------------|-----------------|-----------------|
| `modular_architecture_guide.md` | `developer-guide/architecture/overview.md` | Yes | Add navigation links |
| `component_development_guide.md` | `developer-guide/architecture/components.md` | Yes | Update examples |
| `migration_guide.md` | `developer-guide/architecture/migration.md` | No | Add cross-references |
| `module_interface_api.md` | `developer-guide/api-reference/module-interface.md` | Yes | Standardize format |
| `QUICK_REFERENCE.md` | `developer-guide/api-reference/quick-reference.md` | Yes | Update structure |

#### Deployment Section

| Current File | New Location | Rename Required | Content Changes |
|--------------|--------------|-----------------|-----------------|
| `deployment-guide.md` | `deployment/deployment-guide.md` | No | Update links |
| `cross-platform-guide.md` | `deployment/cross-platform.md` | Yes | Standardize format |
| `ci-cd-guide.md` | `deployment/ci-cd.md` | Yes | Update references |
| `security-guide.md` | `deployment/security.md` | Yes | Add cross-links |
| `release-guide.md` | `deployment/release-process.md` | Yes | Update procedures |

### Phase 2: Consolidations

#### Logging System Documentation

**Target File:** `developer-guide/systems/logging.md`

**Source Files to Merge:**

1. `complete_logging_integration_guide.md` - Integration instructions
2. `unified_logging_system_guide.md` - System overview
3. `logging_system_optimization.md` - Optimization details

**Consolidation Plan:**

```markdown
# Logging System Guide

## Overview (from unified_logging_system_guide.md)
- System architecture
- Key components
- Design principles

## Integration (from complete_logging_integration_guide.md)
- Setup instructions
- Configuration options
- Implementation examples

## Optimization (from logging_system_optimization.md)
- Performance considerations
- Best practices
- Advanced configuration

## API Reference
- Logger classes
- Configuration methods
- Utility functions
```

#### Settings System Documentation

**Target File:** `developer-guide/systems/settings.md`

**Source Files to Merge:**

1. `settings_optimization_summary.md` - Layout optimization
2. `settings_performance_optimization_summary.md` - Performance optimization
3. `settings_search_functionality_summary.md` - Search functionality

**Consolidation Plan:**

```markdown
# Settings System Guide

## Architecture Overview
- Settings system design
- Component organization
- Data flow

## User Interface (from settings_optimization_summary.md)
- Layout optimization
- User experience improvements
- Information architecture

## Performance (from settings_performance_optimization_summary.md)
- Caching system
- Lazy loading
- Performance metrics

## Search Functionality (from settings_search_functionality_summary.md)
- Search implementation
- Indexing strategy
- User interface
```

#### Project History Documentation

**Target File:** `about/project-history.md`

**Source Files to Merge:**

1. `final_completion_report.md` - Project completion status
2. `implementation-summary.md` - Implementation overview
3. `refactoring_project_summary.md` - Refactoring summary
4. `RESTRUCTURING_SUMMARY.md` - Restructuring details
5. `OPTIMIZATION_SUMMARY.md` - Optimization changes
6. `PACKAGE_STRUCTURE_MIGRATION.md` - Package migration

**Consolidation Plan:**

```markdown
# HEAL Project History

## Project Evolution Timeline
- Initial development
- Major milestones
- Recent improvements

## Architecture Evolution (from RESTRUCTURING_SUMMARY.md, OPTIMIZATION_SUMMARY.md)
- Original architecture
- Restructuring decisions
- Optimization improvements

## Implementation Milestones (from implementation-summary.md, final_completion_report.md)
- Cross-platform packaging
- Component modularization
- Feature completions

## Migration History (from PACKAGE_STRUCTURE_MIGRATION.md, refactoring_project_summary.md)
- Package structure changes
- Code refactoring efforts
- Migration procedures
```

### Phase 3: New Content Creation

#### Getting Started Section

| New File | Purpose | Content Source |
|----------|---------|----------------|
| `getting-started/README.md` | Section index | Create new |
| `getting-started/installation.md` | Installation guide | Extract from existing guides |
| `getting-started/quick-start.md` | 5-minute quick start | Create new |
| `getting-started/first-steps.md` | Basic usage tutorial | Create new |
| `getting-started/configuration.md` | Basic configuration | Extract from settings docs |

#### Main Documentation Files

| New File | Purpose | Content Source |
|----------|---------|----------------|
| `docs/README.md` | Main documentation index | Create new |
| `docs/CONTRIBUTING.md` | Contribution guidelines | Create new |
| `docs/CODE_OF_CONDUCT.md` | Community guidelines | Create new |
| `docs/CHANGELOG.md` | Version history | Create new |

#### Section Index Files

| New File | Purpose |
|----------|---------|
| `user-guide/README.md` | User guide navigation |
| `developer-guide/README.md` | Developer guide navigation |
| `developer-guide/architecture/README.md` | Architecture section index |
| `developer-guide/api-reference/README.md` | API reference index |
| `developer-guide/systems/README.md` | Systems documentation index |
| `deployment/README.md` | Deployment section index |
| `tutorials/README.md` | Tutorials index |
| `reference/README.md` | Reference materials index |
| `about/README.md` | About section index |

#### Missing User Documentation

| New File | Purpose | Priority |
|----------|---------|----------|
| `user-guide/user-manual.md` | Comprehensive user manual | High |
| `user-guide/features-overview.md` | Feature descriptions | High |
| `user-guide/configuration/README.md` | Configuration section index | Medium |
| `user-guide/configuration/basic-settings.md` | Basic configuration guide | High |
| `user-guide/configuration/advanced-settings.md` | Advanced configuration | Medium |

#### Missing Developer Documentation

| New File | Purpose | Priority |
|----------|---------|----------|
| `developer-guide/development-setup.md` | Development environment setup | High |
| `developer-guide/coding-standards.md` | Coding standards and conventions | High |
| `developer-guide/testing.md` | Testing guidelines | Medium |
| `developer-guide/contributing.md` | Developer contribution guide | High |

### Phase 4: Files to Archive/Remove

#### Files to Archive (Move to `about/archive/`)

These files contain historical information but are no longer actively needed:

- `final_completion_report.md` (after consolidation)
- `refactoring_project_summary.md` (after consolidation)
- Individual optimization summaries (after consolidation)

#### Files to Remove (After Content Extraction)

These files will be removed after their content is integrated elsewhere:

- Individual settings summaries (after consolidation into systems guide)
- Individual logging guides (after consolidation into systems guide)
- Redundant summary files (after consolidation into project history)

## Migration Execution Plan

### Step 1: Create Directory Structure

```bash
mkdir -p docs/{getting-started,user-guide,developer-guide,deployment,tutorials,reference,about}
mkdir -p docs/user-guide/configuration
mkdir -p docs/developer-guide/{architecture,api-reference,systems}
mkdir -p docs/reference/api
mkdir -p docs/templates
```

### Step 2: Create Index Files

Create all README.md files for navigation before moving content.

### Step 3: Direct Migrations

Move files that require minimal changes first.

### Step 4: Consolidations

Merge related files into comprehensive guides.

### Step 5: New Content Creation

Create missing documentation using templates.

### Step 6: Link Updates

Update all cross-references and external links.

## Link Update Requirements

### External References (Must Update)

- `README.md` - 3 documentation links
- `README_EN.md` - 6 documentation links

### Internal References (Must Update)

- `QUICK_REFERENCE.md` - 3 internal references (will be moved)
- Any cross-references in migrated files

### New Cross-References (To Add)

- Add "See Also" sections to related documents
- Create navigation breadcrumbs
- Link between consolidated content sections

## Validation Checklist

After migration completion:

### Structure Validation

- [ ] All directories created correctly
- [ ] All files moved to correct locations
- [ ] No broken directory references

### Content Validation

- [ ] All content preserved during consolidation
- [ ] No duplicate information
- [ ] Consistent formatting applied

### Link Validation

- [ ] All internal links working
- [ ] External references updated
- [ ] Cross-references added appropriately

### Navigation Validation

- [ ] All index files created
- [ ] Navigation paths clear
- [ ] Breadcrumbs functional

## Rollback Plan

If migration issues occur:

1. **Backup created** - All original files backed up before migration
2. **Git history** - All changes tracked in version control
3. **Incremental approach** - Migration done in phases for easy rollback
4. **Testing at each phase** - Validation before proceeding to next phase

## Timeline Estimate

- **Phase 1 (Direct Migrations):** 2-3 hours
- **Phase 2 (Consolidations):** 4-5 hours
- **Phase 3 (New Content):** 6-8 hours
- **Phase 4 (Link Updates):** 2-3 hours
- **Validation and Testing:** 2-3 hours

**Total Estimated Time:** 16-22 hours
