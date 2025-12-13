"""Embedding service using Google Gemini API."""

import logging
from typing import TYPE_CHECKING, Self

from google.genai.types import EmbedContentConfig, EmbedContentResponse

from kamojiros.infrastructure.genai.client_factory import create_genai_client

if TYPE_CHECKING:
    from collections.abc import Sequence

    from google import genai

    from kamojiros.config.settings import GeminiSettings

EMBEDDING_DIMENSION = 3072


class EmbeddingService:
    """Embedding service using Google Gemini API.

    Note:
        This class is currently unused and experimental.
        The active implementation uses `GeminiEmbeddings` in `kamojiros.infrastructure.rag.gemini_embeddings`.

    """

    embedding_document_config = EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    embedding_query_config = EmbedContentConfig(task_type="RETRIEVAL_QUERY")

    def __init__(self, client: genai.Client) -> None:
        """Initialize EmbeddingService."""
        self.client = client
        self.embedding_model = "gemini-embedding-001"
        self.logger = logging.getLogger(__name__)

    @classmethod
    def create(cls, gemini_settings: GeminiSettings) -> Self:
        """Create an instance of EmbeddingService from GeminiSettings."""
        client = create_genai_client(
            project_id=gemini_settings.project_id,
            api_key=None,  # TODO(kamojiro): Pass api_key from settings if needed
        )
        return cls(
            client=client,
        )

    def _to_embedding_vectors(self, embedding_response: EmbedContentResponse) -> list[list[float]]:
        """Convert EmbedContentResponse to a list of embedding vectors."""
        if not embedding_response.embeddings:
            return []
        return [embedding.values for embedding in embedding_response.embeddings if embedding.values]

    def _embed_vertexai(self, texts: list[str], embedding_config: EmbedContentConfig) -> list[list[float]]:
        """Generate embeddings using the Vertex AI client."""
        embedding_response = self.client.models.embed_content(
            model=self.embedding_model,
            contents=texts,
            config=embedding_config,
        )
        return self._to_embedding_vectors(embedding_response)

    def _embed(self, texts: Sequence[str], embedding_config: EmbedContentConfig) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        return self._embed_vertexai(list(texts), embedding_config)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate document embeddings for a list of texts."""
        return self._embed(texts, self.embedding_document_config)

    def embed_queries(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate query embeddings for a list of texts."""
        return self._embed(texts, self.embedding_query_config)
