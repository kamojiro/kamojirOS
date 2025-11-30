"""RAG-related models."""

from typing import TYPE_CHECKING

from pydantic import BaseModel, HttpUrl

if TYPE_CHECKING:
    from datetime import datetime

    from kamojiros.models import ActivitySource


class ActivityIndexEntry(BaseModel):
    """Activity Index Entry for RAG."""

    id: str
    content: str
    source: ActivitySource
    source_id: str
    post_url: HttpUrl
    author_id: str
    author_username: str
    author_host: str | None
    created_at: datetime
    reply_to_source_id: str | None = None
    thread_root_source_id: str | None = None
    note_ids_in_thread: list[str] = []
    extra_metadata: dict = {}
