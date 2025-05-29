# Development Guidelines

This document contains critical information about working with this codebase. Follow these guidelines precisely.

## Core Development Rules

1. Package Management

   - ONLY use uv, NEVER pip
   - Installation: `uv add package`
   - Running tools: `uvx tool`
   - Upgrading: `uv add --dev package --upgrade-package package`
   - FORBIDDEN: `uv pip install`, `@latest` syntax

2. Code Quality

   - Type hints required for all code
   - Public APIs must have google-style docstrings
   - Target Python version 3.10 syntax
   - Prefer built-in types and types imported from `collections.abc` over types imported from the `typing` module
   - Functions must be focused and small
   - Follow existing patterns exactly
   - Line length: 88 chars maximum

3. Testing Requirements
   - Framework: `uv run --frozen pytest`
   - Coverage: test edge cases and errors
   - New features require tests
   - Bug fixes require regression tests

## Python Tools

## Code Formatting

1. Ruff

   - Format: `uv run --frozen ruff format .`
   - Check: `uv run --frozen ruff check .`
   - Fix: `uv run --frozen ruff check . --fix`
   - Critical issues:
     - Line length (80 chars)
     - Import sorting (I001)
     - Unused imports
   - Line wrapping:
     - Strings: use parentheses
     - Function calls: multi-line with proper indent
     - Imports: split into multiple lines

2. Type Checking

   - Tool: `uv run --frozen mypy`
   - Requirements:
     - Explicit None checks for optional types
     - Type narrowing for strings
     - Version warnings can be ignored if checks pass

3. Code quality

   - Lint check: `qlty check`
   - Code smells: `qlty smell`
   - Code metrics: `qlty metrics --exclude-tests`

4. Pre-commit
   - Config: `.pre-commit-config.yaml`
   - Runs: on git commit
   - Tools: qlty (Markdown/YAML/JSON), Ruff (Python)
   - Ruff updates:
     - Check PyPI versions
     - Update config rev
     - Commit config first

## Error Resolution

1. CI Failures

   - Fix order:
     1. Formatting
     2. Type errors
     3. Linting
   - Type errors:
     - Get full line context
     - Check optional types
     - Add type narrowing
     - Verify function signatures

2. Common Issues

   - Line length:
     - Break strings with parentheses
     - Multi-line function calls
     - Split imports
   - Types:
     - Add None checks for optional types
     - Narrow string types
     - Match existing patterns
   - Pytest:

3. Best Practices
   - Check git status before commits
   - Run formatters before type checks
   - Keep changes minimal
   - Follow existing patterns
   - Document public APIs
   - Test thoroughly
