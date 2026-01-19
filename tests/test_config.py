"""Tests for configuration validation."""

import pytest

from src import config


@pytest.mark.parametrize(
    ("client_id", "client_secret", "expected"),
    [
        ("id", "secret", True),
        (None, "secret", False),
        ("id", None, False),
        (None, None, False),
    ],
)
def test_validate_config_requires_credentials(
    monkeypatch: pytest.MonkeyPatch,
    client_id: str | None,
    client_secret: str | None,
    expected: bool,
) -> None:
    """validate_config should require both client ID and secret."""
    monkeypatch.setattr(config, "SPOTIPY_CLIENT_ID", client_id)
    monkeypatch.setattr(config, "SPOTIPY_CLIENT_SECRET", client_secret)

    assert config.validate_config() is expected
