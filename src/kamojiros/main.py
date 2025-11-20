"""Kamojiros CLI メインエントリーポイント."""

from __future__ import annotations

import typer

from kamojiros.cli.create import create
from kamojiros.cli.list import list_reports
from kamojiros.cli.search import search
from kamojiros.cli.stats import stats

app = typer.Typer(
    name="kamojiros",
    help="Kamojiros - Personal Research Agent",
    no_args_is_help=True,
)

# コマンド登録
app.command(name="create", help="Create a new report")(create)
app.command(name="list", help="List reports")(list_reports)
app.command(name="search", help="Search reports by keyword")(search)
app.command(name="stats", help="Show statistics")(stats)


def main() -> None:
    """CLI エントリーポイント."""
    app()


if __name__ == "__main__":
    main()
