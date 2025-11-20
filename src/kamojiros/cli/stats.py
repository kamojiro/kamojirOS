"""stats コマンド - 統計情報を表示."""

from __future__ import annotations

from datetime import datetime

import typer

from kamojiros.cli.formatters import console, format_stats
from kamojiros.config.settings import Settings
from kamojiros.core.time import JST
from kamojiros.infrastructure.git.markdown_report_writer import MarkdownReportRepository
from kamojiros.services.report_service import ReportService


def stats(
    since: str | None = typer.Option(None, "--since", help="Stats since date (YYYY-MM-DD)"),
) -> None:
    """統計情報を表示する."""
    # since をパース
    since_dt = None
    if since:
        try:
            since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=JST)
        except ValueError:
            console.print(f"[red]Error: Invalid date format '{since}'. Use YYYY-MM-DD[/red]")
            raise typer.Exit(1) from None

    # 統計取得
    settings = Settings()
    if settings.notes is None:
        msg = "settings.notes must be set"
        raise RuntimeError(msg)
    repo = MarkdownReportRepository(notes_repo_root=settings.notes.repo_root)
    service = ReportService(report_repo=repo)

    statistics = service.get_statistics(since=since_dt)

    # 出力
    format_stats(statistics)
