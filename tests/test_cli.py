"""CLI smoke tests for config error handling and data commands"""

import pytest
from click.testing import CliRunner

import src.cli as cli_module
from src import config
from src.cli import cli as root_cli
from src.database import SpotifyDatabase


def _use_temp_db(monkeypatch: pytest.MonkeyPatch, db_path) -> None:
    monkeypatch.setattr(
        cli_module,
        "SpotifyDatabase",
        lambda: SpotifyDatabase(db_path=db_path),
    )


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


def test_search_requires_query_or_filters(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Search should prompt for a query when none is provided."""
    db_path = tmp_path / "spotify_library.json"
    SpotifyDatabase(db_path=db_path).close()
    _use_temp_db(monkeypatch, db_path)

    runner = CliRunner()
    result = runner.invoke(root_cli, ["search"])

    assert result.exit_code == 0
    assert "Please provide a search query" in result.output


def test_search_reports_no_results(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Search should report when filters return no matches."""
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
    _use_temp_db(monkeypatch, db_path)

    runner = CliRunner()
    result = runner.invoke(root_cli, ["search", "--name", "missing"])

    assert result.exit_code == 0
    assert "No results found" in result.output


def test_list_reports_empty_library(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """List should warn when no playlists exist."""
    db_path = tmp_path / "spotify_library.json"
    SpotifyDatabase(db_path=db_path).close()
    _use_temp_db(monkeypatch, db_path)

    runner = CliRunner()
    result = runner.invoke(root_cli, ["list"])

    assert result.exit_code == 0
    assert "No playlists found" in result.output


def test_list_reports_missing_playlist(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """List should report missing playlist matches."""
    db_path = tmp_path / "spotify_library.json"
    seed = SpotifyDatabase(db_path=db_path)
    seed.insert_playlist(
        {
            "id": "p1",
            "name": "Focus",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 0,
        }
    )
    seed.close()
    _use_temp_db(monkeypatch, db_path)

    runner = CliRunner()
    result = runner.invoke(root_cli, ["list", "--playlist", "missing"])

    assert result.exit_code == 0
    assert "No playlist found matching" in result.output


def test_duplicates_reports_empty_db(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Duplicates should warn when playlist data is missing."""
    db_path = tmp_path / "spotify_library.json"
    SpotifyDatabase(db_path=db_path).close()
    _use_temp_db(monkeypatch, db_path)

    runner = CliRunner()
    result = runner.invoke(root_cli, ["duplicates"])

    assert result.exit_code == 0
    assert "No playlist data found" in result.output


def test_duplicates_reports_no_duplicates(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Duplicates should report when no duplicates are found."""
    db_path = tmp_path / "spotify_library.json"
    seed = SpotifyDatabase(db_path=db_path)
    seed.insert_track(
        {
            "id": "t1",
            "name": "Solo",
            "artist": "Artist A",
            "album": "Album A",
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
    seed.add_track_to_playlist("p1", "t1", 0)
    seed.close()
    _use_temp_db(monkeypatch, db_path)

    runner = CliRunner()
    result = runner.invoke(root_cli, ["duplicates"])

    assert result.exit_code == 0
    assert "No duplicates found across playlists" in result.output


def test_list_prompts_for_playlist_selection(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """List should prompt when multiple playlists match."""
    db_path = tmp_path / "spotify_library.json"
    seed = SpotifyDatabase(db_path=db_path)
    seed.insert_playlist(
        {
            "id": "p1",
            "name": "Mix Alpha",
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
            "name": "Mix Beta",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
        }
    )
    seed.insert_track(
        {
            "id": "t1",
            "name": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 0,
        }
    )
    seed.insert_track(
        {
            "id": "t2",
            "name": "Song B",
            "artist": "Artist B",
            "album": "Album B",
            "duration_ms": 0,
        }
    )
    seed.add_track_to_playlist("p1", "t1", 0)
    seed.add_track_to_playlist("p2", "t2", 0)
    seed.close()
    _use_temp_db(monkeypatch, db_path)

    runner = CliRunner()
    result = runner.invoke(root_cli, ["list", "--playlist", "mix"], input="2\n")

    assert result.exit_code == 0
    assert "Multiple playlists found" in result.output
    assert "Mix Alpha" in result.output
    assert "Mix Beta" in result.output
    assert "Song B" in result.output


def test_stats_outputs_summary_and_top_artists(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stats should show totals, listening time, and top artists."""
    db_path = tmp_path / "spotify_library.json"
    seed = SpotifyDatabase(db_path=db_path)
    seed.insert_track(
        {
            "id": "t1",
            "name": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 60000,
        }
    )
    seed.insert_track(
        {
            "id": "t2",
            "name": "Song B",
            "artist": "Artist A",
            "album": "Album B",
            "duration_ms": 120000,
        }
    )
    seed.insert_playlist(
        {
            "id": "p1",
            "name": "Focus",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 2,
        }
    )
    seed.add_saved_track("t1", "2024-01-01T00:00:00Z")
    seed.close()
    _use_temp_db(monkeypatch, db_path)

    runner = CliRunner()
    result = runner.invoke(root_cli, ["stats"])

    assert result.exit_code == 0
    assert "Total unique tracks" in result.output
    assert "Saved/liked tracks" in result.output
    assert "Total playlists" in result.output
    assert "Total listening time" in result.output
    assert "Top Artists" in result.output
    assert "Artist A: 2 tracks" in result.output
