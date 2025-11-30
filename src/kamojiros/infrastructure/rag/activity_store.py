"""Activity Index Vector Store Factory for PostgreSQL."""

from typing import TYPE_CHECKING

from langchain_postgres import PGVectorStore
from psycopg.errors import DuplicateTable
from sqlalchemy.exc import ProgrammingError

from kamojiros.infrastructure.rag.activity_schema import ACTIVITY_INDEX_SCHEMA
from kamojiros.infrastructure.rag.db import create_pg_engine

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings

    from kamojiros.config.settings import PostgreSQLSettings


def _activity_table_name(pg_settings: PostgreSQLSettings) -> str:
    return pg_settings.activity_index_name or ACTIVITY_INDEX_SCHEMA.table_name


async def ainit_activity_index_table(pg_settings: PostgreSQLSettings) -> None:
    """activity_index テーブルを作成（初期化）する."""
    pg_engine = await create_pg_engine(pg_settings)
    try:
        await pg_engine.ainit_vectorstore_table(
            table_name=_activity_table_name(pg_settings),
            vector_size=ACTIVITY_INDEX_SCHEMA.vector_size,
            id_column=ACTIVITY_INDEX_SCHEMA.id_column,
            content_column=ACTIVITY_INDEX_SCHEMA.content_column,
            embedding_column=ACTIVITY_INDEX_SCHEMA.embedding_column,
            metadata_columns=ACTIVITY_INDEX_SCHEMA.metadata_columns,
            metadata_json_column=ACTIVITY_INDEX_SCHEMA.metadata_json_column,
        )
    except ProgrammingError as e:
        # psycopg の DuplicateTable だけ握りつぶす
        orig = getattr(e, "orig", None)
        if isinstance(orig, DuplicateTable):
            # すでに初期化済みなので無視
            return
        raise


async def create_activity_vector_store(
    pg_settings: PostgreSQLSettings,
    embeddings: Embeddings,
) -> PGVectorStore:
    """activity_index 用 PGVectorStore を構築する factory 関数."""
    pg_engine = await create_pg_engine(pg_settings)

    return await PGVectorStore.create(
        engine=pg_engine,
        table_name=_activity_table_name(pg_settings),
        embedding_service=embeddings,
        id_column=ACTIVITY_INDEX_SCHEMA.id_column.name,
        content_column=ACTIVITY_INDEX_SCHEMA.content_column,
        embedding_column=ACTIVITY_INDEX_SCHEMA.embedding_column,
        metadata_columns=[c.name for c in ACTIVITY_INDEX_SCHEMA.metadata_columns],
        metadata_json_column=ACTIVITY_INDEX_SCHEMA.metadata_json_column,
    )
