"""ReportRepository のインターフェイスを定義するモジュール."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from kamojiros.models import Report


class ReportRepository(Protocol):
    """Report をどこかに保存するためのインターフェイス."""

    def save(self, report: Report) -> Path:
        """Report を保存し、生成されたパスを返す."""
        ...
