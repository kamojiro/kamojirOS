"""ReportRepository のインターフェイスを定義するモジュール."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from kamojiros.models import Report


class ReportRepository(Protocol):
    """Report をどこかに保存するためのインターフェイス."""

    def save(self, report: Report) -> Path:
        """Report を保存し、生成されたパスを返す."""
        ...

    def find_recent(self, since: datetime) -> list[Report]:
        """指定した日時以降に作成・更新された Report を取得する."""
        ...
