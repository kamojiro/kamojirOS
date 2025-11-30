"""Activity search CLI."""

import asyncio

import typer
from rich.console import Console

from kamojiros.cli.activity import app
from kamojiros.core import search_misskey_activity

console = Console()


@app.command("search")
def search(
    query: str = typer.Argument(..., help="検索クエリ"),
    days: int | None = typer.Option(None, "--days", "-d"),
    top_k: int = typer.Option(10, "--top-k", "-k"),
) -> None:
    """Misskey Activity をベクトル検索する."""

    async def _run() -> None:
        docs = await search_misskey_activity(
            query,
            days=days or 7,
            top_k=top_k if top_k > 0 else 10,
        )
        for doc in docs:
            typer.echo(doc.content[:40])

    asyncio.run(_run())
