"""self_observer アプリケーションのエントリーポイントモジュール."""

import typer

from kamojiros.config.settings import Settings
from kamojiros.infrastructure.git.markdown_report_writer import MarkdownReportWriter
from kamojiros.services.self_observer_service import SelfObserverService


def run() -> None:
    """self_observer アプリケーションのエントリーポイント."""
    settings = Settings()

    repo = MarkdownReportWriter(notes_repo_root=settings.notes.repo_root)
    service = SelfObserverService(report_repo=repo)

    report = service.create_test_report()
    typer.echo(f"wrote: {report.meta.note_id}")


if __name__ == "__main__":
    run()
