"""Smoke tests to ensure pytest collection works in CI."""


def test_pytest_collects() -> None:
    """Verify that pytest can collect and run at least one test."""
    assert True
