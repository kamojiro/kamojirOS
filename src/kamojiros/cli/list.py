"""list コマンド - レポート一覧を表示."""

from __future__ import annotations

from datetime import datetime

import typer

from kamojiros.cli.formatters import console, format_report_json, format_report_table
from kamojiros.config.settings import Settings
from kamojiros.core.time import JST
from kamojiros.infrastructure.git.markdown_report_writer import MarkdownReportRepository
from kamojiros.models import ReportAuthor, ReportType
from kamojiros.services.report_service import ReportService


def list_reports(  # noqa: C901
    limit: int = typer.Option(10, "--limit", "-n", help="Number of reports to show"),
    since: str | None = typer.Option(None, "--since", help="Show reports since date (YYYY-MM-DD)"),
    report_type: str | None = typer.Option(None, "--type", help="Filter by type (tech/paper/life/meta)"),
    author: str | None = typer.Option(None, "--author", help="Filter by author"),
    tags: str | None = typer.Option(None, "--tags", help="Filter by tags (comma-separated)"),
    json_format: bool = typer.Option(False, "--json", help="Output as JSON"),
    show_body: bool = typer.Option(False, "--show-body", help="Show body preview in table"),
) -> None:
    """レポート一覧を表示する."""
    # since をパース
    since_dt = None
    if since:
        try:
            since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=JST)
        except ValueError:
            console.print(f"[red]Error: Invalid date format '{since}'. Use YYYY-MM-DD[/red]")
            raise typer.Exit(1) from None

    # report_type をパース
    rtype = None
    if report_type:
        try:
            rtype = ReportType(report_type)
        except ValueError:
            console.print(f"[red]Error: Invalid type '{report_type}'. Use: tech, paper, life, or meta[/red]")
            raise typer.Exit(1) from None

    # author をパース
    rauthor = None
    if author:
        try:
            rauthor = ReportAuthor(author)
        except ValueError:
            console.print(f"[red]Error: Invalid author '{author}'[/red]")
            raise typer.Exit(1) from None

    # tags をパース
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]

    # レポート取得
    settings = Settings()
    if settings.notes is None:
        msg = "settings.notes must be set"
        raise RuntimeError(msg)
    repo = MarkdownReportRepository(notes_repo_root=settings.notes.repo_root)
    service = ReportService(report_repo=repo)

    reports = service.list_reports(
        limit=limit,
        since=since_dt,
        report_type=rtype,
        author=rauthor,
        tags=tag_list,
    )

    if not reports:
        console.print("[yellow]No reports found[/yellow]")
        return

    # 出力
    if json_format:
        format_report_json(reports)
    else:
        format_report_table(reports, show_body=show_body)
        console.print(f"\n[dim]Showing {len(reports)} report(s)[/dim]")
