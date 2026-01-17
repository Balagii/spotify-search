"""CLI smoke tests for config error handling."""

from click.testing import CliRunner
import pytest

from src import config
from src.cli import cli as root_cli


def test_sync_requires_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sync should fail fast without credentials."""
    monkeypatch.setattr(config, "validate_config", lambda: False)
    runner = CliRunner()

    result = runner.invoke(root_cli, ["sync"])

    assert result.exit_code == 1
    assert "Spotify credentials not configured" in result.output


def test_sync_diff_requires_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Diff sync should fail fast without credentials."""
    monkeypatch.setattr(config, "validate_config", lambda: False)
    runner = CliRunner()

    result = runner.invoke(root_cli, ["sync-diff"])

    assert result.exit_code == 1
    assert "Spotify credentials not configured" in result.output


def test_auth_requires_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auth should report missing credentials and exit cleanly."""
    monkeypatch.setattr(config, "validate_config", lambda: False)
    runner = CliRunner()

    result = runner.invoke(root_cli, ["auth"])

    assert result.exit_code == 0
    assert "Spotify credentials not configured" in result.output
