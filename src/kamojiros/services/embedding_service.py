"""Embedding service using Google Gemini API."""


import logging
from typing import TYPE_CHECKING, Self

from google import genai
from google.api_core.exceptions import ResourceExhausted
from google.genai.types import EmbedContentConfig, EmbedContentResponse, HttpOptions

if TYPE_CHECKING:
    from collections.abc import Sequence

    from kamojiros.config.settings import GeminiSettings

EMBEDDING_DIMENSION = 3072


class EmbeddingService:
    """Embedding service using Google Gemini API."""

    embedding_document_config = EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    embedding_query_config = EmbedContentConfig(task_type="RETRIEVAL_QUERY")

    def __init__(self, gemini_api_key: str, project_id: str) -> None:
        """Initialize EmbeddingService."""
        self.dev_client: genai.Client = genai.Client(vertexai=False, api_key=gemini_api_key)
        self.vertexai_client = genai.Client(
            vertexai=True,
            project=project_id,
            location="us-central1",
            http_options=HttpOptions(api_version="v1"),
        )
        self.embedding_model = "gemini-embedding-001"
        self.logger = logging.getLogger(__name__)

    @classmethod
    def create(cls, gemini_settings: GeminiSettings) -> Self:
        """Create an instance of EmbeddingService from GeminiSettings."""
        return cls(
            gemini_api_key=gemini_settings.api_key,
            project_id=gemini_settings.project_id,
        )

    def _to_embedding_vectors(self, embedding_response: EmbedContentResponse) -> list[list[float]]:
        """Convert EmbedContentResponse to a list of embedding vectors."""
        if not embedding_response.embeddings:
            return []
        return [embedding.values for embedding in embedding_response.embeddings if embedding.values]

    def _embed_dev(self, texts: list[str], embedding_config: EmbedContentConfig) -> list[list[float]]:
        """Generate embeddings using the dev client."""
        embedding_response = self.dev_client.models.embed_content(
            model=self.embedding_model,
            contents=texts,
            config=embedding_config,
        )
        return self._to_embedding_vectors(embedding_response)

    def _embed_vertexai(self, texts: list[str], embedding_config: EmbedContentConfig) -> list[list[float]]:
        """Generate embeddings using the Vertex AI client."""
        embedding_response = self.vertexai_client.models.embed_content(
            model=self.embedding_model,
            contents=texts,
            config=embedding_config,
        )
        return self._to_embedding_vectors(embedding_response)

    def _embed(self, texts: Sequence[str], embedding_config: EmbedContentConfig) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        return self._embed_vertexai(list(texts), embedding_config)
        # MEMO(kamojiro): genai はうまく動作しなかった
        try:
            return self._embed_dev(list(texts), embedding_config)
        except ResourceExhausted as e:
            self.logger.warning("Dev embedding service quota exhausted, switching to Vertex AI: %s", e)
            return self._embed_vertexai(list(texts), embedding_config)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate document embeddings for a list of texts."""
        return self._embed(texts, self.embedding_document_config)

    def embed_queries(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate query embeddings for a list of texts."""
        return self._embed(texts, self.embedding_query_config)
