"""Unit tests for MisskeyClient."""

from typing import Any
from unittest.mock import patch

import pytest

from kamojiros.infrastructure.misskey.client import MisskeyClient
from kamojiros.models import ActivityType


@pytest.fixture
def mock_response() -> list[dict[str, Any]]:
    """Return a mock response for fetch_notes."""
    return [
        {
            "id": "note1",
            "createdAt": "2023-01-01T00:00:00.000Z",
            "text": "Hello Misskey",
            "user": {"username": "user1"},
        },
        {
            "id": "note2",
            "createdAt": "2023-01-02T00:00:00.000Z",
            "text": None,  # Image only note
            "user": {"username": "user2"},
        },
    ]


def test_fetch_notes(mock_response: list[dict[str, Any]]) -> None:
    """Test fetching notes."""
    with patch("httpx.Client") as mock_client_cls:
        # Mock the client instance and its post method
        mock_instance = mock_client_cls.return_value
        mock_instance.post.return_value.json.return_value = mock_response
        mock_instance.post.return_value.raise_for_status.return_value = None

        client = MisskeyClient(url="https://misskey.io", token="dummy_token")  # noqa: S106
        activities = client.fetch_notes(limit=2)

        assert len(activities) == 2  # noqa: PLR2004

        # Check first activity
        assert activities[0].id == "note1"
        assert activities[0].type == ActivityType.NOTE
        assert activities[0].content == "Hello Misskey"
        assert str(activities[0].source_url) == "https://misskey.io/notes/note1"

        # Check second activity (empty text handling)
        assert activities[1].id == "note2"
        assert activities[1].content == ""

        # Verify API call
        mock_instance.post.assert_called_once()
        args, kwargs = mock_instance.post.call_args
        assert args[0] == "/api/notes/local-timeline"
        assert kwargs["json"]["limit"] == 2  # noqa: PLR2004
        assert kwargs["json"]["i"] == "dummy_token"


def test_fetch_notes_with_since_id() -> None:
    """Test fetching notes with since_id."""
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.post.return_value.json.return_value = []

        client = MisskeyClient(url="https://misskey.io")
        client.fetch_notes(since_id="prev_id")

        _, kwargs = mock_instance.post.call_args
        assert kwargs["json"]["sinceId"] == "prev_id"
