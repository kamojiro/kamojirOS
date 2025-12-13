"""Kamojiros 固有の設定."""

from pathlib import Path
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, Field

from kamojiros.config.base_settings import BaseSettings


class MisskeySettings(BaseModel):
    """Misskey の設定."""

    host: str
    access_token: str
    kamojiroid_id: str


class NotesSettings(BaseModel):
    """Notesリポジトリの設定."""

    repo_root: Path


class GeminiSettings(BaseModel):
    """Google Gemini APIの設定."""

    project_id: str
    api_key: str | None = None


class PostgreSQLSettings(BaseModel):
    """PostgreSQLの設定."""

    host: str = "localhost"
    port: int = 5432
    database: str = "kamojiros"
    user: str
    password: str
    activity_index_name: str | None = None


class StateStoreSettings(BaseModel):
    """State Storeの設定."""

    base_dir: Path = Field(default=Path("./.kamojiros"))


class SelfObserverSettings(BaseModel):
    """自己観察エージェントの設定."""

    timezone: str = "Asia/Tokyo"


class SearxngSettings(BaseModel):
    """Searxng の設定."""

    base_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8080")


class Settings(BaseSettings):
    """全体設定."""

    misskey: MisskeySettings
    notes: NotesSettings
    gemini: GeminiSettings
    postgres: PostgreSQLSettings
    state_store: StateStoreSettings = Field(default_factory=StateStoreSettings)
    self_observer: SelfObserverSettings = Field(default_factory=SelfObserverSettings)
    searxng: SearxngSettings = Field(default_factory=SearxngSettings)

    def __init__(self, **values: Any) -> None:
        """環境変数 or 引数から設定を構築する.

        実体は BaseSettings.__init__ に任せる。
        """
        super().__init__(**values)
