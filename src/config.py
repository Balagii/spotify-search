"""Configuration management for Spotify Library Manager."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent


def _resolve_data_dir(raw_value: str | None) -> Path:
    if not raw_value:
        return PROJECT_ROOT / "data"
    data_dir = Path(raw_value).expanduser()
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir
    return data_dir


SPOTIFY_DATA_DIR = _resolve_data_dir(os.getenv("SPOTIFY_DATA_DIR"))
DB_PATH = SPOTIFY_DATA_DIR / "spotify_library.json"

# Spotify API credentials
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv(
    "SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8000/callback"
)

# Scopes needed for the application
SPOTIFY_SCOPES = [
    "user-library-read",
    "playlist-read-private",
    "playlist-read-collaborative",
]
SPOTIFY_SCOPE = " ".join(SPOTIFY_SCOPES)


def validate_config():
    """Validate that required configuration is present."""
    if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
        return False
    return True
