"""Tests for sync-diff behavior."""

import pytest
from click.testing import CliRunner

import src.cli as cli_module
from src import config
from src.database import SpotifyDatabase

root_cli = cli_module.cli


class FakeClient:
    """Stub client for sync-diff scenarios."""

    def __init__(self, playlists, playlist_tracks, saved_tracks=None):
        self._playlists = playlists
        self._playlist_tracks = playlist_tracks
        self._saved_tracks = saved_tracks or []
        self.playlist_tracks_called = False

    def get_current_user(self):
        return {"display_name": "Test User"}

    def get_saved_tracks_total(self):
        return len(self._saved_tracks)

    def get_saved_tracks(self, progress_callback=None):
        if progress_callback:
            progress_callback(1, 1)
        return list(self._saved_tracks)

    def get_user_playlists(self, progress_callback=None):
        if progress_callback:
            progress_callback(1, 1)
        return self._playlists

    def get_playlist_tracks(self, playlist_id, progress_callback=None):
        self.playlist_tracks_called = True
        if progress_callback:
            progress_callback(1, 1)
        return self._playlist_tracks


def test_sync_diff_skips_matching_snapshot(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Matching snapshot_id should skip playlist updates."""
    db_path = tmp_path / "spotify_library.json"
    seed = SpotifyDatabase(db_path=db_path)
    seed.insert_playlist(
        {
            "id": "p1",
            "name": "Playlist One",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
            "snapshot_id": "snap1",
        }
    )
    seed.close()

    playlist = {
        "id": "p1",
        "name": "Playlist One",
        "description": "",
        "owner": "Owner",
        "public": False,
        "collaborative": False,
        "tracks_total": 1,
        "snapshot_id": "snap1",
        "uri": "uri",
        "external_url": "url",
    }
    fake_client = FakeClient(playlists=[playlist], playlist_tracks=[])

    monkeypatch.setattr(config, "validate_config", lambda: True)
    monkeypatch.setattr(cli_module, "SpotifyClient", lambda: fake_client)
    monkeypatch.setattr(
        cli_module,
        "SpotifyDatabase",
        lambda: SpotifyDatabase(db_path=db_path),
    )

    runner = CliRunner()
    result = runner.invoke(root_cli, ["sync-diff"])

    assert result.exit_code == 0
    assert "Playlists skipped: 1" in result.output
    assert fake_client.playlist_tracks_called is False


def test_sync_diff_updates_when_snapshot_missing(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    """Missing snapshot should trigger playlist update when counts differ."""
    db_path = tmp_path / "spotify_library.json"
    seed = SpotifyDatabase(db_path=db_path)
    seed.insert_playlist(
        {
            "id": "p1",
            "name": "Playlist One",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 0,
        }
    )
    seed.close()

    playlist = {
        "id": "p1",
        "name": "Playlist One",
        "description": "",
        "owner": "Owner",
        "public": False,
        "collaborative": False,
        "tracks_total": 1,
        "snapshot_id": "snap2",
        "uri": "uri",
        "external_url": "url",
    }
    playlist_tracks = [
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
    fake_client = FakeClient(playlists=[playlist], playlist_tracks=playlist_tracks)

    monkeypatch.setattr(config, "validate_config", lambda: True)
    monkeypatch.setattr(cli_module, "SpotifyClient", lambda: fake_client)
    monkeypatch.setattr(
        cli_module,
        "SpotifyDatabase",
        lambda: SpotifyDatabase(db_path=db_path),
    )

    runner = CliRunner()
    result = runner.invoke(root_cli, ["sync-diff"])

    assert result.exit_code == 0
    assert "Playlists updated: 1" in result.output
    assert fake_client.playlist_tracks_called is True

    check = SpotifyDatabase(db_path=db_path)
    stored = check.get_playlist("p1")
    tracks = check.get_playlist_tracks("p1")
    check.close()

    assert stored is not None
    assert stored.get("snapshot_id") == "snap2"
    assert [t["id"] for t in tracks] == ["t1"]


def test_sync_diff_updates_saved_tracks_when_counts_differ(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Saved track count mismatches should trigger a refresh."""
    db_path = tmp_path / "spotify_library.json"
    SpotifyDatabase(db_path=db_path).close()

    saved_tracks = [
        {
            "id": "t1",
            "name": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 0,
            "added_at": "2024-01-01T00:00:00Z",
        }
    ]
    fake_client = FakeClient(
        playlists=[], playlist_tracks=[], saved_tracks=saved_tracks
    )

    monkeypatch.setattr(config, "validate_config", lambda: True)
    monkeypatch.setattr(cli_module, "SpotifyClient", lambda: fake_client)
    monkeypatch.setattr(
        cli_module,
        "SpotifyDatabase",
        lambda: SpotifyDatabase(db_path=db_path),
    )

    runner = CliRunner()
    result = runner.invoke(root_cli, ["sync-diff"])

    assert result.exit_code == 0
    assert "Saved tracks updated: 1" in result.output

    check = SpotifyDatabase(db_path=db_path)
    saved = check.get_saved_tracks()
    check.close()

    assert [t["id"] for t in saved] == ["t1"]
