"""search コマンド - レポートをキーワード検索."""

from __future__ import annotations

import typer

from kamojiros.cli.formatters import console, format_report_table
from kamojiros.config.settings import Settings
from kamojiros.infrastructure.git.markdown_report_writer import MarkdownReportRepository
from kamojiros.services.report_service import ReportService


def search(
    keyword: str = typer.Argument(..., help="Search keyword"),
    title_only: bool = typer.Option(False, "--title-only", help="Search only in titles"),
    body_only: bool = typer.Option(False, "--body-only", help="Search only in body"),
    tags_only: bool = typer.Option(False, "--tags-only", help="Search only in tags"),
) -> None:
    """キーワードでレポートを検索する."""
    # 検索範囲の決定
    search_in_title = not body_only and not tags_only
    search_in_body = not title_only and not tags_only
    search_in_tags = not title_only and not body_only

    # レポート検索
    settings = Settings()
    repo = MarkdownReportRepository(notes_repo_root=settings.notes.repo_root)
    service = ReportService(report_repo=repo)

    reports = service.search_reports(
        keyword=keyword,
        search_in_title=search_in_title,
        search_in_body=search_in_body,
        search_in_tags=search_in_tags,
    )

    if not reports:
        console.print(f"[yellow]No reports found for keyword: '{keyword}'[/yellow]")
        return

    console.print(f"[bold]Search Results for '{keyword}'[/bold]\n")
    format_report_table(reports, show_body=True)
    console.print(f"\n[dim]Found {len(reports)} report(s)[/dim]")
