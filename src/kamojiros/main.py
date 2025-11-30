"""Kamojiros CLI メインエントリーポイント."""

from __future__ import annotations

import typer

from kamojiros.cli.activity import app as activity_app
from kamojiros.cli.report import app as report_app

app = typer.Typer(
    name="kamojiros",
    help="Kamojiros - Personal Research Agent",
    no_args_is_help=True,
)

# コマンド登録
app.add_typer(report_app, name="report")
app.add_typer(activity_app, name="activity")


def main() -> None:
    """CLI エントリーポイント."""
    app()


if __name__ == "__main__":
    main()
