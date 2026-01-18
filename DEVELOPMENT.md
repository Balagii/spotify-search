# Development Setup

This document describes the standardized development environment for the Spotify Search project.

## Table of Contents

- [Quick Start](#quick-start)
  - [Option 1: GitHub Codespaces (Recommended)](#option-1-github-codespaces-recommended)
  - [Option 2: Dev Container](#option-2-dev-container)
  - [Option 3: Local Setup](#option-3-local-setup)
- [Development Workflow](#development-workflow)
  - [Common Commands](#common-commands)
  - [Pre-commit Hooks](#pre-commit-hooks)
  - [Code Style Standards](#code-style-standards)
  - [Editor Configuration](#editor-configuration)
- [Project Structure](#project-structure)
- [Testing](#testing)
  - [Running Tests](#running-tests)
  - [Writing Tests](#writing-tests)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Additional Resources](#additional-resources)

## Quick Start

### Option 1: GitHub Codespaces (Recommended)

The fastest way to get started is with GitHub Codespaces, which provides a fully configured cloud-based development environment with Python 3.14 (the only supported version):

1. **Open in Codespaces:**
   - Navigate to the [repository on GitHub](https://github.com/Balagii/spotify-search)
   - Click the green **Code** button
   - Select the **Codespaces** tab
   - Click **Create codespace on master**

2. **Wait for Setup:**
   - Codespaces will automatically build and configure your environment
   - All dependencies, tools, and extensions will be installed automatically
   - This takes 2-3 minutes on first launch

3. **Start Developing:**
   - Your environment is ready to use immediately
   - Pre-commit hooks are already installed
   - All VS Code extensions are configured

**Benefits:**
- ✅ No local setup required
- ✅ Works from any computer with a browser
- ✅ Consistent environment for everyone
- ✅ Free tier available for personal accounts

### Option 2: Dev Container

If you prefer to work locally with Docker:

1. **Prerequisites:**
   - [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - [VS Code](https://code.visualstudio.com/)
   - [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Open in Container:**
   - Open this project in VS Code
   - When prompted, click "Reopen in Container"
   - Or use Command Palette: `Dev Containers: Reopen in Container`

3. **Wait for Setup:**
   - The container will build and install all dependencies automatically
   - This may take a few minutes the first time

### Option 3: Local Setup

If you prefer to work locally:

```bash
# Clone the repository
git clone https://github.com/Balagii/spotify-search.git
cd spotify-search

# Run setup (creates venv, installs deps, sets up hooks)
make setup

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate     # On Windows

# Or manually:
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"  # Install project + dev dependencies
pre-commit install
```

## Development Workflow

### Common Commands

We use a `Makefile` for common development tasks:

```bash
make help          # Show all available commands
make format        # Format code with black and isort
make lint          # Check code style with flake8
make type-check    # Run mypy type checker
make test          # Run tests
make test-cov      # Run tests with coverage report
make pre-commit    # Run all pre-commit hooks manually
make clean         # Remove cache and build artifacts
```

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. They run automatically on `git commit` and check:

- ✅ Code formatting (Black)
- ✅ Import sorting (isort)
- ✅ Linting (flake8)
- ✅ Type checking (mypy)
- ✅ Tests (pytest)
- ✅ File consistency (trailing whitespace, EOF, etc.)
- ✅ Staged file cleanliness (fails if hooks modify staged files)

**How Pre-commit Hooks Work:**

When you run `git commit`, the hooks automatically:
1. Check and format your **staged files**
2. Run `pytest` for the full test suite
3. If any files are modified or tests fail, the commit is **blocked**
4. Review and stage the changes, then commit again

The hook output prints the exact fix command (formatting: `pre-commit run --all-files`;
tests: `python -m pytest`).
Hooks run in pre-commit-managed envs, so venv activation is not required. The
first run can take longer while hook environments install.

**If a Commit Fails:**

```bash
# 1. Pre-commit hooks modified your files
git commit -m "Your message"
# ❌ Commit blocked - files were reformatted

# 2. Stage the newly formatted changes
git add .

# 3. Commit again
git commit -m "Your message"
# ✅ Commit succeeds
```

If tests fail, fix them and rerun `git commit`. The hook output will show the
exact command to run locally (typically `python -m pytest`).

**Bypass Hooks (Use Sparingly):**

If you need to commit without running hooks (e.g., work in progress):
```bash
git commit --no-verify -m "WIP: incomplete feature"
```

**Run Hooks Manually:**

To check all files without committing:
```bash
make pre-commit
# or
pre-commit run --all-files
```

### Code Style Standards

This project follows these conventions:

- **PEP 8** style guide with 88-character line length
- **Black** for code formatting
- **isort** for import sorting (black-compatible profile)
- **Type hints** on all function signatures
- **Docstrings** following PEP 257

### Editor Configuration

The repository includes [`.editorconfig`](.editorconfig) which is automatically respected by VS Code and most modern editors. This ensures:

- Consistent indentation (4 spaces for Python)
- LF line endings
- UTF-8 encoding
- Trailing whitespace removal
- Final newline insertion

## Project Structure

```
spotify-search/
├── .devcontainer/          # Dev container configuration
│   ├── devcontainer.json
│   └── post-create.sh
├── .github/
│   └── instructions/       # Coding guidelines
├── src/                    # Source code
│   ├── cli.py
│   ├── config.py
│   ├── database.py
│   ├── spotify_client.py
│   └── tools/
├── tests/                  # Test files (to be added)
├── .editorconfig          # Editor configuration
├── .gitignore
├── .pre-commit-config.yaml # Pre-commit hooks config
├── Makefile               # Development commands
├── pyproject.toml         # Python project & tool config
└── README.md
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
pytest tests/test_specific.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use pytest fixtures for common setup
- Aim for >80% code coverage

## Troubleshooting

### Pre-commit hooks fail

If pre-commit hooks fail:

1. Fix the issues reported by the hooks
2. Run `pre-commit run --all-files` to apply formatting and re-run checks
3. Re-stage any changed files and try committing again

### Virtual environment issues

```bash
# Remove and recreate virtual environment
rm -rf .venv
make setup
```

### Dev container issues

```bash
# Rebuild container
# In VS Code: Command Palette → "Dev Containers: Rebuild Container"

# Or rebuild without cache
# Command Palette → "Dev Containers: Rebuild Container Without Cache"
```

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run `make pre-commit` to check everything
4. Commit your changes (hooks will run automatically)
5. Push and create a pull request

## Additional Resources

- [Black documentation](https://black.readthedocs.io/)
- [Pre-commit documentation](https://pre-commit.com/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
