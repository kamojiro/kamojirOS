"""Simple file-based key-value store with namespaces."""

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kamojiros.config.settings import StateStoreSettings

if TYPE_CHECKING:
    from pathlib import Path

NAMESPACE = Literal["misskey_sync"]
FILE_STORE_KV_STORE_NAME = "file_kv_store"


class FileKeyValueStore:
    """名前空間付きの key-value をファイルで保存するだけのストア."""

    def __init__(self, settings: StateStoreSettings) -> None:
        """Initialize FileKeyValueStore with the given root directory."""
        self._file_kv_path = settings.base_dir / FILE_STORE_KV_STORE_NAME

    def _path(self, namespace: NAMESPACE, key: str) -> Path:
        """Get the file path for the given namespace and key.

        例: <root>/misskey_sync/<user_id>.txt
        """
        return self._file_kv_path / namespace / f"{key}.txt"

    def load(self, namespace: NAMESPACE, key: str) -> str | None:
        """Load the value for the given namespace and key."""
        path = self._path(namespace, key)
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8").strip()
        return text or None

    def save(self, namespace: NAMESPACE, key: str, value: str) -> None:
        """Save the value for the given namespace and key."""
        path = self._path(namespace, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
