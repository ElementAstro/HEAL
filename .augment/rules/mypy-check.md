---
type: "manual"
---

Run mypy type checking across the entire project to identify type-related issues, then systematically fix all the errors found. Please follow these steps:

1. First, run mypy on the entire codebase to get a comprehensive list of type errors
2. Analyze the output to understand the types of errors present
3. Prioritize and categorize the errors (e.g., missing type annotations, incorrect type usage, import issues)
4. Fix the errors systematically, starting with the most critical ones
5. After making fixes, re-run mypy to verify the errors are resolved
6. Continue this process until all mypy errors are eliminated

If mypy is not already configured for this project, please also:
- Check if there's an existing mypy configuration file (mypy.ini, pyproject.toml, or setup.cfg)
- If no configuration exists, create an appropriate mypy configuration
- Ensure mypy is installed as a development dependency

Please provide a summary of the types of errors found and the fixes applied.