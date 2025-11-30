"""Tests for GeminiEmbeddings."""

from typing import TYPE_CHECKING

import pytest

from kamojiros.config.settings import Settings
from kamojiros.infrastructure.rag.activity_schema import GEMINI_EMBEDDING_DIMENSION
from kamojiros.infrastructure.rag.gemini_embeddings import GeminiEmbeddings

if TYPE_CHECKING:
    from google.genai import Client  # noqa: F401


class TestGeminiEmbeddings:
    """Tests for GeminiEmbeddings."""

    def create_embeddings(self) -> GeminiEmbeddings:
        """Create a GeminiEmbeddings instance for testing."""
        settings = Settings()
        return GeminiEmbeddings.create(settings.gemini)

    # ---- sync tests ----

    @pytest.mark.gemini_required
    def test_embed_documents(self) -> None:
        """embed_documents() returns vectors with expected dimension."""
        # arrange
        texts = ["Hello, world!", "Testing embeddings."]
        sut = self.create_embeddings()

        # act
        embeddings = sut.embed_documents(texts)

        # assert
        assert len(embeddings) == len(texts)
        assert all(len(vec) == GEMINI_EMBEDDING_DIMENSION for vec in embeddings)

    @pytest.mark.gemini_required
    def test_embed_query(self) -> None:
        """embed_query() returns a single vector with expected dimension."""
        # arrange
        query = "Find recent posts about Python."
        sut = self.create_embeddings()

        # act
        embedding = sut.embed_query(query)

        # assert
        assert len(embedding) == GEMINI_EMBEDDING_DIMENSION

    # ---- async tests ----

    @pytest.mark.gemini_required
    @pytest.mark.asyncio
    async def test_aembed_documents(self) -> None:
        """aembed_documents() returns vectors with expected dimension."""
        # arrange
        texts = ["Hello, async world!", "Async embeddings test."]
        sut = self.create_embeddings()

        # act
        embeddings = await sut.aembed_documents(texts)

        # assert
        assert len(embeddings) == len(texts)
        assert all(len(vec) == GEMINI_EMBEDDING_DIMENSION for vec in embeddings)

    @pytest.mark.gemini_required
    @pytest.mark.asyncio
    async def test_aembed_query(self) -> None:
        """aembed_query() returns a single vector with expected dimension."""
        # arrange
        query = "Async query about LangChain."
        sut = self.create_embeddings()

        # act
        embedding = await sut.aembed_query(query)

        # assert
        assert len(embedding) == GEMINI_EMBEDDING_DIMENSION
