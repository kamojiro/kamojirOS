"""create コマンド - 新しいレポートを作成."""

import typer
from rich.prompt import Prompt

from kamojiros.cli.report import app
from kamojiros.cli.report.formatters import console
from kamojiros.config.settings import Settings
from kamojiros.infrastructure.git.markdown_report_writer import MarkdownReportRepository
from kamojiros.models import ReportAuthor, ReportType
from kamojiros.services.report_service import ReportService


@app.command("create")
def create(  # noqa: C901
    theme: str = typer.Option(None, "--title", "-t", help="Report title"),
) -> None:
    """新しいレポートを作成する."""
    # レポート保存
    settings = Settings()
    if settings.notes is None:
        msg = "settings.notes must be set"
        raise RuntimeError(msg)
    repo = MarkdownReportRepository(notes_repo_root=settings.notes.repo_root)
    service = ReportService(report_repo=repo)

    report = service.create_report(
        title=title,
        body=body,
        report_type=rtype,
        author=ReportAuthor.USER,
        tags=tag_list,
    )

    # console.print(f"\n[green]✓ Report created: {report.meta.note_id}[/green]")
    # path_str = (
    #     f"docs/journal/{report.meta.created_at.year}/{report.meta.created_at.month:02d}/"
    #     f"{report.meta.created_at.day:02d}/{report.meta.note_id}.md"
    # )
    # console.print(f"  Path: {path_str}")
