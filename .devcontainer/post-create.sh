#!/bin/bash
set -e

echo "🚀 Setting up development environment..."

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Pre-install all hook environments
pre-commit install-hooks

echo "✅ Development environment setup complete!"
