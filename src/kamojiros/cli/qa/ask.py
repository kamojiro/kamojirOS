"""QA ask CLI."""

import asyncio

from kamojiros.models import QAResult
from pydantic_ai import AgentRunResult
import typer
from rich.console import Console

from kamojiros.cli.qa import app
from kamojiros.core import qa_ask

console = Console()


@app.command("ask")
def ask(
    query: str = typer.Argument(..., help="検索クエリ")
) -> None:
    """QA with tools."""

    async def _run() -> None:
        qa_result: QAResult = await qa_ask(query)
        typer.echo(qa_result.output.answer_markdown)
    asyncio.run(_run())
