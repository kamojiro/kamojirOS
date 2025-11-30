"""Tests."""

from contextlib import suppress
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from sqlalchemy.exc import ProgrammingError

from kamojiros.config.settings import Settings
from kamojiros.infrastructure.misskey.client import MisskeyClient
from kamojiros.infrastructure.rag.activity_store import ainit_activity_index_table, create_activity_vector_store
from kamojiros.infrastructure.rag.gemini_embeddings import GeminiEmbeddings
from kamojiros.infrastructure.state.file_kv_store import FileKeyValueStore
from kamojiros.services.misskey.activity_sync_service import MISSKEY_NAMESPACE, MisskeyActivitySyncService
from kamojiros.services.rag.activity_ingest_service import ActivityIngestService
from kamojiros.services.rag.activity_retrieve_service import ActivityRetrieveService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

    from langchain_postgres import PGVectorStore


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Settings for test."""
    settings = Settings()
    settings.postgres.database = "kamojiros_test"
    settings.state_store.base_dir = tmp_path
    return settings


@pytest_asyncio.fixture
async def test_vector_store(test_settings: Settings) -> AsyncGenerator[PGVectorStore]:
    """."""
    embeddings = GeminiEmbeddings.create(test_settings.gemini)
    with suppress(ProgrammingError):
        await ainit_activity_index_table(test_settings.postgres)
    vector_store = await create_activity_vector_store(test_settings.postgres, embeddings)

    try:
        yield vector_store
    finally:
        await vector_store.adrop_vector_index()


def get_since_id(misskey_client: MisskeyClient, user_id: str, *, limit: int = 100) -> str:
    """Get 100th note id."""
    activities = misskey_client.fetch_notes(user_id, limit=limit)
    return activities[-1].source_id


@pytest.mark.gemini_required
@pytest.mark.postgres_required
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires running PostgreSQL")
async def test_activity_sync_service_sync_user(test_settings: Settings, test_vector_store: PGVectorStore) -> None:
    """Exp."""
    kv_store = FileKeyValueStore(test_settings.state_store)
    misskey_client = MisskeyClient.create(test_settings.misskey)
    kamojiroid_id = test_settings.misskey.kamojiroid_id
    test_size = 100
    batch_size = 10
    since_id = get_since_id(misskey_client, kamojiroid_id, limit=test_size)
    kv_store.save(MISSKEY_NAMESPACE, kamojiroid_id, since_id)

    activity_ingestor = ActivityIngestService(test_vector_store)
    activity_sync_service = MisskeyActivitySyncService(activity_ingestor, test_vector_store, kv_store, misskey_client)
    activity_retrieve_service = ActivityRetrieveService(test_vector_store)

    await activity_sync_service.sync_user(kamojiroid_id, batch_size=batch_size)
    await activity_retrieve_service.search_recent_misskey_activity("A", days=None, top_k=None)
