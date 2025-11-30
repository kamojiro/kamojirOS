"""Tests for EmbeddingService."""

from typing import TYPE_CHECKING

import pytest
from google.genai.types import EmbedContentConfig

from kamojiros.config.settings import Settings
from kamojiros.services.embedding_service import EMBEDDING_DIMENSION, EmbeddingService

if TYPE_CHECKING:
    from google.genai.types import EmbedContentConfig


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    def create_embedding_service(self) -> EmbeddingService:
        """Create an instance of EmbeddingService for testing."""
        settings = Settings()
        return EmbeddingService.create(settings.gemini)

    @pytest.mark.skip(reason="gemini-embedding-001 model is not available via API key.")
    @pytest.mark.parametrize(
        "embedding_config",
        [
            EmbeddingService.embedding_document_config,
            EmbeddingService.embedding_query_config,
        ],
    )
    @pytest.mark.gemini_required
    def test_dev_client_embedding(self, embedding_config: EmbedContentConfig) -> None:
        """Test embedding using the dev client."""
        # arrange
        texts = ["Hello, world!", "Testing embeddings."]
        sut = self.create_embedding_service()
        # act
        embeddings = sut._embed_dev(texts, embedding_config)
        # assert
        assert len(embeddings) == len(texts)
        assert all(len(embedding_vector) == EMBEDDING_DIMENSION for embedding_vector in embeddings)

    @pytest.mark.parametrize(
        "embedding_config",
        [
            EmbeddingService.embedding_document_config,
            EmbeddingService.embedding_query_config,
        ],
    )
    @pytest.mark.gemini_required
    @pytest.mark.skip(reason="Requires real credentials")
    def test_vertexai_client_embedding(self, embedding_config: EmbedContentConfig) -> None:
        """Test embedding using the dev client."""
        # arrange
        texts = ["Hello, world!", "Testing embeddings."]
        sut = self.create_embedding_service()
        # act
        embeddings = sut._embed_vertexai(texts, embedding_config)
        # assert
        assert len(embeddings) == len(texts)
        assert all(len(embedding_vector) == EMBEDDING_DIMENSION for embedding_vector in embeddings)
