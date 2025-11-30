"""Activity Ingest Service."""

import uuid
from typing import TYPE_CHECKING

from langchain_core.documents import Document

from kamojiros.models import ActivitySource
from kamojiros.services.misskey.activity_sync_service import MISSKEY_NAMESPACE

if TYPE_CHECKING:
    from collections.abc import Sequence

    from langchain_postgres import PGVectorStore

    from kamojiros.models import Activity

MISSKEY_NAMESPACE_UUID = uuid.uuid5(uuid.NAMESPACE_DNS, MISSKEY_NAMESPACE)


def create_id(activity: Activity) -> str:
    """Create uuid."""
    _id: uuid.UUID | None = None
    if activity.source == ActivitySource.MISSKEY:
        _id = uuid.uuid5(MISSKEY_NAMESPACE_UUID, activity.source_id)
    if isinstance(_id, uuid.UUID):
        return str(_id)
    msg = f"Unknown activity source: {activity.source}"
    raise ValueError(msg)


def activity_to_document(activity: Activity) -> Document:
    """Activity を activity_index テーブルに対応する Document に変換."""
    metadata = {
        "source": activity.source.value,
        "activity_id": activity.id,
        "source_id": activity.source_id,
        "source_url": str(activity.source_url),
        "activity_type": activity.type.value,
        "author_id": activity.author_id,
        "author_username": activity.author_username,
        "author_host": activity.author_host,
        "created_at": activity.created_at,
        "reply_to_source_id": activity.reply_to_source_id,
        "renote_source_id": activity.renote_source_id,
        # ここから下は metadata_json_column に入る
        "urls": [str(u) for u in activity.urls],
    }
    return Document(
        page_content=activity.content,
        id=create_id(activity),
        metadata=metadata,
    )


class ActivityIngestService:
    """Activity Ingest Service."""

    def __init__(self, vector_store: PGVectorStore) -> None:
        """Initialize."""
        self._vector_store = vector_store

    async def ingest_activities(
        self,
        activities: Sequence[Activity],
    ) -> None:
        """Ingest activity to vector store."""
        docs = [activity_to_document(a) for a in activities]
        if not docs:
            return
        await self._vector_store.aadd_documents(docs)
