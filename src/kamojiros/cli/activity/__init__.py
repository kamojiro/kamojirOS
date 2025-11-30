"""Activity CLI."""

import typer

app = typer.Typer(help="Activity related commands.", no_args_is_help=True)

from kamojiros.cli.activity import search, sync  # noqa: E402, F401
