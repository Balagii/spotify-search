"""Tests for SpotifyClient data extraction and paging."""

import hashlib
from typing import Any, Dict, List, Optional

import pytest

import src.spotify_client as spotify_client_module

SpotifyClient = spotify_client_module.SpotifyClient


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


def test_get_saved_tracks_returns_empty_on_empty_page() -> None:
    """Saved tracks should return empty when the page has no items."""
    pages = [{"items": [], "next": None, "total": 0}]
    client = SpotifyClient.__new__(SpotifyClient)
    client.sp = FakeSpotipy(saved_pages=pages)

    tracks = client.get_saved_tracks()

    assert tracks == []


def test_get_saved_tracks_total_returns_int() -> None:
    """Total saved tracks should be reported as an integer."""

    class TotalSpotipy:
        def current_user_saved_tracks(self, limit: int) -> Dict[str, Any]:
            return {"total": 42}

    client = SpotifyClient.__new__(SpotifyClient)
    client.sp = TotalSpotipy()

    assert client.get_saved_tracks_total() == 42


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

    calls = []

    def progress(current: int, total: int) -> None:
        calls.append((current, total))

    playlists = client.get_user_playlists(progress_callback=progress)

    assert [p["id"] for p in playlists] == ["p1", "p2"]
    assert playlists[0]["owner"] == "Owner"
    assert playlists[1]["owner"] == "owner2"
    assert calls[0] == (1, 2)
    assert calls[-1] == (2, 2)


def test_get_user_playlists_returns_empty_on_empty_page() -> None:
    """Empty playlist pages should return an empty list."""
    pages = [{"items": [], "next": None, "total": 0}]
    client = SpotifyClient.__new__(SpotifyClient)
    client.sp = FakeSpotipy(playlist_pages=pages)

    playlists = client.get_user_playlists()

    assert playlists == []


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


def test_get_playlist_tracks_reports_progress() -> None:
    """Playlist track paging should report progress when requested."""
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
                }
            ],
            "next": None,
            "total": 1,
        }
    ]
    client = SpotifyClient.__new__(SpotifyClient)
    client.sp = FakeSpotipy(playlist_tracks_pages=pages)

    calls = []

    def progress(current: int, total: int) -> None:
        calls.append((current, total))

    tracks = client.get_playlist_tracks("playlist123", progress_callback=progress)

    assert [(t["id"], pos) for t, pos in tracks] == [("t1", 0)]
    assert calls[-1] == (1, 1)


def test_get_playlist_tracks_returns_empty_on_empty_page() -> None:
    """Empty playlist track pages should return an empty list."""
    pages = [{"items": [], "next": None, "total": 0}]
    client = SpotifyClient.__new__(SpotifyClient)
    client.sp = FakeSpotipy(playlist_tracks_pages=pages)

    tracks = client.get_playlist_tracks("playlist123")

    assert tracks == []


def test_spotify_client_init_requires_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Init should fail fast when credentials are missing."""
    monkeypatch.setattr(spotify_client_module.config, "validate_config", lambda: False)

    with pytest.raises(ValueError, match="Spotify credentials not configured"):
        spotify_client_module.SpotifyClient()


def test_spotify_client_init_builds_spotipy_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Init should wire the Spotipy client with OAuth."""
    monkeypatch.setattr(spotify_client_module.config, "validate_config", lambda: True)
    monkeypatch.setattr(spotify_client_module.config, "SPOTIPY_CLIENT_ID", "id")
    monkeypatch.setattr(spotify_client_module.config, "SPOTIPY_CLIENT_SECRET", "secret")
    monkeypatch.setattr(
        spotify_client_module.config, "SPOTIPY_REDIRECT_URI", "http://example"
    )
    monkeypatch.setattr(spotify_client_module.config, "SPOTIFY_SCOPE", "scope")

    oauth_kwargs = {}

    def fake_oauth(**kwargs):
        oauth_kwargs.update(kwargs)
        return "oauth"

    class FakeSpotify:
        def __init__(self, auth_manager):
            self.auth_manager = auth_manager

    monkeypatch.setattr(spotify_client_module, "SpotifyOAuth", fake_oauth)
    monkeypatch.setattr(spotify_client_module.spotipy, "Spotify", FakeSpotify)

    client = spotify_client_module.SpotifyClient()

    assert isinstance(client.sp, FakeSpotify)
    assert client.sp.auth_manager == "oauth"
    assert oauth_kwargs["client_id"] == "id"
    assert oauth_kwargs["client_secret"] == "secret"
    assert oauth_kwargs["redirect_uri"] == "http://example"
    assert oauth_kwargs["scope"] == "scope"
    assert oauth_kwargs["cache_path"] == ".auth-cache"


def test_get_current_user_delegates_to_spotipy() -> None:
    """Current user fetch should delegate to the Spotipy client."""

    class UserSpotipy:
        def current_user(self) -> Dict[str, Any]:
            return {"display_name": "Tester"}

    client = SpotifyClient.__new__(SpotifyClient)
    client.sp = UserSpotipy()

    assert client.get_current_user()["display_name"] == "Tester"
