"""Tests for SpotifyClient data extraction."""

import hashlib

from src.spotify_client import SpotifyClient


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
