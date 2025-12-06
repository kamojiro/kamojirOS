"""QA CLI."""

import typer

app = typer.Typer(help="Question&Answer related commands.", no_args_is_help=True)

from kamojiros.cli.qa import ask  # noqa: E402, F401
