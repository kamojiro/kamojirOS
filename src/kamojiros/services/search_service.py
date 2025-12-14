"""Search service wrapper for SearxNG."""

from typing import TYPE_CHECKING

import httpx
from pydantic import BaseModel, HttpUrl

from kamojiros.infrastructure.tools.searxng_search_tool import (
    SearchMode,
    SearxngSearchTool,
    TimeRange,
)

if TYPE_CHECKING:
    from kamojiros.config.settings import SearxngSettings

__all__ = ("SearchResult", "SearchService")


class SearchResult(BaseModel):
    """Search result."""

    title: str
    url: HttpUrl
    snippet: str


class SearchService:
    """Search service (SearxNG wrapper)."""

    def __init__(self, tool: SearxngSearchTool) -> None:
        """Initialize."""
        self._tool = tool

    @classmethod
    def create(cls, searxng_settings: SearxngSettings) -> SearchService:
        """Create search service."""
        tool = SearxngSearchTool(
            base_url=str(searxng_settings.base_url),
            timeout=10.0,
            default_language="ja",
            default_safesearch=1,
        )
        return cls(tool)

    async def search(
        self,
        query: str,
        *,
        mode: SearchMode = "web",
        num_results: int = 10,
        time_range: TimeRange | None = None,
    ) -> list[SearchResult]:
        """Search SearxNG.

        Args:
            query: 検索クエリ
            mode: 検索モード ('web' | 'dev' | 'paper')
            num_results: 返す最大件数
            time_range: 期間指定 ('day' | 'week' | 'month' | 'year')

        Returns:
            検索結果のリスト

        """
        try:
            raw_results = await self._tool(
                query=query,
                mode=mode,
                num_results=num_results,
                time_range=time_range,
            )

            return [
                SearchResult(
                    title=r["title"],
                    url=HttpUrl(r["url"]),  # type: ignore[arg-type]
                    snippet=r["content"],
                )
                for r in raw_results
            ]
        except (httpx.HTTPError, ValueError) as e:
            # SearxNG 失敗時は空リストを返す
            del e
            return []
