"""Activity Index Query Repository."""

from typing import TYPE_CHECKING, Any

import sqlalchemy as sa

from kamojiros.models import Activity, ActivitySource, ActivityType

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncEngine


class ActivityIndexQueryRepositoryImpl:
    """Activity Index Table Query Repository."""

    def __init__(self, pg_engine: AsyncEngine, table_name: str) -> None:
        """Initialize the repository.

        Args:
            pg_engine: SQLAlchemy AsyncEngine.
            table_name: Name of the activity index table.

        """
        self._engine = pg_engine
        self._table = sa.table(
            table_name,
            sa.column("id"),
            sa.column("content"),
            sa.column("source"),
            sa.column("activity_id"),
            sa.column("source_id"),
            sa.column("source_url"),
            sa.column("activity_type"),
            sa.column("author_id"),
            sa.column("author_username"),
            sa.column("author_host"),
            sa.column("created_at"),
            sa.column("reply_to_source_id"),
            sa.column("renote_source_id"),
            sa.column("metadata"),  # JSONB
        )

    async def list_between(
        self,
        start: datetime,
        end: datetime,
        *,
        source: ActivitySource | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[Activity]:
        """指定期間の Activity をリストする."""
        stmt = sa.select(self._table).where(
            sa.and_(
                self._table.c.created_at >= start,
                self._table.c.created_at < end,
            )
        )

        if source:
            stmt = stmt.where(self._table.c.source == source.value)

        # 最新順
        stmt = stmt.order_by(self._table.c.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        async with self._engine.connect() as conn:
            result = await conn.execute(stmt)
            rows = result.mappings().all()

        return [self._row_to_activity(row) for row in rows]

    def _row_to_activity(self, row: Mapping[Any, Any]) -> Activity:
        meta = row["metadata"] or {}
        urls = meta.get("urls") or []

        # metadata カラムに入っているものは extra として扱う
        # 既知のカラム以外のものを抽出
        extra_metadata = {k: v for k, v in meta.items() if k != "urls"}

        return Activity(
            id=row["activity_id"],
            source=ActivitySource(row["source"]),
            source_id=row["source_id"],
            source_url=row["source_url"],
            type=ActivityType(row["activity_type"]),
            created_at=row["created_at"],
            author_id=row["author_id"],
            author_username=row["author_username"],
            author_host=row["author_host"],
            content=row["content"],
            urls=urls,
            reply_to_source_id=row["reply_to_source_id"],
            renote_source_id=row["renote_source_id"],
            extra_metadata=extra_metadata,
            raw_data=None,
        )
