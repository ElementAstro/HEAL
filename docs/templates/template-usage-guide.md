# Documentation Template Usage Guide

This guide explains how to use the documentation templates to create consistent, high-quality documentation for the HEAL project.

## Available Templates

### Template Files

- `TEMPLATE_USER_GUIDE.md` - For end-user documentation
- `TEMPLATE_DEVELOPER_GUIDE.md` - For developer/contributor documentation
- `TEMPLATE_API_REFERENCE.md` - For API and technical reference documentation
- `TEMPLATE_TUTORIAL.md` - For step-by-step learning materials

### When to Use Each Template

#### User Guide Template

**Use for:**

- Feature usage instructions
- Configuration guides
- Troubleshooting guides
- End-user workflows

**Target Audience:** End users of the HEAL application

#### Developer Guide Template

**Use for:**

- Component development guides
- System architecture documentation
- Implementation guides
- Technical deep-dives

**Target Audience:** Developers and contributors

#### API Reference Template

**Use for:**

- Class and function documentation
- Module references
- Technical specifications
- Code examples with parameters and return values

**Target Audience:** Developers integrating with HEAL

#### Tutorial Template

**Use for:**

- Step-by-step learning materials
- Hands-on exercises
- Getting started guides
- Progressive skill building

**Target Audience:** Users learning specific skills

## How to Use Templates

### Step 1: Choose the Right Template

1. Identify your target audience
2. Determine the document's primary purpose
3. Select the appropriate template

### Step 2: Copy and Customize

1. Copy the template file to your target location
2. Rename the file following naming conventions
3. Replace placeholder content with your specific information

### Step 3: Fill in Content

1. Replace `[Placeholder Text]` with actual content
2. Remove sections that don't apply
3. Add additional sections if needed
4. Follow the established structure

### Step 4: Review and Validate

1. Check against documentation standards
2. Verify all links work
3. Test code examples
4. Review for consistency

## Template Customization Guidelines

### Required Sections

Each template has required sections that should always be included:

- Title and description
- Overview or introduction
- Main content sections
- Related links or references

### Optional Sections

Some sections can be omitted if not relevant:

- Advanced features (if none exist)
- Troubleshooting (if comprehensive guide exists elsewhere)
- Examples (if covered in separate tutorial)

### Adding Custom Sections

You can add sections specific to your content:

- Keep the overall structure consistent
- Use appropriate header levels
- Follow naming conventions
- Add to table of contents if present

## Content Guidelines

### Writing Style

- **Clear and concise** - Avoid unnecessary complexity
- **Active voice** - Use active voice when possible
- **Present tense** - Use present tense for instructions
- **Consistent terminology** - Use the same terms throughout

### Code Examples

- **Complete and working** - All examples should be functional
- **Realistic** - Use realistic scenarios and data
- **Well-commented** - Include explanatory comments
- **Tested** - Verify all examples work as shown

### Cross-References

- **Link to related content** - Help users find additional information
- **Use relative paths** - For internal documentation links
- **Descriptive link text** - Avoid "click here" or generic text
- **Verify links** - Ensure all links work correctly

## Template Maintenance

### Updating Templates

When updating templates:

1. Consider impact on existing documentation
2. Update the template usage guide
3. Notify documentation maintainers
4. Version control template changes

### Template Versioning

- Track template versions in commit messages
- Document significant changes
- Maintain backward compatibility when possible
- Provide migration guidance for breaking changes

## Quality Checklist

Before publishing documentation created from templates:

### Content Quality

- [ ] All placeholder text replaced
- [ ] Information accurate and up-to-date
- [ ] Examples tested and working
- [ ] Appropriate level of detail for audience

### Structure and Format

- [ ] Follows template structure
- [ ] Headers properly formatted
- [ ] Code blocks have language identifiers
- [ ] Lists and tables properly formatted

### Navigation and Links

- [ ] All internal links work
- [ ] External links verified
- [ ] Cross-references appropriate
- [ ] "See Also" section included where relevant

### Standards Compliance

- [ ] Follows naming conventions
- [ ] Meets formatting standards
- [ ] Includes required metadata
- [ ] Consistent with project style

## Examples

### Creating a User Guide

1. Copy `TEMPLATE_USER_GUIDE.md` to `user-guide/new-feature.md`
2. Replace `[Feature/Topic Name]` with "Advanced Search"
3. Fill in overview, prerequisites, and steps
4. Add troubleshooting section with common issues
5. Include examples and configuration options
6. Add cross-references to related guides

### Creating a Developer Guide

1. Copy `TEMPLATE_DEVELOPER_GUIDE.md` to `developer-guide/systems/caching.md`
2. Replace placeholders with caching system information
3. Include architecture diagrams and code examples
4. Add API reference section with class documentation
5. Include testing examples and best practices
6. Link to related architecture documentation

### Creating an API Reference

1. Copy `TEMPLATE_API_REFERENCE.md` to `developer-guide/api-reference/data-manager.md`
2. Document all public classes and methods
3. Include complete parameter and return information
4. Add usage examples for each major function
5. Document exceptions and error conditions
6. Include migration notes if applicable

### Creating a Tutorial

1. Copy `TEMPLATE_TUTORIAL.md` to `tutorials/creating-custom-component.md`
2. Define clear learning objectives
3. Break down into logical steps with checkpoints
4. Include complete, working code examples
5. Add troubleshooting for common issues
6. Provide next steps and related resources

## Best Practices

### Template Selection

- **Match audience needs** - Choose template based on who will read it
- **Consider document purpose** - Select based on what users need to accomplish
- **Think about context** - Consider where the document fits in the overall documentation

### Content Development

- **Start with outline** - Plan your content structure before writing
- **Write for scanning** - Use headers, lists, and formatting for easy scanning
- **Include examples** - Concrete examples help users understand concepts
- **Test everything** - Verify all instructions and examples work

### Maintenance

- **Regular reviews** - Schedule periodic reviews of template-based documentation
- **User feedback** - Incorporate feedback to improve template usage
- **Template evolution** - Update templates based on common patterns and needs
- **Consistency checks** - Regularly verify consistency across template-based documents

## Getting Help

### Template Questions

- Check this usage guide first
- Review existing documentation for examples
- Ask in project discussions or issues
- Contact documentation maintainers

### Content Questions

- Review documentation standards
- Check style guide for writing guidelines
- Look at similar existing documentation
- Get feedback from target audience

### Technical Issues

- Verify markdown formatting
- Test all links and references
- Check code examples in appropriate environment
- Validate against project standards

---

**Last Updated:** [Date]  
**Template Version:** 1.0  
**Maintainer:** Documentation Team
