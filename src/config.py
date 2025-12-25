"""Configuration management for Spotify Library Manager."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "spotify_library.json"

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
