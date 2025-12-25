"""
Pytest configuration and fixtures for the test suite.
"""

import pytest


@pytest.fixture
def sample_track():
    """Sample track data for testing."""
    return {
        "name": "Test Track",
        "artists": [{"name": "Test Artist"}],
        "album": {"name": "Test Album"},
        "duration_ms": 180000,
        "id": "test123",
    }


@pytest.fixture
def sample_playlist():
    """Sample playlist data for testing."""
    return {
        "name": "Test Playlist",
        "id": "playlist123",
        "snapshot_id": "snapshot123",
        "tracks": {"total": 10},
    }
