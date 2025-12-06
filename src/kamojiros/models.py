"""Kamojiros Notes のノートを表すモデル群."""


from datetime import datetime  # noqa: TC003
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import AnyHttpUrl, BaseModel, Field, HttpUrl

if TYPE_CHECKING:
    from langchain_core.documents import Document


class ReportType(StrEnum):
    """ノートのざっくり種別."""

    TECH = "tech"  # 技術メモ・実装ノート
    PAPER = "paper"  # 論文のメモ
    FOOD = "food" # 食べ物系
    LIFE = "life"  # ライフログ系
    META = "meta"  # システム・自己観察など


class ReportAuthor(StrEnum):
    """誰がこのノートを書いたか."""

    USER = "user"
    SELF_OBSERVER = "agent:self_observer"
    SUMMARIZER = "agent:summarizer"
    INGESTOR = "agent:ingestor"


class ReportMeta(BaseModel):
    """ノートのメタ情報."""

    note_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    type: ReportType
    author: ReportAuthor

    tags: list[str] = []
    source_urls: list[HttpUrl] = []


class Report(BaseModel):
    """Kamojiros Notes のノート."""

    meta: ReportMeta
    body_markdown: str


class ReportStats(BaseModel):
    """レポート統計情報."""

    total_count: int
    period_start: datetime
    period_end: datetime
    by_type: dict[str, int]
    by_author: dict[str, int]
    top_tags: dict[str, int]

    @classmethod
    def from_reports(cls, reports: list[Report], period_start: datetime, period_end: datetime) -> ReportStats:
        """レポートリストから統計を生成する."""
        type_counts: dict[str, int] = {}
        author_counts: dict[str, int] = {}
        tag_counts: dict[str, int] = {}

        for r in reports:
            # Type
            t = r.meta.type.value
            type_counts[t] = type_counts.get(t, 0) + 1

            # Author
            a = r.meta.author.value
            author_counts[a] = author_counts.get(a, 0) + 1

            # Tags
            for tag in r.meta.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # タグを頻度順にソートして上位10件
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        top_tags = dict(sorted_tags[:10])

        return cls(
            total_count=len(reports),
            period_start=period_start,
            period_end=period_end,
            by_type=type_counts,
            by_author=author_counts,
            top_tags=top_tags,
        )


class ActivitySource(StrEnum):
    """Activityの発生元サービス."""

    MISSKEY = "misskey"


class ActivityType(StrEnum):
    """Activityの種別."""

    NOTE = "note"
    REPLY = "reply"
    RENOTE = "renote"


class Activity(BaseModel):
    """外部サービスで起きたイベント（Misskey Note 等）."""

    id: str  # 内部ID（ULID/UUIDv7など）※今は note["id"] でもOK
    source: ActivitySource  # "misskey"
    source_id: str  # Misskey の note.id（= raw_data["id"]）
    source_url: AnyHttpUrl
    type: ActivityType

    created_at: datetime

    author_id: str
    author_username: str
    author_host: str | None = None

    content: str
    urls: list[AnyHttpUrl] = Field(default_factory=list)

    reply_to_source_id: str | None = None
    renote_source_id: str | None = None

    extra_metadata: dict = Field(default_factory=dict)

    raw_data: dict | None  # Misskey の生 JSON（トラブルシュート・再インデックス用）

    @classmethod
    def from_langchain_doc(cls, doc: Document) -> Activity:
        """LangChain Document から Activity を復元する."""
        m = doc.metadata

        # JSON 側から復元
        urls_raw = m.get("urls") or []
        urls = [AnyHttpUrl(url) for url in urls_raw]  # 雑に書いてるけど実際は TypeAdapter 使う方が安全

        known_keys = {
            "source",
            "activity_id",
            "source_id",
            "source_url",
            "activity_type",
            "author_id",
            "author_username",
            "author_host",
            "created_at",
            "reply_to_source_id",
            "renote_source_id",
            "urls",
        }
        extra = {k: v for k, v in m.items() if k not in known_keys}

        return cls(
            id=m["activity_id"],
            source=ActivitySource(m["source"]),
            source_id=m["source_id"],
            source_url=m["source_url"],
            type=ActivityType(m["activity_type"]),
            created_at=m["created_at"],
            author_id=m["author_id"],
            author_username=m["author_username"],
            author_host=m.get("author_host"),
            content=doc.page_content,
            urls=urls,
            reply_to_source_id=m.get("reply_to_source_id"),
            renote_source_id=m.get("renote_source_id"),
            extra_metadata=extra,
            raw_data=None,  # Document から復元時は raw_data はない
        )

class QAResult(BaseModel):
    """QA エージェントの結果."""

    question: str
    answer_markdown: str

    # RAG で使ったコンテキスト（後で Misskey/Report に埋め込めるようにしておく）
    used_activity_ids: list[str] = Field(default_factory=list)
    used_urls: list[AnyHttpUrl] = Field(default_factory=list)