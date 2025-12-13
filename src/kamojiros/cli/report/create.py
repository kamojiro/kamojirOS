"""Report create cli."""

import asyncio
from typing import TYPE_CHECKING

import typer
from pydantic import HttpUrl, TypeAdapter

from kamojiros.activity_bootstrap import deep_research
from kamojiros.cli.report import app
from kamojiros.cli.report.formatters import console
from kamojiros.config.settings import Settings
from kamojiros.infrastructure.git.markdown_report_writer import MarkdownReportRepository
from kamojiros.models import ReportAuthor
from kamojiros.services.report_service import ReportService

if TYPE_CHECKING:
    from kamojiros.services.deep_research.models import DeepResearchResult


@app.command("create")
def create(
    topic: str = typer.Argument(..., help="Research Topic"),
    urls: list[str] | None = typer.Option(None, "--url", help="Research source URLs"),  # noqa: B008
    known_info: str | None = typer.Option(None, "--known-info", help="Known info"),
) -> None:
    """Deep Research を実行してレポートを作成する."""
    settings = Settings()
    if settings.notes is None:
        msg = "settings.notes must be set"
        raise RuntimeError(msg)

    async def _run() -> None:
        console.print(f"[bold cyan]Starting Deep Research on: {topic}[/bold cyan]")

        # URL変換
        valid_urls: list[HttpUrl] | None = None
        if urls:
            adapter = TypeAdapter(list[HttpUrl])
            valid_urls = adapter.validate_python(urls)

        try:
            result: DeepResearchResult = await deep_research(
                topic=topic,
                urls=valid_urls,
                known_info=known_info,
                settings=settings,
            )
            console.print("[green]Deep Research Completed![/green]")
            # レポート保存
            repo = MarkdownReportRepository(notes_repo_root=settings.notes.repo_root)
            service = ReportService(report_repo=repo)

            report, path = service.create_report(
                title=result.title,
                body=result.final_report_markdown,
                report_type=result.type,
                author=ReportAuthor.USER,  # CLI経由はユーザー扱いとする
                tags=result.tags,
            )

            console.print(f"\n[green]✓ Report created: {report.meta.note_id}[/green]")
            console.print(f"  Path: {path!r}")

        except Exception as e:
            console.print(f"[red]Deep Research failed: {e}[/red]")
            raise typer.Exit(1) from e

    asyncio.run(_run())
