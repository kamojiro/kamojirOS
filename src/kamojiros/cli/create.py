"""create コマンド - 新しいレポートを作成."""

from __future__ import annotations

import typer
from rich.prompt import Prompt

from kamojiros.cli.formatters import console
from kamojiros.config.settings import Settings
from kamojiros.infrastructure.git.markdown_report_writer import MarkdownReportRepository
from kamojiros.models import ReportAuthor, ReportType
from kamojiros.services.report_service import ReportService


def create(  # noqa: C901
    title: str | None = typer.Option(None, "--title", "-t", help="Report title"),
    report_type: str | None = typer.Option(None, "--type", help="Report type (tech/paper/life/meta)"),
    body: str | None = typer.Option(None, "--body", "-b", help="Report body (markdown)"),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i/-I", help="Interactive mode"),
) -> None:
    """新しいレポートを作成する."""
    # インタラクティブモードの場合は対話的に入力
    if interactive and not all([title, report_type, body]):
        console.print("[bold]Create a new report[/bold]\n")

        if not title:
            title = Prompt.ask("Title")

        if not report_type:
            report_type = Prompt.ask(
                "Type",
                choices=["tech", "paper", "life", "meta"],
                default="tech",
            )

        if not tags:
            tags_input = Prompt.ask("Tags (comma-separated)", default="")
            tags = tags_input or None

        if not body:
            console.print(
                "\n[yellow]Enter body (Markdown). Press Ctrl+D (Unix) or Ctrl+Z (Windows) when done:[/yellow]"
            )
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            body = "\n".join(lines)

    # 必須項目チェック
    if not title or not report_type or not body:
        console.print("[red]Error: title, type, and body are required[/red]")
        raise typer.Exit(1)

    # タグのパース
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    # ReportType変換
    try:
        rtype = ReportType(report_type)
    except ValueError:
        console.print(f"[red]Error: Invalid type '{report_type}'. Use: tech, paper, life, or meta[/red]")
        raise typer.Exit(1) from None

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

    console.print(f"\n[green]✓ Report created: {report.meta.note_id}[/green]")
    path_str = (
        f"docs/journal/{report.meta.created_at.year}/{report.meta.created_at.month:02d}/"
        f"{report.meta.created_at.day:02d}/{report.meta.note_id}.md"
    )
    console.print(f"  Path: {path_str}")
