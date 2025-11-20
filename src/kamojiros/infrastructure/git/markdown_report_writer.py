"""Kamomo Notes (Git repo) に Report を保存する実装を定義するモジュール."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import ClassVar

import yaml
from pydantic import HttpUrl

from kamojiros.models import Report, ReportAuthor, ReportMeta, ReportType


@dataclass
class MarkdownReportRepository:
    """Kamomo Notes (Git repo) に Report を保存・読み出しする実装."""

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

    def find_recent(self, since: datetime) -> list[Report]:
        """指定した日時以降に作成・更新された Report を取得する."""
        reports: list[Report] = []
        docs_root = self.notes_repo_root / self.DOCS
        journal_root = docs_root / self.JOURNAL

        # since から現在までの日付ディレクトリを走査
        current_date = since.date()
        today = datetime.now(tz=since.tzinfo).date()

        while current_date <= today:
            day_dir = (
                journal_root / f"{current_date.year:04d}" / f"{current_date.month:02d}" / f"{current_date.day:02d}"
            )
            if day_dir.exists():
                for md_file in day_dir.glob("*.md"):
                    report = self._load_report(md_file)
                    if report and report.meta.updated_at >= since:
                        reports.append(report)

            current_date += timedelta(days=1)

        return reports

    def _load_report(self, file_path: Path) -> Report | None:
        try:
            content = file_path.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            fm_text = parts[1]
            body = parts[2]

            fm = yaml.safe_load(fm_text)

            meta = ReportMeta(
                note_id=fm["note_id"],
                title=fm["title"],
                created_at=datetime.fromisoformat(fm["created_at"]),
                updated_at=datetime.fromisoformat(fm["updated_at"]),
                type=ReportType(fm["type"]),
                author=ReportAuthor(fm["author"]),
                tags=fm.get("tags", []),
                source_urls=[HttpUrl(u) for u in fm.get("source_urls", [])],
            )
            return Report(meta=meta, body_markdown=body.strip())
        except Exception:
            # パースエラーなどは一旦無視（ログ出すべきだが）
            return None
