"""Kamomo Notes のノートを表すモデル群."""

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
    """Kamomo Notes のノート."""

    meta: ReportMeta
    body_markdown: str
