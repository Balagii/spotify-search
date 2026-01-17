"""Tests for SpotifyClient data extraction and paging."""

import hashlib
from typing import Any, Dict, List, Optional

from src.spotify_client import SpotifyClient


class FakeSpotipy:
    """Minimal stub for Spotipy paging behavior."""

    def __init__(
        self,
        saved_pages: Optional[List[Dict[str, Any]]] = None,
        playlist_pages: Optional[List[Dict[str, Any]]] = None,
        playlist_tracks_pages: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self._saved_pages = saved_pages or []
        self._playlist_pages = playlist_pages or []
        self._playlist_tracks_pages = playlist_tracks_pages or []

    def current_user_saved_tracks(self, limit: int, offset: int) -> Dict[str, Any]:
        idx = offset // limit
        return self._saved_pages[idx]

    def current_user_playlists(self, limit: int, offset: int) -> Dict[str, Any]:
        idx = offset // limit
        return self._playlist_pages[idx]

    def playlist_tracks(
        self,
        playlist_id: str,
        limit: int,
        offset: int,
        fields: str,
    ) -> Dict[str, Any]:
        idx = offset // limit
        return self._playlist_tracks_pages[idx]


def test_extract_track_data_returns_none_for_empty_track() -> None:
    """None input should yield None output."""
    client = SpotifyClient.__new__(SpotifyClient)
    assert client.extract_track_data(None) is None


def test_extract_track_data_handles_missing_id_and_local_flag() -> None:
    """Local tracks without IDs should get a deterministic ID."""
    client = SpotifyClient.__new__(SpotifyClient)
    track = {
        "id": None,
        "name": "Local Song",
        "uri": "spotify:local:abc",
        "artists": [{"name": "Local Artist"}],
        "album": {"name": "Local Album"},
        "duration_ms": 123,
        "explicit": False,
        "external_urls": {"spotify": "https://open.spotify.com/track/x"},
    }

    data = client.extract_track_data(track, is_local_item=True)
    expected_id = hashlib.md5("spotify:local:abc:Local Song".encode()).hexdigest()

    assert data is not None
    assert data["id"] == expected_id
    assert data["is_local"] is True
    assert data["artist"] == "Local Artist"
    assert data["album"] == "Local Album"


def test_extract_track_data_prefers_existing_id() -> None:
    """Remote tracks should preserve their Spotify ID."""
    client = SpotifyClient.__new__(SpotifyClient)
    track = {
        "id": "spotify123",
        "name": "Song A",
        "uri": "spotify:track:spotify123",
        "artists": [{"name": "Artist A"}],
        "album": {"name": "Album A"},
        "duration_ms": 321,
        "explicit": True,
        "external_urls": {"spotify": "https://open.spotify.com/track/spotify123"},
    }

    data = client.extract_track_data(track, is_local_item=False)

    assert data is not None
    assert data["id"] == "spotify123"
    assert data["is_local"] is False
    assert data["explicit"] is True


def test_extract_track_data_handles_missing_artists() -> None:
    """Missing artist data should yield the fallback label."""
    client = SpotifyClient.__new__(SpotifyClient)
    track = {
        "id": "spotify123",
        "name": "Song A",
        "uri": "spotify:track:spotify123",
        "artists": [],
        "album": {"name": "Album A"},
        "duration_ms": 321,
        "explicit": False,
        "external_urls": {"spotify": "https://open.spotify.com/track/spotify123"},
    }

    data = client.extract_track_data(track, is_local_item=False)

    assert data is not None
    assert data["artist"] == "Unknown Artist"


def test_get_saved_tracks_paginates_and_reports_progress() -> None:
    """Saved tracks should paginate and call progress callback."""
    pages = [
        {
            "items": [
                {
                    "track": {
                        "id": "t1",
                        "name": "Song A",
                        "uri": "spotify:track:t1",
                        "artists": [{"name": "Artist A"}],
                        "album": {"name": "Album A"},
                        "duration_ms": 123,
                        "explicit": False,
                        "external_urls": {"spotify": "url"},
                    },
                    "is_local": False,
                    "added_at": "2024-01-01T00:00:00Z",
                }
            ],
            "next": "next",
            "total": 60,
        },
        {
            "items": [
                {
                    "track": {
                        "id": "t2",
                        "name": "Song B",
                        "uri": "spotify:track:t2",
                        "artists": [{"name": "Artist B"}],
                        "album": {"name": "Album B"},
                        "duration_ms": 456,
                        "explicit": False,
                        "external_urls": {"spotify": "url"},
                    },
                    "is_local": False,
                    "added_at": "2024-01-02T00:00:00Z",
                }
            ],
            "next": None,
            "total": 60,
        },
    ]

    client = SpotifyClient.__new__(SpotifyClient)
    client.sp = FakeSpotipy(saved_pages=pages)

    calls = []

    def progress(current: int, total: int) -> None:
        calls.append((current, total))

    tracks = client.get_saved_tracks(progress_callback=progress)

    assert len(tracks) == 2
    assert tracks[0]["added_at"] == "2024-01-01T00:00:00Z"
    assert tracks[1]["added_at"] == "2024-01-02T00:00:00Z"
    assert calls[0] == (1, 2)
    assert calls[-1] == (2, 2)


def test_get_user_playlists_paginates() -> None:
    """Playlist fetch should return all pages."""
    pages = [
        {
            "items": [
                {
                    "id": "p1",
                    "name": "One",
                    "description": "",
                    "owner": {"display_name": "Owner"},
                    "public": False,
                    "collaborative": False,
                    "tracks": {"total": 1},
                    "snapshot_id": "snap1",
                    "uri": "uri1",
                    "external_urls": {"spotify": "url1"},
                }
            ],
            "next": "next",
            "total": 60,
        },
        {
            "items": [
                {
                    "id": "p2",
                    "name": "Two",
                    "description": "",
                    "owner": {"id": "owner2"},
                    "public": True,
                    "collaborative": True,
                    "tracks": {"total": 2},
                    "snapshot_id": "snap2",
                    "uri": "uri2",
                    "external_urls": {"spotify": "url2"},
                }
            ],
            "next": None,
            "total": 60,
        },
    ]

    client = SpotifyClient.__new__(SpotifyClient)
    client.sp = FakeSpotipy(playlist_pages=pages)

    playlists = client.get_user_playlists()

    assert [p["id"] for p in playlists] == ["p1", "p2"]
    assert playlists[0]["owner"] == "Owner"
    assert playlists[1]["owner"] == "owner2"


def test_get_playlist_tracks_preserves_positions_across_pages() -> None:
    """Playlist tracks should keep positions even for skipped items."""
    pages = [
        {
            "items": [
                {
                    "track": {
                        "id": "t1",
                        "name": "Song A",
                        "uri": "spotify:track:t1",
                        "artists": [{"name": "Artist A"}],
                        "album": {"name": "Album A"},
                        "duration_ms": 123,
                        "explicit": False,
                        "external_urls": {"spotify": "url"},
                    },
                    "is_local": False,
                },
                {"track": None, "is_local": False},
            ],
            "next": "next",
            "total": 101,
        },
        {
            "items": [
                {
                    "track": {
                        "id": "t2",
                        "name": "Song B",
                        "uri": "spotify:track:t2",
                        "artists": [{"name": "Artist B"}],
                        "album": {"name": "Album B"},
                        "duration_ms": 456,
                        "explicit": False,
                        "external_urls": {"spotify": "url"},
                    },
                    "is_local": False,
                }
            ],
            "next": None,
            "total": 101,
        },
    ]

    client = SpotifyClient.__new__(SpotifyClient)
    client.sp = FakeSpotipy(playlist_tracks_pages=pages)

    tracks = client.get_playlist_tracks("playlist123")

    assert [(t["id"], pos) for t, pos in tracks] == [("t1", 0), ("t2", 2)]
