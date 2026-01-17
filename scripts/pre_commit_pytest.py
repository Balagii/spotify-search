"""Run pytest for pre-commit and print a helpful failure message."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Run pytest and provide guidance on failure."""
    result = subprocess.run([sys.executable, "-m", "pytest"], check=False)
    if result.returncode != 0:
        sys.stderr.write("\npytest failed.\n")
        sys.stderr.write("Fix locally with: python -m pytest\n")
        sys.stderr.write(
            "If formatting changed files, run: pre-commit run --all-files\n"
        )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
