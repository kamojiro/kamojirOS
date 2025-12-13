"""Tests for activity bootstrap module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kamojiros.activity_bootstrap import ActivityStack, build_activity_stack
from kamojiros.config.settings import Settings


@pytest.mark.asyncio
async def test_build_activity_stack() -> None:
    """Test that ActivityStack is built correctly."""
    # Mocking dependencies to avoid real I/O and external calls
    with (
        patch("kamojiros.activity_bootstrap.GeminiEmbeddings.create", return_value=MagicMock()) as mock_embeddings,
        patch("kamojiros.activity_bootstrap.ainit_activity_index_table", new_callable=AsyncMock) as mock_init_table,
        patch("kamojiros.activity_bootstrap.create_activity_vector_store", new_callable=AsyncMock) as mock_create_store,
        patch("kamojiros.activity_bootstrap.ActivityIngestService") as mock_ingest,
        patch("kamojiros.activity_bootstrap.FileKeyValueStore"),
        patch("kamojiros.activity_bootstrap.MisskeyClient.create"),
        patch("kamojiros.activity_bootstrap.MisskeyActivitySyncService") as mock_sync,
        patch("kamojiros.activity_bootstrap.ActivityRetrieveService"),
        patch("kamojiros.activity_bootstrap.QAService.create") as mock_qa,
        patch("kamojiros.activity_bootstrap.DeepResearchService.create") as mock_deep_research,
    ):
        mock_store_instance = AsyncMock()
        mock_create_store.return_value = mock_store_instance

        settings = Settings()

        stack = await build_activity_stack(settings)

        assert isinstance(stack, ActivityStack)
        assert stack.settings == settings
        mock_embeddings.assert_called_once()
        mock_init_table.assert_awaited_once()
        mock_create_store.assert_awaited_once()
        mock_ingest.assert_called_once()
        mock_sync.assert_called_once()
        mock_qa.assert_called_once()
        mock_deep_research.assert_called_once()
