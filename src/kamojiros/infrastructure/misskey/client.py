"""Misskey API Client module."""

from datetime import datetime

import httpx
from pydantic import HttpUrl

from kamojiros.models import Activity, ActivityType


class MisskeyClient:
    """Misskey API Client."""

    def __init__(self, url: str, token: str | None = None) -> None:
        """Initialize Misskey Client."""
        self.url = url.rstrip("/")
        self.token = token
        self.client = httpx.Client(base_url=self.url, timeout=10.0)

    def fetch_notes(self, limit: int = 10, since_id: str | None = None) -> list[Activity]:
        """Fetch notes from local timeline."""
        endpoint = "/api/notes/local-timeline"
        payload = {
            "limit": limit,
            "i": self.token,
        }
        if since_id:
            payload["sinceId"] = since_id

        response = self.client.post(endpoint, json=payload)
        response.raise_for_status()
        data = response.json()

        return [self._to_activity(note) for note in data]

    def _to_activity(self, note: dict) -> Activity:
        """Convert Misskey note to Activity."""
        # Misskey returns ISO format like "2023-01-01T00:00:00.000Z"
        # datetime.fromisoformat handles "Z" in Python 3.11+, but for safety/older versions we might replace it.
        # However, ruff complained about unnecessary replacement if it's standard.
        # Let's try standard fromisoformat first, if it fails on Z in older python we handle it.
        # Assuming Python 3.11+ based on project context.
        created_at_str = note["createdAt"]
        if created_at_str.endswith("Z"):
            created_at_str = created_at_str[:-1] + "+00:00"

        return Activity(
            id=note["id"],
            type=ActivityType.NOTE,
            content=note.get("text") or "",
            created_at=datetime.fromisoformat(created_at_str),
            source_url=HttpUrl(f"{self.url}/notes/{note['id']}"),
            raw_data=note,
        )
