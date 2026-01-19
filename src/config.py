"""Configuration management for Spotify Library Manager."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class EnvVar:
    """Metadata for environment variables used by the app."""

    name: str
    default: str | None
    example: str | None
    required: bool
    description: str


ENV_DOCS_HEADER = [
    "# Spotify API Credentials",
    "# Get these from https://developer.spotify.com/dashboard/applications",
]

ENV_VARS = [
    EnvVar(
        name="SPOTIPY_CLIENT_ID",
        default=None,
        example="your_client_id_here",
        required=True,
        description="",
    ),
    EnvVar(
        name="SPOTIPY_CLIENT_SECRET",
        default=None,
        example="your_client_secret_here",
        required=True,
        description="",
    ),
    EnvVar(
        name="SPOTIPY_REDIRECT_URI",
        default="http://127.0.0.1:8000/callback",
        example=None,
        required=False,
        description="",
    ),
    EnvVar(
        name="SPOTIFY_DATA_DIR",
        default="data",
        example=None,
        required=False,
        description="where to store local data",
    ),
]

ENV_VAR_BY_NAME = {var.name: var for var in ENV_VARS}

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_SPOTIFY_DATA_DIR = ENV_VAR_BY_NAME["SPOTIFY_DATA_DIR"].default or "data"
DEFAULT_SPOTIPY_REDIRECT_URI = (
    ENV_VAR_BY_NAME["SPOTIPY_REDIRECT_URI"].default or "http://127.0.0.1:8000/callback"
)


def _resolve_data_dir(raw_value: str | None) -> Path:
    if not raw_value:
        raw_value = DEFAULT_SPOTIFY_DATA_DIR
    data_dir = Path(raw_value).expanduser()
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir
    return data_dir


def _get_env_value(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    return ENV_VAR_BY_NAME[name].default


SPOTIFY_DATA_DIR = _resolve_data_dir(_get_env_value("SPOTIFY_DATA_DIR"))
DB_PATH = SPOTIFY_DATA_DIR / "spotify_library.json"

# Spotify API credentials
SPOTIPY_CLIENT_ID = _get_env_value("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = _get_env_value("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = (
    _get_env_value("SPOTIPY_REDIRECT_URI") or DEFAULT_SPOTIPY_REDIRECT_URI
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
