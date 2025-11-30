"""Report CLI."""

import typer

app = typer.Typer(help="Report related commands.", no_args_is_help=True)

from kamojiros.cli.report import create, list_report, search, stats  # noqa: E402, F401
