"""CLI smoke tests for config error handling and data commands."""

from click.testing import CliRunner
import pytest

import src.cli as cli_module
from src import config
from src.cli import cli as root_cli
from src.database import SpotifyDatabase


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


def test_search_outputs_results(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Search should print matching tracks from the local DB."""
    db_path = tmp_path / "spotify_library.json"
    seed = SpotifyDatabase(db_path=db_path)
    seed.insert_track(
        {
            "id": "t1",
            "name": "Hello",
            "artist": "Adele",
            "album": "25",
            "duration_ms": 0,
        }
    )
    seed.close()

    monkeypatch.setattr(
        cli_module,
        "SpotifyDatabase",
        lambda: SpotifyDatabase(db_path=db_path),
    )

    runner = CliRunner()
    result = runner.invoke(root_cli, ["search", "hello"])

    assert result.exit_code == 0
    assert "Hello" in result.output
    assert "Adele" in result.output


def test_list_playlists_and_tracks(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """List should show playlists and tracks for a selected playlist."""
    db_path = tmp_path / "spotify_library.json"
    seed = SpotifyDatabase(db_path=db_path)
    seed.insert_playlist(
        {
            "id": "p1",
            "name": "Focus",
            "description": "Work",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
        }
    )
    seed.insert_track(
        {
            "id": "t1",
            "name": "Deep Work",
            "artist": "Artist A",
            "album": "Flow",
            "duration_ms": 0,
        }
    )
    seed.add_track_to_playlist("p1", "t1", 0)
    seed.close()

    monkeypatch.setattr(
        cli_module,
        "SpotifyDatabase",
        lambda: SpotifyDatabase(db_path=db_path),
    )

    runner = CliRunner()
    list_result = runner.invoke(root_cli, ["list"])
    assert list_result.exit_code == 0
    assert "Focus" in list_result.output

    playlist_result = runner.invoke(root_cli, ["list", "--playlist", "focus"])
    assert playlist_result.exit_code == 0
    assert "Deep Work" in playlist_result.output


def test_duplicates_command_reports_duplicates(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Duplicates should report a track that appears more than once."""
    db_path = tmp_path / "spotify_library.json"
    seed = SpotifyDatabase(db_path=db_path)
    seed.insert_track(
        {
            "id": "t1",
            "name": "Repeat",
            "artist": "Artist A",
            "album": "Loop",
            "duration_ms": 0,
        }
    )
    seed.insert_playlist(
        {
            "id": "p1",
            "name": "Mix 1",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
        }
    )
    seed.insert_playlist(
        {
            "id": "p2",
            "name": "Mix 2",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
        }
    )
    seed.add_track_to_playlist("p1", "t1", 0)
    seed.add_track_to_playlist("p2", "t1", 0)
    seed.close()

    monkeypatch.setattr(
        cli_module,
        "SpotifyDatabase",
        lambda: SpotifyDatabase(db_path=db_path),
    )

    runner = CliRunner()
    result = runner.invoke(root_cli, ["duplicates", "--limit", "1"])

    assert result.exit_code == 0
    assert "Repeat" in result.output
