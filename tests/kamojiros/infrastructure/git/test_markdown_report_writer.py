"""MarkdownReportWriter の単体テスト."""

from datetime import datetime
from typing import TYPE_CHECKING

import yaml

from kamojiros.core.time import JST
from kamojiros.infrastructure.git.markdown_report_writer import MarkdownReportWriter
from kamojiros.models import Report, ReportAuthor, ReportMeta, ReportType

if TYPE_CHECKING:
    from pathlib import Path


def _make_report(created_at: datetime) -> Report:
    """テスト用の Report を作成するヘルパー."""
    meta = ReportMeta(
        note_id="2025-11-17-2100-meta-self-observer-test",
        title="self_observer v0 テストノート",
        created_at=created_at,
        updated_at=created_at,
        type=ReportType.META,
        author=ReportAuthor.SELF_OBSERVER,
        tags=["test", "self-observer"],
        source_urls=[],
    )
    body = "# self_observer v0 テスト\n\n本文です。"
    return Report(meta=meta, body_markdown=body)


def test_save_creates_expected_path_and_file(tmp_path: Path) -> None:
    """docs/journal/YYYY/MM/DD/note_id.md が作成されることを検証する."""
    notes_repo_root = tmp_path / "notes"
    report = _make_report(datetime(2025, 11, 17, 21, 0, 0, tzinfo=JST))

    writer = MarkdownReportWriter(notes_repo_root=notes_repo_root)
    path = writer.save(report)

    # ファイルパスの検証
    expected_dir = notes_repo_root / "docs" / "journal" / "2025" / "11" / "17"
    assert path.parent == expected_dir
    assert path.name == "2025-11-17-2100-meta-self-observer-test.md"

    # ファイルが実際に存在すること
    assert path.is_file()


def test_save_writes_front_matter_and_body(tmp_path: Path) -> None:
    """YAML フロントマターと本文が期待どおりに書き込まれることを検証する."""
    notes_repo_root = tmp_path / "notes"
    created_at = datetime(2025, 11, 17, 21, 0, 0, tzinfo=JST)
    report = _make_report(created_at)

    writer = MarkdownReportWriter(notes_repo_root=notes_repo_root)
    path = writer.save(report)

    content = path.read_text(encoding="utf-8")

    # 先頭がフロントマターで始まること
    assert content.startswith("---\n")

    # フロントマターと本文を分割
    # 形式: '---\n' + YAML + '---\n\n' + body # noqa: ERA001
    _, rest = content.split("---\n", 1)
    yaml_part, body_part = rest.split("---\n\n", 1)

    front_matter = yaml.safe_load(yaml_part)

    # フロントマターの中身の検証
    assert front_matter["note_id"] == report.meta.note_id
    assert front_matter["title"] == report.meta.title
    assert front_matter["created_at"] == report.meta.created_at.isoformat()
    assert front_matter["updated_at"] == report.meta.updated_at.isoformat()
    assert front_matter["type"] == report.meta.type.value
    assert front_matter["author"] == report.meta.author.value
    assert front_matter["tags"] == report.meta.tags
    assert front_matter["source_urls"] == [str(u) for u in report.meta.source_urls]

    # 本文の検証（末尾の改行 1 つだけを許容）
    assert body_part == report.body_markdown.rstrip() + "\n"
