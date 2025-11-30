"""Test configuration."""

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set dummy environment variables for all tests."""
    monkeypatch.setenv("KAMOJIROS_GEMINI__API_KEY", "dummy-api-key")
    monkeypatch.setenv("KAMOJIROS_GEMINI__PROJECT_ID", "dummy-project-id")
    monkeypatch.setenv("KAMOJIROS_MISSKEY__HOST", "misskey.example.com")
    monkeypatch.setenv("KAMOJIROS_MISSKEY__ACCESS_TOKEN", "dummy-token")
    monkeypatch.setenv("KAMOJIROS_MISSKEY__KAMOJIROID_ID", "dummy-id")
    monkeypatch.setenv("KAMOJIROS_POSTGRES__USER", "postgres")
    monkeypatch.setenv("KAMOJIROS_POSTGRES__PASSWORD", "password")
