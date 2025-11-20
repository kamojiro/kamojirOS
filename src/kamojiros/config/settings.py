"""Kamojiros 固有の設定."""

from pathlib import Path  # noqa: TC003
from typing import Any

from pydantic import BaseModel

from kamojiros.config.base_settings import BaseSettings


class NotesSettings(BaseModel):
    """Kamomo Notes (Git repo) 関連の設定."""

    repo_root: Path
    default_branch: str = "main"


class SelfObserverSettings(BaseModel):
    """self_observer エージェント固有の設定."""

    enabled: bool = True
    schedule_cron: str = "0 * * * *"  # 例: 毎時


class TrackerSettings(BaseModel):
    """tracker_api 関連の設定."""

    db_url: str = "sqlite:///kamojiros.db"
    base_url: str = "https://example.com"


class Settings(BaseSettings):
    """アプリ全体の設定（エントリポイント用）."""

    notes: NotesSettings
    self_observer: SelfObserverSettings = SelfObserverSettings()
    tracker: TrackerSettings = TrackerSettings()

    def __init__(self, **values: Any) -> None:
        """環境変数 or 引数から設定を構築する.

        実体は BaseSettings.__init__ に任せる。
        """
        super().__init__(**values)
