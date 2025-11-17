"""Kamomo 共通の Settings 基底クラス."""

from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict


class BaseSettings(PydanticBaseSettings):
    """Kamomo 共通の Settings 基底クラス.

    - 環境変数プレフィックス: KAMOJIROS_
    - ネスト区切り: "__"
    - .env を自動で読む
    """

    model_config = SettingsConfigDict(
        env_prefix="KAMOJIROS_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
