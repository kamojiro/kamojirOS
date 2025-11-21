"""Kamojiros Notes のノートを表すモデル群."""

from datetime import datetime  # noqa: TC003
from enum import StrEnum

from pydantic import BaseModel, HttpUrl


class ReportType(StrEnum):
    """ノートのざっくり種別."""

    TECH = "tech"  # 技術メモ・実装ノート
    PAPER = "paper"  # 論文のメモ
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


class ActivityType(StrEnum):
    """アクティビティの種類."""

    NOTE = "note"


class Activity(BaseModel):
    """外部サービスからのアクティビティ (Misskey Note等)."""

    id: str
    type: ActivityType
    content: str
    created_at: datetime
    source_url: HttpUrl
    raw_data: dict  # 元のJSONを保持
