"""Self Observer Application."""

import traceback

from rich.console import Console

from kamojiros.apps.misskey_ingestor.main import run as run_ingestor
from kamojiros.config.settings import Settings
from kamojiros.infrastructure.files.activity_repository import ActivityRepository
from kamojiros.infrastructure.git.markdown_report_writer import MarkdownReportRepository
from kamojiros.services.report_service import ReportService
from kamojiros.services.self_observer_service import SelfObserverService

console = Console()


def run() -> None:
    """Run Self Observer."""
    settings = Settings()

    # 1. Ingest activities (Optional: can be separate cron)
    # For now, we run it here to ensure we have latest data
    console.print("Running Misskey Ingestor...")
    run_ingestor()

    # 2. Initialize services
    # Note: We need to handle the case where notes settings might be missing,
    # but for this app it's required.
    if not settings.notes:
        console.print("[red]Notes settings are not configured.[/red]")
        return

    report_writer = MarkdownReportRepository(settings.notes.repo_root)
    report_service = ReportService(report_writer)
    activity_repo = ActivityRepository()

    service = SelfObserverService(report_service, activity_repo)

    # 3. Observe
    console.print("Observing...")
    try:
        report = service.observe()
        console.print(f"[green]Report created: {report.meta.title}[/green]")
        console.print(f"Saved to: {report.meta.note_id}")
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]Error during observation: {e}[/red]")
        traceback.print_exc()


if __name__ == "__main__":
    run()
