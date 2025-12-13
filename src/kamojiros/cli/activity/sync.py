"""Activity search CLI."""

import asyncio

import typer
from rich.console import Console

from kamojiros.activity_bootstrap import sync_misskey_activity
from kamojiros.cli.activity import app

console = Console()


@app.command("sync")
def sync(
    user_id: str | None = typer.Option(
        None,
        "--user-id",
        "-u",
        help="同期する Misskey ユーザ ID（省略時は settings.misskey.kamojiroid_id）",
    ),
) -> None:
    """Misskey のノートを activity ベクトルストアに同期する."""

    async def _run() -> None:
        console.print("[bold]Syncing Misskey activities...[/bold]")
        await sync_misskey_activity(
            user_id=user_id,
        )
        console.print("[green]Done.[/green]")

    asyncio.run(_run())
