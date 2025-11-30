"""Activity Index Schema for PostgreSQL Vector Store."""

from dataclasses import dataclass, field
from typing import Final

from langchain_postgres import Column

GEMINI_EMBEDDING_DIMENSION: Final[int] = 3072


@dataclass(frozen=True)
class ActivityIndexSchema:
    """Activity Indexのスキーマ定義."""

    table_name: str = "activity_index"
    vector_size: int = GEMINI_EMBEDDING_DIMENSION

    # コア列
    id_column: Column = field(default_factory=lambda: Column("id", "UUID"))
    content_column: str = "content"
    embedding_column: str = "embedding"

    # 型付きメタデータ列
    metadata_columns: tuple[Column, ...] = (
        Column("source", "TEXT"),  # Activity.source
        Column("activity_id", "TEXT"),  # Activity.id
        Column("source_id", "TEXT"),  # Activity.source_id
        Column("source_url", "TEXT"),  # Activity.source_url
        Column("activity_type", "TEXT"),  # Activity.type
        Column("author_id", "TEXT"),  # 発言者ID
        Column("author_username", "TEXT"),  # @username
        Column("author_host", "TEXT"),  # misskey.io など
        Column("created_at", "TIMESTAMPTZ"),
        Column("reply_to_source_id", "TEXT"),
        Column("renote_source_id", "TEXT"),
    )

    metadata_json_column: str = "metadata"


ACTIVITY_INDEX_SCHEMA = ActivityIndexSchema()
