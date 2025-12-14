"""Theme CLI commands."""

import typer

app = typer.Typer(name="theme", help="Theme suggestion commands")

# Import to register commands
from kamojiros.cli.theme import suggest  # noqa: E402

del suggest  # Import for side effects only
