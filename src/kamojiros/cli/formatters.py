"""CLI出力フォーマッター."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from kamojiros.models import Report

console = Console()


def format_report_table(reports: list[Report], show_body: bool = False) -> None:
    """レポートをテーブル形式で表示する."""
    table = Table(title="Reports")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Author", style="yellow")
    table.add_column("Tags", style="blue")
    table.add_column("Updated", style="white")

    if show_body:
        table.add_column("Body Preview", style="white", max_width=50)

    for report in reports:
        tags_str = ", ".join(report.meta.tags) if report.meta.tags else "-"
        updated_str = report.meta.updated_at.strftime("%Y-%m-%d %H:%M")

        row = [
            report.meta.note_id,
            report.meta.title,
            report.meta.type.value,
            report.meta.author.value,
            tags_str,
            updated_str,
        ]

        if show_body:
            body_preview = report.body_markdown[:100].replace("\n", " ")
            row.append(body_preview)

        table.add_row(*row)

    console.print(table)


def format_report_json(reports: list[Report]) -> None:
    """レポートをJSON形式で表示する."""
    data = [
        {
            "note_id": report.meta.note_id,
            "title": report.meta.title,
            "type": report.meta.type.value,
            "author": report.meta.author.value,
            "tags": report.meta.tags,
            "created_at": report.meta.created_at.isoformat(),
            "updated_at": report.meta.updated_at.isoformat(),
            "body_markdown": report.body_markdown,
        }
        for report in reports
    ]

    console.print_json(json.dumps(data, ensure_ascii=False, indent=2))


def format_stats(stats: dict) -> None:
    """統計情報を表示する."""
    console.print("\n[bold]Statistics[/bold]")
    console.print(f"Period: {stats['period_start']} to {stats['period_end']}")
    console.print(f"Total Reports: [bold]{stats['total_count']}[/bold]\n")

    # By Type
    console.print("[bold]By Type:[/bold]")
    type_table = Table()
    type_table.add_column("Type", style="green")
    type_table.add_column("Count", style="cyan")
    for type_name, count in stats["by_type"].items():
        type_table.add_row(type_name, str(count))
    console.print(type_table)

    # By Author
    console.print("\n[bold]By Author:[/bold]")
    author_table = Table()
    author_table.add_column("Author", style="yellow")
    author_table.add_column("Count", style="cyan")
    for author_name, count in stats["by_author"].items():
        author_table.add_row(author_name, str(count))
    console.print(author_table)

    # Top Tags
    if stats["top_tags"]:
        console.print("\n[bold]Top Tags:[/bold]")
        tag_table = Table()
        tag_table.add_column("Tag", style="blue")
        tag_table.add_column("Count", style="cyan")
        for tag, count in stats["top_tags"].items():
            tag_table.add_row(tag, str(count))
        console.print(tag_table)
