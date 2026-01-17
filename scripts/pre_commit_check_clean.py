"""Detect formatting changes to staged files and print next steps."""

from __future__ import annotations

import subprocess
import sys


def _git_output(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    """Fail if staged files were modified by hooks."""
    staged = set(_git_output(["diff", "--cached", "--name-only"]))
    unstaged = set(_git_output(["diff", "--name-only"]))
    modified = sorted(staged & unstaged)
    if not modified:
        return 0

    sys.stderr.write("\nFormatting hooks modified staged files:\n")
    for path in modified:
        sys.stderr.write(f" - {path}\n")
    sys.stderr.write("\nFix locally with:\n")
    sys.stderr.write("  pre-commit run --all-files\n")
    sys.stderr.write("  git add <files>\n")
    sys.stderr.write("  git commit\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
