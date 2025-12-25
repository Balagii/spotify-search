#!/bin/bash
set -e

echo "🚀 Setting up development environment..."

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

echo "✅ Development environment setup complete!"
