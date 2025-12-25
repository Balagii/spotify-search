.PHONY: help install install-dev format lint type-check test test-cov clean pre-commit setup

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup          - Initial setup (create venv, install deps, setup hooks)"
	@echo "  make install        - Install production dependencies"
	@echo "  make install-dev    - Install all dependencies (prod + dev)"
	@echo "  make format         - Format code with black and isort"
	@echo "  make lint           - Run flake8 linter"
	@echo "  make type-check     - Run mypy type checker"
	@echo "  make test           - Run tests with pytest"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make pre-commit     - Run all pre-commit hooks"
	@echo "  make clean          - Remove cache files and build artifacts"

# Initial setup
setup:
	@echo "🚀 Setting up development environment..."
	python -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -r requirements.txt
	. .venv/bin/activate && pip install -r requirements-dev.txt
	. .venv/bin/activate && pre-commit install
	@echo "✅ Setup complete! Activate venv with: source .venv/bin/activate"

# Install dependencies
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Code formatting
format:
	@echo "🎨 Formatting code..."
	black src/
	isort src/

# Linting
lint:
	@echo "🔍 Running linter..."
	flake8 src/ --max-line-length=88 --extend-ignore=E203,W503

# Type checking
type-check:
	@echo "📝 Running type checker..."
	mypy src/ --ignore-missing-imports --no-strict-optional

# Testing
test:
	@echo "🧪 Running tests..."
	pytest

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=src --cov-report=term-missing --cov-report=html

# Pre-commit
pre-commit:
	@echo "🔨 Running pre-commit hooks..."
	pre-commit run --all-files

# Cleaning
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "✨ Cleaned!"
