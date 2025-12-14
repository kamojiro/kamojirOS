"""Theme suggest CLI command."""

import asyncio
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.table import Table

from kamojiros.activity_bootstrap import build_activity_stack
from kamojiros.cli.theme import app
from kamojiros.config.settings import Settings

if TYPE_CHECKING:
    from kamojiros.models import ThemeSuggestion

console = Console()


@app.command("suggest")
def suggest(
    query: str | None = typer.Argument(None, help="Query to determine theme kind"),
) -> None:
    """Suggest themes for deep research."""
    settings = Settings()

    async def _run() -> None:
        console.print("[bold cyan]Generating theme suggestions...[/bold cyan]")

        stack = await build_activity_stack(settings)
        suggestions: list[ThemeSuggestion] = await stack.theme.suggest(query)

        # テーブル表示
        table = Table(title="Theme Suggestions")
        table.add_column("No.", style="cyan", justify="right")
        table.add_column("Topic", style="green")
        table.add_column("Rationale", style="yellow")
        table.add_column("URLs", justify="right")
        table.add_column("Confidence", justify="right")

        for i, suggestion in enumerate(suggestions, 1):
            table.add_row(
                str(i),
                suggestion.topic,
                suggestion.rationale,
                str(len(suggestion.urls)),
                f"{suggestion.confidence:.2f}",
            )

        console.print(table)

    asyncio.run(_run())
