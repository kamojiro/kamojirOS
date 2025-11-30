"""Services for syncing Misskey activities into the vector store."""

import re
from collections import defaultdict
from contextlib import suppress
from logging import Logger, getLogger
from typing import TYPE_CHECKING

from pydantic import AnyHttpUrl, TypeAdapter, ValidationError

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from langchain_postgres import PGVectorStore

    from kamojiros.infrastructure.misskey.client import MisskeyClient
    from kamojiros.infrastructure.state.file_kv_store import FileKeyValueStore
    from kamojiros.models import Activity
    from kamojiros.services.rag.activity_ingest_service import ActivityIngestService


MISSKEY_NAMESPACE = "misskey_sync"

MD_LINK_PATTERN = re.compile(r"\[[^\]]*\]\((https?://[^\s)]+)\)")


class MisskeyActivitySyncService:
    """Sync vector store with misskey notes."""

    def __init__(
        self,
        activity_ingestor: ActivityIngestService,
        vector_store: PGVectorStore,
        kv_store: FileKeyValueStore,
        misskey_client: MisskeyClient,
    ) -> None:
        """Initialize."""
        self._activity_ingestor = activity_ingestor
        self._vector_store = vector_store
        self._kv_store = kv_store
        self._misskey_client = misskey_client

        self._any_http_url_adapter = TypeAdapter(AnyHttpUrl)

        self.logger: Logger = getLogger(__name__)

    def _load_last_note_id(self, user_id: str) -> str | None:
        return self._kv_store.load(MISSKEY_NAMESPACE, user_id)

    def _save_last_note_id(self, user_id: str, last_id: str) -> None:
        self._kv_store.save(MISSKEY_NAMESPACE, user_id, last_id)

    def _collect_thread(self, root: Activity, children_by_parent: MutableMapping[str, list[Activity]]) -> Activity:
        res = root.model_copy(deep=True)
        stack: list[str] = [root.id]
        while stack:
            parent_id = stack.pop()
            children = children_by_parent.pop(parent_id, [])
            for child in children:
                res.content += child.content
                stack.append(child.id)
        return res

    def _get_urls(self, activity: Activity) -> list[AnyHttpUrl]:
        urls = MD_LINK_PATTERN.findall(activity.content)
        unique_urls = dict.fromkeys(urls)
        result: list[AnyHttpUrl] = []
        for url in unique_urls:
            with suppress(ValidationError):
                result.append(self._any_http_url_adapter.validate_python(url))
        return result

    async def sync_user(self, user_id: str, *, batch_size: int = 100) -> None:
        """ノートをベクトルストアに同期する."""
        last_id = self._load_last_note_id(user_id)

        children_by_parent: defaultdict[str, list[Activity]] = defaultdict(list)
        latest_seen_id: str | None = last_id

        processed = 0
        self.logger.info("start misskey activity sync.")

        async for activities in self._misskey_client.aiter_user_notes(
            user_id=user_id,
            since_id=last_id,  # None ならフル同期
            page_size=batch_size,
        ):
            for activity in activities:
                # 最新IDの更新（last_id 用）
                if latest_seen_id is None or activity.id > latest_seen_id:
                    latest_seen_id = activity.id

                if activity.reply_to_source_id:
                    # 親がまだ出てきていないので、いったん pending に積む
                    children_by_parent[activity.reply_to_source_id].append(activity)
                    continue

                # reply_id がない → スレッドの root とみなす
                collected_activity = self._collect_thread(activity, children_by_parent)

                # urls を付加する
                collected_activity.urls.extend(self._get_urls(collected_activity))

                # ここで thread_activities を ActivityIngestService に渡す
                await self._activity_ingestor.ingest_activities([collected_activity])

            processed += len(activities)
            msg = f"Processed activities: {processed}"
            self.logger.info(msg)

        # ループが終わっても親が見つからなかった「孤児返信」が残る
        # （親が古すぎて今回の同期レンジの外にいるケースなど）
        for orphan_children in children_by_parent.values():
            # ひとまず単独ポストとして入れてしまう
            await self._activity_ingestor.ingest_activities(orphan_children)

        if latest_seen_id is not None and latest_seen_id != last_id:
            self._save_last_note_id(user_id, latest_seen_id)
