#!/usr/bin/env python3
"""Generate .env.example and README env snippet from config metadata."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config  # noqa: E402

ENV_EXAMPLE_PATH = ROOT / ".env.example"
README_PATH = ROOT / "README.md"

README_START = "<!-- env-example:start -->"
README_END = "<!-- env-example:end -->"


def _env_value_for_example(var: config.EnvVar) -> str:
    if var.example is not None:
        return var.example
    if var.default is not None:
        return var.default
    return ""


def build_env_lines() -> list[str]:
    lines: list[str] = []
    lines.extend(config.ENV_DOCS_HEADER)
    for var in config.ENV_VARS:
        comment = ""
        if var.description:
            if var.required:
                comment = f"# {var.description}"
            else:
                default_note = f" (default: {var.default})" if var.default else ""
                comment = f"# Optional: {var.description}{default_note}"
        if comment:
            lines.append(comment)
        lines.append(f"{var.name}={_env_value_for_example(var)}")
    return lines


def write_env_example(lines: list[str]) -> None:
    ENV_EXAMPLE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_readme(lines: list[str]) -> None:
    block = "\n".join(lines)
    snippet = f"{README_START}\n```env\n{block}\n```\n{README_END}"
    text = README_PATH.read_text(encoding="utf-8")
    if README_START not in text or README_END not in text:
        raise SystemExit("README env-example markers not found.")
    start = text.index(README_START)
    end = text.index(README_END) + len(README_END)
    README_PATH.write_text(text[:start] + snippet + text[end:], encoding="utf-8")


def main() -> None:
    lines = build_env_lines()
    write_env_example(lines)
    update_readme(lines)


if __name__ == "__main__":
    main()
