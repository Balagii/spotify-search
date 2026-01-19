"""Tests for sync command behavior."""

import pytest
from click.testing import CliRunner

import src.cli as cli_module
from src.database import SpotifyDatabase

root_cli = cli_module.cli


class FakeSyncClient:
    """Stub client for sync scenarios."""

    def __init__(self, playlists, playlist_tracks, saved_tracks=None):
        self._playlists = playlists
        self._playlist_tracks = playlist_tracks
        self._saved_tracks = saved_tracks or []
        self.saved_tracks_called = False

    def get_current_user(self):
        return {"display_name": "Test User"}

    def get_saved_tracks(self, progress_callback=None):
        self.saved_tracks_called = True
        if progress_callback:
            progress_callback(1, 1)
        return list(self._saved_tracks)

    def get_user_playlists(self, progress_callback=None):
        if progress_callback:
            progress_callback(1, 1)
        return list(self._playlists)

    def get_playlist_tracks(self, playlist_id, progress_callback=None):
        if progress_callback:
            progress_callback(1, 1)
        return list(self._playlist_tracks.get(playlist_id, []))


def _use_temp_db(monkeypatch: pytest.MonkeyPatch, db_path) -> None:
    monkeypatch.setattr(
        cli_module,
        "SpotifyDatabase",
        lambda: SpotifyDatabase(db_path=db_path),
    )


def test_sync_playlist_name_not_found_exits(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sync should exit when no playlist matches the provided name."""
    db_path = tmp_path / "spotify_library.json"
    SpotifyDatabase(db_path=db_path).close()

    playlists = [
        {
            "id": "p1",
            "name": "Focus",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 0,
            "snapshot_id": "snap1",
            "uri": "uri1",
            "external_url": "url1",
        }
    ]
    fake_client = FakeSyncClient(playlists=playlists, playlist_tracks={})

    monkeypatch.setattr(cli_module.config, "validate_config", lambda: True)
    monkeypatch.setattr(cli_module, "SpotifyClient", lambda: fake_client)
    _use_temp_db(monkeypatch, db_path)

    runner = CliRunner()
    result = runner.invoke(root_cli, ["sync", "--playlist", "missing"])

    assert result.exit_code == 0
    assert "No playlist found matching" in result.output


def test_sync_playlist_selection_saves_selected(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sync should prompt and save only the selected playlist."""
    db_path = tmp_path / "spotify_library.json"
    SpotifyDatabase(db_path=db_path).close()

    playlists = [
        {
            "id": "p1",
            "name": "Mix Alpha",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
            "snapshot_id": "snap1",
            "uri": "uri1",
            "external_url": "url1",
        },
        {
            "id": "p2",
            "name": "Mix Beta",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
            "snapshot_id": "snap2",
            "uri": "uri2",
            "external_url": "url2",
        },
    ]
    playlist_tracks = {
        "p1": [
            (
                {
                    "id": "t1",
                    "name": "Song A",
                    "artist": "Artist A",
                    "album": "Album A",
                    "duration_ms": 0,
                },
                0,
            )
        ],
        "p2": [
            (
                {
                    "id": "t2",
                    "name": "Song B",
                    "artist": "Artist B",
                    "album": "Album B",
                    "duration_ms": 0,
                },
                0,
            )
        ],
    }
    fake_client = FakeSyncClient(playlists=playlists, playlist_tracks=playlist_tracks)

    monkeypatch.setattr(cli_module.config, "validate_config", lambda: True)
    monkeypatch.setattr(cli_module, "SpotifyClient", lambda: fake_client)
    _use_temp_db(monkeypatch, db_path)

    runner = CliRunner()
    result = runner.invoke(root_cli, ["sync", "--playlist", "mix"], input="2\n")

    assert result.exit_code == 0
    assert "Mix Beta" in result.output

    check = SpotifyDatabase(db_path=db_path)
    playlists = check.get_all_playlists()
    tracks = check.get_playlist_tracks("p2")
    snapshot = check.get_playlist("p2")
    saved = check.get_saved_tracks()
    check.close()

    assert len(playlists) == 1
    assert playlists[0]["id"] == "p2"
    assert [t["id"] for t in tracks] == ["t2"]
    assert snapshot is not None
    assert snapshot.get("snapshot_id") == "snap2"
    assert saved == []


def test_sync_clear_option_removes_existing_data(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sync with --clear should remove existing data before saving new data."""
    db_path = tmp_path / "spotify_library.json"
    seed = SpotifyDatabase(db_path=db_path)
    seed.insert_track(
        {
            "id": "old",
            "name": "Old Song",
            "artist": "Old Artist",
            "album": "Old Album",
            "duration_ms": 0,
        }
    )
    seed.insert_playlist(
        {
            "id": "old-pl",
            "name": "Old Playlist",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
        }
    )
    seed.add_track_to_playlist("old-pl", "old", 0)
    seed.add_saved_track("old", "2024-01-01T00:00:00Z")
    seed.close()

    saved_tracks = [
        {
            "id": "t1",
            "name": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 0,
            "added_at": "2024-02-01T00:00:00Z",
        }
    ]
    playlists = [
        {
            "id": "p1",
            "name": "Mix One",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
            "snapshot_id": "snap1",
            "uri": "uri1",
            "external_url": "url1",
        }
    ]
    playlist_tracks = {
        "p1": [
            (
                {
                    "id": "t1",
                    "name": "Song A",
                    "artist": "Artist A",
                    "album": "Album A",
                    "duration_ms": 0,
                },
                0,
            )
        ]
    }
    fake_client = FakeSyncClient(
        playlists=playlists,
        playlist_tracks=playlist_tracks,
        saved_tracks=saved_tracks,
    )

    monkeypatch.setattr(cli_module.config, "validate_config", lambda: True)
    monkeypatch.setattr(cli_module, "SpotifyClient", lambda: fake_client)
    _use_temp_db(monkeypatch, db_path)

    runner = CliRunner()
    result = runner.invoke(root_cli, ["sync", "--clear"])

    assert result.exit_code == 0
    assert "Sync completed successfully" in result.output

    check = SpotifyDatabase(db_path=db_path)
    assert check.get_track("old") is None
    assert check.get_playlist("old-pl") is None
    saved = check.get_saved_tracks()
    check.close()

    assert [t["id"] for t in saved] == ["t1"]
