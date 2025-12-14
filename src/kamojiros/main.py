"""Kamojiros CLI メインエントリーポイント."""

import logging

import typer

from kamojiros.cli.activity import app as activity_app
from kamojiros.cli.qa import app as qa_app
from kamojiros.cli.report import app as report_app
from kamojiros.cli.theme import app as theme_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


app = typer.Typer(
    name="kamojiros",
    help="Kamojiros - Personal Research Agent",
    no_args_is_help=True,
)

# コマンド登録
app.add_typer(report_app, name="report")
app.add_typer(activity_app, name="activity")
app.add_typer(qa_app, name="qa")
app.add_typer(theme_app, name="theme")


def main() -> None:
    """CLI エントリーポイント."""
    app()


if __name__ == "__main__":
    main()
