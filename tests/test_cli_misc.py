"""Miscellaneous CLI tests for help, shell, and auth utilities."""

from pathlib import Path

import pytest
from click.testing import CliRunner

import src.cli as cli_module
from src.cli import cli as root_cli
from src.database import SpotifyDatabase


def test_unknown_command_shows_detailed_help() -> None:
    """Unknown command should trigger expanded help output."""
    runner = CliRunner()

    result = runner.invoke(root_cli, ["does-not-exist"])

    assert result.exit_code == 0
    assert "DETAILED COMMAND HELP" in result.output


def test_cli_without_subcommand_invokes_shell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Root CLI without args should delegate to the interactive shell."""
    called = {"value": False}

    def fake_shell():
        called["value"] = True
        raise SystemExit()

    monkeypatch.setattr(cli_module, "shell", fake_shell)
    runner = CliRunner()

    result = runner.invoke(root_cli, [])

    assert result.exit_code == 0
    assert called["value"] is True


def test_print_track_item_outputs_details(tmp_path, capsys) -> None:
    """Track output should include metadata, duplicates, and playlists."""
    db_path = tmp_path / "spotify_library.json"
    db = SpotifyDatabase(db_path=db_path)
    db.insert_track(
        {
            "id": "t1",
            "name": "Local Song",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 90000,
            "external_url": "https://example.com/track",
            "is_local": True,
        }
    )
    db.insert_playlist(
        {
            "id": "p1",
            "name": "Mix One",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
            "external_url": "https://example.com/playlist",
        }
    )
    db.add_track_to_playlist("p1", "t1", 0)
    db.add_track_to_playlist("p1", "t1", 2)
    db.add_saved_track("t1", "2024-01-01T00:00:00Z")

    track = db.get_track("t1")
    assert track is not None

    cli_module._print_track_item(track, db, dup_count=2)
    output = capsys.readouterr().out

    assert "Local file" in output
    assert "Duplicates: 2 occurrences" in output
    assert "https://example.com/track" in output
    assert "https://example.com/playlist" in output
    assert "#1, #3" in output
    assert "Liked Songs" in output

    db.close()


def test_clear_auth_dry_run_and_delete() -> None:
    """Clear-auth should list files, respect dry-run, and delete on request."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".auth-cache").write_text("token", encoding="utf-8")
        Path(".cache-old").write_text("token", encoding="utf-8")

        dry_run = runner.invoke(root_cli, ["clear-auth", "--dry-run"])
        assert dry_run.exit_code == 0
        assert "DRY RUN" in dry_run.output
        assert Path(".auth-cache").exists()
        assert Path(".cache-old").exists()

        cleared = runner.invoke(root_cli, ["clear-auth"])
        assert cleared.exit_code == 0
        assert "Cache cleared" in cleared.output
        assert not Path(".auth-cache").exists()
        assert not Path(".cache-old").exists()


def test_shell_handles_parse_error_and_help(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Shell should report parse errors and run help commands."""
    calls = []

    def fake_run(args, check=False):
        calls.append(args)

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(cli_module.subprocess, "run", fake_run)
    runner = CliRunner()

    result = runner.invoke(root_cli, ["shell"], input='bad "quote\nhelp\nexit\n')

    assert result.exit_code == 0
    assert "Parse error" in result.output
    assert calls
    assert "--help" in calls[0]


def test_auth_success_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auth should print user details when credentials are valid."""

    class FakeClient:
        def get_current_user(self):
            return {"display_name": "Tester", "email": "t@example.com", "country": "US"}

    monkeypatch.setattr(cli_module.config, "validate_config", lambda: True)
    monkeypatch.setattr(cli_module, "SpotifyClient", lambda: FakeClient())
    runner = CliRunner()

    result = runner.invoke(root_cli, ["auth"])

    assert result.exit_code == 0
    assert "Successfully authenticated" in result.output
    assert "t@example.com" in result.output
