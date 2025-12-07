# Copilot Configuration

This directory contains GitHub Copilot customizations for the spotify-search project.

## What's Included

### Instructions
- **python.instructions.md** - Python coding conventions and guidelines automatically applied to all `*.py` files
  - PEP 8 style guide compliance
  - Type hints and docstrings (PEP 257)
  - Code formatting standards
  - Edge case handling and testing practices

### Agents
- **python-expert.agent.md** - Expert Python developer assistant for:
  - General Python development
  - FastAPI and web framework guidance
  - Code quality and testing
  - Performance optimization
  - Debugging and refactoring
  - API development and integration

## How to Use

### Using the Python Expert Agent
1. Open GitHub Copilot Chat in VS Code
2. Start a new agent session
3. Select the "python-expert" agent from the available list
4. Ask questions about Python development, FastAPI, testing, etc.

### Example Queries
- "Help me refactor this API endpoint"
- "Write comprehensive tests for this function"
- "What's the best way to handle this error?"
- "How can I improve the performance of this code?"
- "Show me FastAPI best practices for this use case"

### Automatic Instructions
Python instructions are automatically applied to all Python files when working with Copilot. They provide contextual guidance on:
- Type hints and docstrings
- PEP 8 compliance
- Testing practices
- Code organization

## Integration with awesome-copilot

These tools were sourced from the [awesome-copilot](https://github.com/microsoft/awesome-copilot) repository, a community collection of GitHub Copilot customizations.

For additional tools, agents, and prompts, visit the awesome-copilot repository or use the awesome-copilot MCP server.
