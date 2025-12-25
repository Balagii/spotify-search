# Contributing to Spotify Search

Thank you for considering contributing to Spotify Search! This document provides guidelines and instructions for contributing.

## Development Environment

Please read [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions. Quick start:

```bash
# Using Dev Container (recommended)
# Open in VS Code and select "Reopen in Container"

# Or local setup
make setup
source .venv/bin/activate
```

## Code Standards

### Style Guide

- Follow **PEP 8** with 88-character line length
- Use **Black** for formatting (runs automatically on commit)
- Use **isort** for import sorting
- Include **type hints** on all function signatures
- Write **docstrings** for all public functions/classes

### Before Committing

All commits must pass pre-commit hooks:

```bash
make pre-commit  # Run all checks manually
make format      # Auto-format code
make lint        # Check code style
make type-check  # Run type checker
make test        # Run tests
```

### Commit Messages

Follow conventional commit format:

- `feat: add new search filter`
- `fix: resolve duplicate detection bug`
- `docs: update README with new examples`
- `refactor: simplify database query logic`
- `test: add tests for spotify client`
- `chore: update dependencies`

## Pull Request Process

1. **Fork & Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write clear, documented code
   - Add tests for new functionality
   - Ensure all tests pass

3. **Run Checks**
   ```bash
   make pre-commit
   make test-cov
   ```

4. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Describe your changes clearly
   - Reference any related issues
   - Ensure CI passes

## Testing Guidelines

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names: `test_search_finds_exact_match`
- Aim for >80% code coverage
- Use pytest fixtures for setup

### Running Tests

```bash
make test          # Run all tests
make test-cov      # With coverage report
pytest tests/test_specific.py  # Specific file
pytest -k test_name           # Specific test
```

## Reporting Issues

When reporting bugs, include:

- Description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Error messages/stack traces

## Feature Requests

For new features:

- Describe the feature and use case
- Explain why it would be valuable
- Provide examples if possible

## Questions?

- Open a GitHub issue
- Check existing issues and discussions
- Review documentation

## Code Review

All submissions require review. We aim to:

- Respond within 2-3 days
- Provide constructive feedback
- Ensure code quality and consistency

Thank you for contributing! 🎵
