"""Activity retrieve service."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from kamojiros.models import Activity, ActivitySource, ActivityType

if TYPE_CHECKING:
    from collections.abc import Sequence

    from langchain_core.documents import Document
    from langchain_postgres import PGVectorStore

    from kamojiros.infrastructure.rag.activity_index_query_repository import (
        ActivityIndexQueryRepositoryImpl,
    )


def _activity_from_document(doc: Document) -> Activity:
    m = doc.metadata

    data = {
        "id": m["activity_id"],
        "source": ActivitySource(m["source"]),
        "source_id": m["source_id"],
        "source_url": m["source_url"],  # AnyHttpUrl には Pydantic が変換してくれる
        "type": ActivityType(m["activity_type"]),
        "created_at": m["created_at"],
        "author_id": m["author_id"],
        "author_username": m["author_username"],
        "author_host": m.get("author_host"),
        "content": doc.page_content,
        "urls": m.get("urls") or [],
        "reply_to_source_id": m.get("reply_to_source_id"),
        "renote_source_id": m.get("renote_source_id"),
        # index からは raw_data は戻せないので None
        "raw_data": None,
    }

    return Activity.model_validate(data)


class ActivityRetrieveService:
    """Activity retriever."""

    def __init__(
        self,
        store: PGVectorStore,
        query_repo: ActivityIndexQueryRepositoryImpl | None = None,
    ) -> None:
        """Initialize."""
        self._store = store
        self._query_repo = query_repo

    async def search_recent_misskey_activity(
        self,
        query: str,
        *,
        days: int | None = 7,
        top_k: int | None = 10,
    ) -> list[Activity]:
        """Search misskey activity."""
        search_kwargs = {}
        if top_k:
            search_kwargs["k"] = top_k

        filters: list[dict] = [
            {"source": {"$eq": "misskey"}},
        ]

        # days が指定されているときだけ created_at フィルタを入れる
        if days is not None:
            if days <= 0:
                # 0 以下は「全期間」とみなす or ValueError にするかはお好みで
                pass
            else:
                now_utc = datetime.now(UTC)
                cutoff = now_utc - timedelta(days=days)
                filters.append({"created_at": {"$gte": cutoff}})

        search_kwargs["filter"] = {"$and": filters}

        retriever = self._store.as_retriever(search_kwargs=search_kwargs)
        docs: Sequence[Document] = await retriever.ainvoke(query)
        return [_activity_from_document(doc) for doc in docs]

    async def list_between_activity(
        self,
        start: datetime,
        end: datetime,
        *,
        source: ActivitySource | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Activity]:
        """List activities between start and end (SQL direct)."""
        if not self._query_repo:
            msg = "ActivityIndexQueryRepository is not configured"
            raise RuntimeError(msg)

        return list(
            await self._query_repo.list_between(
                start=start,
                end=end,
                source=source,
                limit=limit,
                offset=offset,
            )
        )
