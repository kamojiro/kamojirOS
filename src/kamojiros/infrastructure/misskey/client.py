"""Misskey API Client module."""

import asyncio
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Self

import httpx
from pydantic import AnyHttpUrl

from kamojiros.models import Activity, ActivitySource, ActivityType

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from kamojiros.config.settings import MisskeySettings


class MisskeyClient:
    """Misskey API Client."""

    def __init__(self, host: str, token: str) -> None:
        """Initialize Misskey Client."""
        self.url = f"https://{host}"
        self.token = token
        self.client = httpx.Client(base_url=self.url, timeout=10.0)

    @classmethod
    def create(cls, settings: MisskeySettings) -> Self:
        """Create MisskeyClient from settings."""
        return cls(host=settings.host, token=settings.access_token)

    def get_id_by_name(self, username: str) -> str:
        """Get user ID by username."""
        headers = {"Content-Type": "application/json"}
        response = self.client.post("/api/users/show", json={"username": username, "i": self.token}, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["id"]

    def fetch_notes(
        self, user_id: str, *, limit: int = 30, since_id: str | None = None, until_id: str | None = None
    ) -> list[Activity]:
        """Fetch notes from local timeline."""
        headers = {"Content-Type": "application/json"}
        endpoint = "/api/users/notes"
        payload = {
            "userId": user_id,
            "limit": limit,
            "i": self.token,
        }
        if since_id:
            payload["sinceId"] = since_id
        if until_id:
            payload["untilId"] = until_id

        response = self.client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return [self._to_activity(note) for note in data]

    async def _afetch_notes(
        self,
        user_id: str,
        *,
        limit: int = 30,
        since_id: str | None = None,
        until_id: str | None = None,
    ) -> list[Activity]:
        """Async fetch notes."""
        loop = asyncio.get_running_loop()
        func = partial(
            self.fetch_notes,
            user_id,
            limit=limit,
            since_id=since_id,
            until_id=until_id,
        )
        return await loop.run_in_executor(None, func)

    async def aiter_user_notes(
        self,
        user_id: str,
        *,
        since_id: str | None = None,
        page_size: int = 100,
    ) -> AsyncGenerator[list[Activity]]:
        """since_id 以降のノートを新しい順にすべて返す.

        - since_id is None → 全履歴（フル同期）
        - since_id is not None → since_id より新しい分だけ（増分同期）

        Misskey の挙動は `sinceId < id < untilId` であり、
        since_id は固定、until_id をだんだん古くしていく。
        """
        upper: str | None = None  # 「この id より古い側」を切り落とす上限

        while True:
            activities = await self._afetch_notes(
                user_id,
                limit=page_size,
                since_id=since_id,
                until_id=upper,
            )
            if not activities:
                break

            # Misskey は新しい順（id 降順）で返す前提
            yield activities

            # このバッチの中でいちばん古い id を、次の upper にする
            oldest = activities[-1]
            upper = oldest.id

    def _to_activity(self, note: dict) -> Activity:
        """Convert Misskey note JSON to Activity."""
        # createdAt
        created_at_str = note["createdAt"]
        if created_at_str.endswith("Z"):
            created_at_str = created_at_str[:-1] + "+00:00"
        created_at = datetime.fromisoformat(created_at_str)

        # user
        user = note["user"]
        username = user["username"]
        author_host = user.get("host")
        author_id = user["id"]

        # URL
        # ローカル Misskey の URL を canonical とみなす
        # remote note の場合はほんとはもう一工夫いるけど、まずはこれで。
        url = AnyHttpUrl(f"{self.url}/notes/{note['id']}")

        return Activity(
            id=note["id"],
            source=ActivitySource.MISSKEY,
            source_id=note["id"],
            source_url=url,
            type=ActivityType.NOTE,
            created_at=created_at,
            author_id=author_id,
            author_username=username,
            author_host=author_host,
            content=note.get("text") or "",
            urls=[],
            reply_to_source_id=note.get("replyId"),
            renote_source_id=note.get("renoteId"),
            raw_data=note,
        )
