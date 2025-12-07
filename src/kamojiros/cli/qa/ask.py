"""QA ask CLI."""

import asyncio
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from kamojiros.cli.qa import app
from kamojiros.core import qa_ask

if TYPE_CHECKING:
    from kamojiros.models import QAResult

console = Console()


@app.command("ask")
def ask(query: str = typer.Argument(..., help="検索クエリ")) -> None:
    """QA with tools."""

    async def _run() -> None:
        qa_result: QAResult = await qa_ask(query)
        typer.echo(qa_result.answer_markdown)

    asyncio.run(_run())
