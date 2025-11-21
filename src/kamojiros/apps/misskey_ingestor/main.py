"""Misskey Ingestor Application."""

from pathlib import Path

from rich.console import Console

from kamojiros.config.settings import Settings
from kamojiros.infrastructure.misskey.client import MisskeyClient

console = Console()


def run() -> None:
    """Misskey Ingestor execution."""
    settings = Settings()
    if not settings.misskey or not settings.misskey.url:
        console.print("[red]Misskey URL is not configured.[/red]")
        return

    client = MisskeyClient(url=settings.misskey.url, token=settings.misskey.token)

    # データ保存先
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    output_file = data_dir / "activities.jsonl"

    console.print(f"Fetching notes from {settings.misskey.url}...")
    try:
        activities = client.fetch_notes(limit=20)
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]Error fetching notes: {e}[/red]")
        return

    console.print(f"Fetched {len(activities)} notes.")

    # 追記モードで保存
    with output_file.open("a", encoding="utf-8") as f:
        for activity in activities:
            # モデルをJSON文字列に変換して書き込み
            f.write(activity.model_dump_json() + "\n")

    console.print(f"[green]Saved to {output_file}[/green]")


if __name__ == "__main__":
    run()
