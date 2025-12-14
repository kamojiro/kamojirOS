"""Aggregate calling settings and initialize infrastructure and service."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from langchain_postgres import PGEngine
from langchain_postgres.v2.vectorstores import PGVectorStore

from kamojiros.config.settings import Settings
from kamojiros.infrastructure.misskey.client import MisskeyClient
from kamojiros.infrastructure.rag.activity_index_query_repository import (
    ActivityIndexQueryRepositoryImpl,
)
from kamojiros.infrastructure.rag.activity_store import (
    ainit_activity_index_table,
    create_activity_table_name,
    create_activity_vector_store,
)
from kamojiros.infrastructure.rag.db import create_async_engine_from_settings
from kamojiros.infrastructure.rag.gemini_embeddings import GeminiEmbeddings
from kamojiros.infrastructure.state.file_kv_store import FileKeyValueStore
from kamojiros.services.deep_research.deep_research_service import DeepResearchService
from kamojiros.services.misskey.activity_sync_service import MisskeyActivitySyncService
from kamojiros.services.qa_service import QAService
from kamojiros.services.rag.activity_ingest_service import ActivityIngestService
from kamojiros.services.rag.activity_retrieve_service import ActivityRetrieveService

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings
    from langchain_postgres import PGVectorStore
    from pydantic import HttpUrl

    from kamojiros.models import Activity, QAResult
    from kamojiros.services.deep_research.models import DeepResearchResult


@dataclass
class ActivityStack:
    """Activity 関連の依存をまとめた束."""

    settings: Settings
    embeddings: Embeddings
    store: PGVectorStore
    ingest: ActivityIngestService
    sync: MisskeyActivitySyncService
    retrieve: ActivityRetrieveService
    qa: QAService
    deep_research: DeepResearchService


async def build_activity_stack(settings: Settings | None = None) -> ActivityStack:
    """Activity 用の依存を全部組み立てる."""
    settings = settings or Settings()

    # Embeddings
    embeddings = GeminiEmbeddings.create(settings.gemini)

    # VectorStore 初期化
    # VectorStore 初期化
    activity_table_name = create_activity_table_name(settings.postgres)
    await ainit_activity_index_table(settings.postgres, activity_table_name)

    # Engine を作成して共有
    async_engine = create_async_engine_from_settings(settings.postgres)
    pg_engine = PGEngine.from_engine(async_engine)

    store: PGVectorStore = await create_activity_vector_store(pg_engine, embeddings, activity_table_name)

    # QueryRepository 作成
    query_repo = ActivityIndexQueryRepositoryImpl(async_engine, activity_table_name)

    # Services
    ingest = ActivityIngestService(store)
    kv_store = FileKeyValueStore(settings.state_store)
    misskey_client = MisskeyClient.create(settings.misskey)
    sync = MisskeyActivitySyncService(
        activity_ingestor=ingest,
        vector_store=store,
        kv_store=kv_store,
        misskey_client=misskey_client,
    )
    retrieve = ActivityRetrieveService(store, query_repo=query_repo)

    qa = QAService.create(settings.gemini, settings.searxng, retrieve, misskey_client)

    deep_research = DeepResearchService.create(settings.gemini, settings.searxng, retrieve)

    return ActivityStack(
        settings=settings,
        embeddings=embeddings,
        store=store,
        ingest=ingest,
        sync=sync,
        retrieve=retrieve,
        qa=qa,
        deep_research=deep_research,
    )


async def sync_misskey_activity(
    *,
    user_id: str | None = None,
    settings: Settings | None = None,
    batch_size: int = 100,
    full: bool = False,
) -> None:
    """Misskey のノートを activity ベクトルストアに同期する."""
    stack = await build_activity_stack(settings)
    settings = stack.settings

    user_id = user_id or settings.misskey.kamojiroid_id

    # full の扱いは、KV ストアにメソッドを足してもよいし、
    # namespace を変えるなどでもよい
    if full:
        # 例: FileKeyValueStore に delete(namespace, key) を生やして使う
        kv = FileKeyValueStore(settings.state_store)
        kv.delete(namespace="misskey", key=user_id)

    await stack.sync.sync_user(user_id=user_id, batch_size=batch_size)


async def search_misskey_activity(
    query: str,
    *,
    settings: Settings | None = None,
    days: int = 7,
    top_k: int = 16,
) -> list[Activity]:
    """Misskey Activity をベクトル検索する."""
    stack = await build_activity_stack(settings)
    return await stack.retrieve.search_recent_misskey_activity(
        query,
        days=days,
        top_k=top_k,
    )


async def qa_ask(query: str, *, settings: Settings | None = None) -> QAResult:
    """Ask."""
    stack = await build_activity_stack(settings)
    return await stack.qa.ask(query)


async def deep_research(
    topic: str, *, urls: list[HttpUrl] | None = None, known_info: str | None = None, settings: Settings | None = None
) -> DeepResearchResult:
    """Deep research."""
    stack = await build_activity_stack(settings)
    return await stack.deep_research.run_deep_research(topic=topic, urls=urls, known_info=known_info)
