"""Tests for MarkdownReportRepository."""

from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003

import pytest

from kamojiros.infrastructure.git.markdown_report_writer import MarkdownReportRepository
from kamojiros.models import Report, ReportAuthor, ReportMeta, ReportType


@pytest.fixture
def repo(tmp_path: Path) -> MarkdownReportRepository:
    """Create a temporary repository."""
    return MarkdownReportRepository(notes_repo_root=tmp_path)


def test_save_report_path(repo: MarkdownReportRepository) -> None:
    """Test that report is saved to correct path."""
    created_at = datetime(2025, 12, 25, 10, 0, 0, tzinfo=UTC)
    meta = ReportMeta(
        note_id="test_note_id",
        title="Test Report",
        date=created_at.date(),
        created_at=created_at,
        updated_at=created_at,
        type=ReportType.TECH,
        author=ReportAuthor.USER,
        tags=["test"],
        source_urls=[],
    )
    report = Report(meta=meta, body_markdown="Test Content")

    saved_path = repo.save(report)

    expected_path = repo.notes_repo_root / "docs/journal/posts/2025/12/25/test_note_id.md"
    assert saved_path == expected_path
    assert saved_path.exists()
    assert "Test Content" in saved_path.read_text(encoding="utf-8")


def test_find_recent_reports(repo: MarkdownReportRepository) -> None:
    """Test finding recent reports."""
    # Setup: Create a dummy report file in the expected directory structure
    target_dir = repo.notes_repo_root / "docs/journal/posts/2025/12/01"
    target_dir.mkdir(parents=True, exist_ok=True)

    meta_content = """
note_id: recent_note
title: Recent Report
date: 2025-12-01
created_at: 2025-12-01T10:00:00+00:00
updated_at: 2025-12-01T10:00:00+00:00
type: tech
author: user
tags: []
source_urls: []
"""
    file_content = f"---{meta_content}---\n\nRecent Content"
    (target_dir / "recent_note.md").write_text(file_content)

    # Test finding it
    since = datetime(2025, 11, 30, tzinfo=UTC)
    reports = repo.find_recent(since)

    assert len(reports) == 1
    assert reports[0].meta.note_id == "recent_note"
    assert reports[0].body_markdown == "Recent Content"
