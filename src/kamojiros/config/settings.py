"""Kamojiros 固有の設定."""

from pathlib import Path  # noqa: TC003
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict

from kamojiros.config.base_settings import BaseSettings


class NotesSettings(BaseModel):
    """Notesリポジトリの設定."""

    repo_root: Path


class SelfObserverSettings(BaseModel):
    """Self Observerの設定."""

    timezone: str = "Asia/Tokyo"


class TrackerSettings(BaseModel):
    """Trackerの設定."""

    base_url: str = "https://example.com"


class MisskeySettings(PydanticBaseSettings):
    """Misskey設定."""

    url: str | None = None
    token: str | None = None

    model_config = SettingsConfigDict(env_prefix="MISSKEY_")


class Settings(BaseSettings):
    """全体設定."""

    notes: NotesSettings | None = None
    self_observer: SelfObserverSettings | None = None
    tracker: TrackerSettings | None = None
    misskey: MisskeySettings = Field(default_factory=MisskeySettings)

    model_config = SettingsConfigDict(env_nested_delimiter="__")

    @field_validator("notes")
    @classmethod
    def _ensure_notes(cls, v: NotesSettings | None) -> NotesSettings:
        if v is None:
            msg = "KAMOJIROS_NOTES__REPO_ROOT is required"
            raise ValueError(msg)
        return v

    def __init__(self, **values: Any) -> None:
        """環境変数 or 引数から設定を構築する.

        実体は BaseSettings.__init__ に任せる。
        """
        super().__init__(**values)
