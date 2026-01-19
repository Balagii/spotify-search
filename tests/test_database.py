"""Tests for SpotifyDatabase behavior."""

from typing import Iterator

import pytest

from src.database import SpotifyDatabase


@pytest.fixture
def db(tmp_path) -> Iterator[SpotifyDatabase]:
    """Provide a database backed by a temporary JSON file."""
    db_path = tmp_path / "spotify_library.json"
    database = SpotifyDatabase(db_path=db_path)
    yield database
    database.close()


def test_search_tracks_matches_any_field(db: SpotifyDatabase) -> None:
    """Search should match name, artist, or album."""
    db.insert_track(
        {
            "id": "t1",
            "name": "Hello",
            "artist": "Adele",
            "album": "25",
            "duration_ms": 0,
        }
    )
    db.insert_track(
        {
            "id": "t2",
            "name": "Rolling in the Deep",
            "artist": "Adele",
            "album": "21",
            "duration_ms": 0,
        }
    )

    by_name = db.search_tracks("hello")
    by_artist = db.search_tracks("adele")
    by_album = db.search_tracks("21")

    assert {t["id"] for t in by_name} == {"t1"}
    assert {t["id"] for t in by_artist} == {"t1", "t2"}
    assert {t["id"] for t in by_album} == {"t2"}


def test_search_tracks_by_properties_requires_all_fields(
    db: SpotifyDatabase,
) -> None:
    """Property search should require name, artist, and album matches."""
    db.insert_track(
        {
            "id": "t1",
            "name": "Love Song",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 0,
        }
    )
    db.insert_track(
        {
            "id": "t2",
            "name": "Love Song",
            "artist": "Artist B",
            "album": "Album A",
            "duration_ms": 0,
        }
    )

    results = db.search_tracks_by_properties("love", "artist a", "album a")
    assert {t["id"] for t in results} == {"t1"}


def test_search_tracks_by_query_and_properties_combines_filters(
    db: SpotifyDatabase,
) -> None:
    """Combined search should honor both query and property filters."""
    db.insert_track(
        {
            "id": "t1",
            "name": "Faded",
            "artist": "Alan Walker",
            "album": "Different World",
            "duration_ms": 0,
        }
    )
    db.insert_track(
        {
            "id": "t2",
            "name": "Fade",
            "artist": "Artist B",
            "album": "Different World",
            "duration_ms": 0,
        }
    )

    results = db.search_tracks_by_query_and_properties(
        query="faded",
        name_query="faded",
        artist_query="alan",
        album_query="different",
    )
    assert {t["id"] for t in results} == {"t1"}


def test_get_playlist_tracks_orders_by_position(db: SpotifyDatabase) -> None:
    """Playlist tracks should be ordered by position."""
    db.insert_track(
        {
            "id": "t1",
            "name": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 0,
        }
    )
    db.insert_track(
        {
            "id": "t2",
            "name": "Song B",
            "artist": "Artist B",
            "album": "Album B",
            "duration_ms": 0,
        }
    )
    db.insert_playlist(
        {
            "id": "p1",
            "name": "Playlist One",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 2,
        }
    )
    db.add_track_to_playlist("p1", "t1", 1)
    db.add_track_to_playlist("p1", "t2", 0)

    tracks = db.get_playlist_tracks("p1")
    assert [t["id"] for t in tracks] == ["t2", "t1"]


def test_get_playlists_for_track_includes_positions_and_liked(
    db: SpotifyDatabase,
) -> None:
    """Track playlist lookup should include duplicate positions and liked songs."""
    db.insert_track(
        {
            "id": "t1",
            "name": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 0,
        }
    )
    db.insert_playlist(
        {
            "id": "p1",
            "name": "Playlist One",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 2,
        }
    )
    db.add_track_to_playlist("p1", "t1", 0)
    db.add_track_to_playlist("p1", "t1", 2)
    db.add_saved_track("t1", "2024-01-01T00:00:00Z")

    playlists = db.get_playlists_for_track("t1")
    playlist = next(p for p in playlists if p["id"] == "p1")
    assert playlist["positions"] == [0, 2]
    assert any(p["id"] == "__saved_tracks__" for p in playlists)


def test_get_playlist_tracks_skips_missing_track_rows(
    db: SpotifyDatabase,
) -> None:
    """Missing track rows should be ignored when listing playlist tracks."""
    db.insert_track(
        {
            "id": "t1",
            "name": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 0,
        }
    )
    db.insert_playlist(
        {
            "id": "p1",
            "name": "Playlist One",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 2,
        }
    )
    db.add_track_to_playlist("p1", "missing", 0)
    db.add_track_to_playlist("p1", "t1", 1)

    tracks = db.get_playlist_tracks("p1")

    assert [t["id"] for t in tracks] == ["t1"]


def test_get_saved_tracks_skips_missing_track_rows(
    db: SpotifyDatabase,
) -> None:
    """Saved tracks with missing track data should be ignored."""
    db.add_saved_track("missing", "2024-01-01T00:00:00Z")

    assert db.get_saved_tracks() == []


def test_add_track_to_playlist_ignores_duplicate_positions(
    db: SpotifyDatabase,
) -> None:
    """Duplicate (playlist, track, position) inserts should be ignored."""
    db.insert_track(
        {
            "id": "t1",
            "name": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 0,
        }
    )
    db.insert_playlist(
        {
            "id": "p1",
            "name": "Playlist One",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
        }
    )

    db.add_track_to_playlist("p1", "t1", 0)
    db.add_track_to_playlist("p1", "t1", 0)

    assert len(db.playlist_tracks) == 1


def test_insert_track_updates_existing_row(db: SpotifyDatabase) -> None:
    """Insert should update existing tracks with the same ID."""
    db.insert_track(
        {
            "id": "t1",
            "name": "Old Name",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 0,
        }
    )
    db.insert_track(
        {
            "id": "t1",
            "name": "New Name",
            "artist": "Artist B",
            "album": "Album B",
            "duration_ms": 123,
        }
    )

    track = db.get_track("t1")

    assert track is not None
    assert track["name"] == "New Name"
    assert track["artist"] == "Artist B"


def test_get_playlists_for_track_sorts_by_name(
    db: SpotifyDatabase,
) -> None:
    """Playlist list should be sorted by name for stable output."""
    db.insert_track(
        {
            "id": "t1",
            "name": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 0,
        }
    )
    db.insert_playlist(
        {
            "id": "p1",
            "name": "Beta",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
        }
    )
    db.insert_playlist(
        {
            "id": "p2",
            "name": "Alpha",
            "description": "",
            "owner": "Owner",
            "public": False,
            "collaborative": False,
            "tracks_total": 1,
        }
    )
    db.add_track_to_playlist("p1", "t1", 0)
    db.add_track_to_playlist("p2", "t1", 0)

    playlists = db.get_playlists_for_track("t1")

    assert [p["name"] for p in playlists] == ["Alpha", "Beta"]


def test_get_saved_tracks_includes_added_at(db: SpotifyDatabase) -> None:
    """Saved tracks should include their added_at metadata."""
    db.insert_track(
        {
            "id": "t1",
            "name": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "duration_ms": 0,
        }
    )
    db.add_saved_track("t1", "2024-01-01T00:00:00Z")

    saved = db.get_saved_tracks()

    assert len(saved) == 1
    assert saved[0]["added_at"] == "2024-01-01T00:00:00Z"
