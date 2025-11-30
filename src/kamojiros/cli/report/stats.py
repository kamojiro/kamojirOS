"""Stats command."""

from datetime import datetime, timedelta

import typer

from kamojiros.cli.report import app
from kamojiros.cli.report.formatters import format_stats
from kamojiros.config.settings import Settings
from kamojiros.infrastructure.git.markdown_report_writer import MarkdownReportRepository
from kamojiros.services.report_service import ReportService
from kamojiros.utils.time import JST


@app.command("stats")
def stats(
    days: int = typer.Option(30, "--days", "-d", help="集計期間（日）"),
) -> None:
    """レポートの統計情報を表示する."""
    settings = Settings()
    if settings.notes is None:
        msg = "settings.notes must be set"
        raise RuntimeError(msg)
    repo = MarkdownReportRepository(notes_repo_root=settings.notes.repo_root)
    service = ReportService(report_repo=repo)

    since = datetime.now(JST) - timedelta(days=days)
    stats = service.get_statistics(since=since)

    format_stats(stats)
