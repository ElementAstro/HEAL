# HEAL Documentation Standards and Conventions

## File and Directory Naming Conventions

### Directory Names

- **Use lowercase with hyphens** for multi-word directories
- **Be descriptive and concise**
- **Use singular nouns** where appropriate

**Examples:**

- ✅ `getting-started/`
- ✅ `user-guide/`
- ✅ `developer-guide/`
- ✅ `api-reference/`
- ❌ `Getting_Started/`
- ❌ `userGuide/`
- ❌ `DEVELOPER-GUIDE/`

### File Names

- **Use lowercase with hyphens** for multi-word files
- **Use descriptive names** that clearly indicate content
- **Always use `.md` extension** for Markdown files
- **Use `README.md`** for directory index files

**Examples:**

- ✅ `installation.md`
- ✅ `quick-start.md`
- ✅ `api-reference.md`
- ✅ `troubleshooting.md`
- ❌ `Installation.md`
- ❌ `quick_start.md`
- ❌ `API-Reference.MD`
- ❌ `troubleShooting.md`

### Special File Names

- **`README.md`** - Directory index and navigation
- **`CONTRIBUTING.md`** - Contribution guidelines (project root)
- **`CODE_OF_CONDUCT.md`** - Community guidelines (project root)
- **`CHANGELOG.md`** - Version history (project root)

## Markdown Formatting Standards

### Document Structure

Every document should follow this structure:

```markdown
# Document Title

Brief description of the document's purpose and scope.

## Table of Contents (for long documents)
- [Section 1](#section-1)
- [Section 2](#section-2)

## Section 1

Content here...

### Subsection 1.1

Content here...

## Section 2

Content here...

## See Also
- [Related Document 1](../path/to/document.md)
- [Related Document 2](path/to/document.md)
```

### Headers

- **Use ATX-style headers** (`#`, `##`, `###`)
- **Use sentence case** for headers (capitalize first word and proper nouns)
- **Include space after `#`**
- **Maximum 4 levels** of headers (`####`)
- **Use descriptive headers** that clearly indicate content

**Examples:**

- ✅ `# Getting started with HEAL`
- ✅ `## Installation requirements`
- ✅ `### Windows installation`
- ❌ `#Getting Started`
- ❌ `## INSTALLATION REQUIREMENTS`
- ❌ `##### Too many levels`

### Code Blocks

- **Use fenced code blocks** with language specification
- **Include language identifier** for syntax highlighting
- **Use consistent indentation** (4 spaces for nested content)

**Examples:**

```markdown
```python
def hello_world():
    print("Hello, World!")
```

```bash
pip install heal
```

```json
{
  "name": "heal",
  "version": "1.0.0"
}
```

```

### Lists
- **Use `-` for unordered lists**
- **Use `1.` for ordered lists**
- **Maintain consistent indentation** (2 spaces for nested items)
- **Use parallel structure** in list items

**Examples:**
```markdown
- First item
- Second item
  - Nested item
  - Another nested item
- Third item

1. First step
2. Second step
3. Third step
```

### Links and References

- **Use descriptive link text** (not "click here")
- **Use relative paths** for internal documentation links
- **Include file extensions** in links
- **Test all links** before publishing

**Examples:**

- ✅ `[Installation guide](getting-started/installation.md)`
- ✅ `[API reference](../developer-guide/api-reference/)`
- ✅ `[HEAL GitHub repository](https://github.com/ElementAstro/HEAL)`
- ❌ `[Click here](installation.md)`
- ❌ `[guide](installation)`

### Cross-References

- **Add "See Also" sections** for related content
- **Use breadcrumb navigation** where appropriate
- **Link to parent/child documents**

**Example:**

```markdown
## See Also
- [User Guide](../user-guide/README.md) - For end-user documentation
- [API Reference](api-reference/README.md) - For detailed API information
- [Troubleshooting](../user-guide/troubleshooting.md) - For common issues
```

### Tables

- **Use pipe tables** with proper alignment
- **Include headers** for all tables
- **Align columns** for readability
- **Keep tables simple** (complex data should use lists)

**Example:**

```markdown
| Feature | Status | Notes |
|---------|--------|-------|
| Authentication | ✅ Complete | Fully implemented |
| Logging | 🚧 In Progress | Basic functionality ready |
| Testing | ❌ Planned | Not yet started |
```

### Emphasis and Formatting

- **Use `**bold**`** for important terms and UI elements
- **Use `*italic*`** for emphasis and first-time term introduction
- **Use `code`** for code elements, file names, and commands
- **Use `> blockquotes`** for important notes and warnings

**Examples:**

- ✅ Click the **Save** button to save your changes
- ✅ The *configuration file* contains all settings
- ✅ Run `python main.py` to start the application
- ✅ > **Warning:** This action cannot be undone

### Admonitions and Callouts

Use consistent formatting for different types of callouts:

```markdown
> **Note:** Additional information that might be helpful.

> **Warning:** Important information that could prevent errors.

> **Tip:** Helpful suggestions for better results.

> **Important:** Critical information that must not be ignored.
```

## Content Standards

### Writing Style

- **Use clear, concise language**
- **Write in active voice** when possible
- **Use present tense** for instructions
- **Be consistent with terminology**
- **Define technical terms** on first use

### Code Examples

- **Provide complete, working examples**
- **Include expected output** where relevant
- **Use realistic examples** that users might actually need
- **Test all code examples** before publishing

### Screenshots and Images

- **Use descriptive alt text** for accessibility
- **Keep images up-to-date** with current UI
- **Use consistent image formats** (PNG for screenshots, SVG for diagrams)
- **Store images in appropriate directories**

## Template Usage

### Document Templates

Each document type should follow its specific template:

- **User guides** - Focus on tasks and outcomes
- **Developer guides** - Include technical details and examples
- **API references** - Provide complete parameter and return information
- **Tutorials** - Use step-by-step format with clear objectives

### Template Locations

- Templates are stored in `docs/templates/`
- Use appropriate template for document type
- Customize template content while maintaining structure

## Quality Checklist

Before publishing any documentation:

### Content Review

- [ ] Purpose and audience clearly defined
- [ ] Information accurate and up-to-date
- [ ] Examples tested and working
- [ ] Cross-references verified

### Format Review

- [ ] Naming conventions followed
- [ ] Markdown formatting correct
- [ ] Headers properly structured
- [ ] Links working and properly formatted
- [ ] Code blocks have language identifiers

### Navigation Review

- [ ] Document linked from appropriate index
- [ ] Cross-references added where helpful
- [ ] "See Also" section included if relevant
- [ ] Breadcrumb navigation clear

## Maintenance Guidelines

### Regular Updates

- **Review quarterly** for accuracy
- **Update screenshots** when UI changes
- **Verify links** regularly
- **Update examples** with new features

### Version Control

- **Use meaningful commit messages** for documentation changes
- **Review changes** before merging
- **Tag major documentation updates**
- **Maintain changelog** for significant changes

### Feedback Integration

- **Monitor user feedback** on documentation
- **Address common questions** by improving docs
- **Update based on support requests**
- **Regularly review and improve** based on usage patterns

## Tools and Automation

### Recommended Tools

- **Markdown linter** for format checking
- **Link checker** for broken link detection
- **Spell checker** for content review
- **Grammar checker** for writing quality

### Automation Opportunities

- **Automated link checking** in CI/CD
- **Format validation** on pull requests
- **Automated table of contents** generation
- **Cross-reference validation**
