"""LangChain Embeddings implementation using google.genai.Client for Gemini Embeddings."""

from typing import TYPE_CHECKING, Self

from google.genai.types import EmbedContentConfig, EmbedContentResponse
from langchain_core.embeddings import Embeddings

from kamojiros.infrastructure.genai.client_factory import create_genai_client

if TYPE_CHECKING:
    from collections.abc import Sequence

    from google import genai

    from kamojiros.config.settings import GeminiSettings


class GeminiEmbeddings(Embeddings):
    """google.genai.Client を使う LangChain Embeddings 実装."""

    def __init__(
        self,
        client: genai.Client,
        *,
        model: str = "gemini-embedding-001",
        document_task_type: str = "RETRIEVAL_DOCUMENT",
        query_task_type: str = "RETRIEVAL_QUERY",
        output_dimensionality: int | None = None,
    ) -> None:
        """Initialize GeminiEmbeddings."""
        self._client = client
        self._async_client = client.aio
        self._model = model
        self._doc_task_type = document_task_type
        self._query_task_type = query_task_type
        self._output_dimensionality = output_dimensionality

    @classmethod
    def create(cls, gemini_settings: GeminiSettings) -> Self:
        """GeminiSettings から GeminiEmbeddings インスタンスを作る."""
        client = create_genai_client(
            project_id=gemini_settings.project_id,
            api_key=None,  # TODO(kamojiro): Pass api_key from settings if needed
        )
        return cls(client=client)

    # ---------- 内部ヘルパー ----------

    def _build_config(self, task_type: str) -> EmbedContentConfig:
        kwargs: dict = {"task_type": task_type}
        if self._output_dimensionality is not None:
            kwargs["output_dimensionality"] = self._output_dimensionality
        return EmbedContentConfig(**kwargs)

    def _to_embedding_vectors(self, embedding_response: EmbedContentResponse) -> list[list[float]]:
        """Convert EmbedContentResponse to a list of embedding vectors."""
        if not embedding_response.embeddings:
            return []
        return [embedding.values for embedding in embedding_response.embeddings if embedding.values is not None]

    def _embed_sync(
        self,
        texts: Sequence[str],
        *,
        task_type: str,
    ) -> list[list[float]]:
        """同期版 embed 実装."""
        if not texts:
            return []

        # genai.Client.models.embed_content は str / list[str] 両方受けるが、
        # 明示的に list[str] を渡したほうが扱いやすい
        embedding_response = self._client.models.embed_content(
            model=self._model,
            contents=list(texts),
            config=self._build_config(task_type),
        )
        return self._to_embedding_vectors(embedding_response)

    async def _embed_async(
        self,
        texts: Sequence[str],
        *,
        task_type: str,
    ) -> list[list[float]]:
        """非同期版 embed 実装 (client.aio を利用)."""
        if not texts:
            return []

        embedding_response = await self._async_client.models.embed_content(
            model=self._model,
            contents=list(texts),
            config=self._build_config(task_type),
        )
        return self._to_embedding_vectors(embedding_response)

    # ---------- LangChain Embeddings インターフェース (sync) ----------

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """コーパス/ドキュメント用 (RETRIEVAL_DOCUMENT)."""
        return self._embed_sync(texts, task_type=self._doc_task_type)

    def embed_query(self, text: str) -> list[float]:
        """クエリ用 (RETRIEVAL_QUERY)."""
        vectors = self._embed_sync([text], task_type=self._query_task_type)
        return vectors[0]

    # ---------- LangChain Embeddings インターフェース (async) ----------

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """コーパス/ドキュメント用 (RETRIEVAL_DOCUMENT)."""
        return await self._embed_async(texts, task_type=self._doc_task_type)

    async def aembed_query(self, text: str) -> list[float]:
        """クエリ用 (RETRIEVAL_QUERY)."""
        vectors = await self._embed_async([text], task_type=self._query_task_type)
        return vectors[0]
