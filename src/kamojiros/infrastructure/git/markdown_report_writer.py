"""Kamomo Notes (Git repo) に Report を保存する実装を定義するモジュール."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

import yaml

if TYPE_CHECKING:
    from pathlib import Path

    from kamojiros.models import Report


@dataclass
class MarkdownReportWriter:
    """Kamomo Notes (Git repo) に Report を保存する実装."""

    DOCS: ClassVar[str] = "docs"
    JOURNAL: ClassVar[str] = "journal"

    notes_repo_root: Path  # Kamomo Notes を clone したルート

    def __init__(self, notes_repo_root: Path) -> None:
        """初期化."""
        self.notes_repo_root = notes_repo_root

    def save(self, report: Report) -> Path:
        """Report を保存し、生成されたパスを返す."""
        docs_root = self.notes_repo_root / self.DOCS

        meta = report.meta
        created = meta.created_at

        # docs/journal/YYYY/MM/DD/
        dir_path = docs_root / self.JOURNAL / f"{created.year:04d}" / f"{created.month:02d}" / f"{created.day:02d}"
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / f"{meta.note_id}.md"

        front_matter = {
            "note_id": meta.note_id,
            "title": meta.title,
            "created_at": meta.created_at.isoformat(),
            "updated_at": meta.updated_at.isoformat(),
            "type": meta.type.value,
            "author": meta.author.value,
            "tags": meta.tags,
            "source_urls": [str(u) for u in meta.source_urls],
        }

        fm_yaml = yaml.safe_dump(front_matter, sort_keys=False, allow_unicode=True)
        content = f"---\n{fm_yaml}---\n\n{report.body_markdown.rstrip()}\n"

        file_path.write_text(content, encoding="utf-8")
        return file_path
