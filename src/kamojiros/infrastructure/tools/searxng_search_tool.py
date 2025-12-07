"""SearxNG search tool."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import httpx
from pydantic import TypeAdapter
from pydantic_ai.tools import Tool
from typing_extensions import TypedDict

if TYPE_CHECKING:
    from kamojiros.config.settings import SearxngSettings

__all__ = ("SearxngSearchResult", "searxng_search_tool")


class SearxngSearchResult(TypedDict):
    """A normalized SearxNG search result."""

    title: str
    """The title of the search result."""
    url: str
    """The URL of the search result."""
    content: str
    """A short description / snippet of the result."""
    engine: str | None
    """The SearxNG engine that produced this result (e.g. 'google')."""
    score: float | None
    """Optional relevance score, if provided by SearxNG."""


searxng_search_ta = TypeAdapter(list[SearxngSearchResult])

SearchMode = Literal["web", "dev", "paper"]
TimeRange = Literal["day", "week", "month", "year"]


@dataclass
class SearxngSearchTool:
    """The SearxNG search tool with mode-based engine presets."""

    base_url: str  # e.g. "http://localhost:8080"
    timeout: float = 10.0

    # デフォルト language / safesearch
    default_language: str | None = "ja"
    default_safesearch: int = 1  # 0: none, 1: moderate, 2: strict

    # モードごとの engine プリセット
    web_engines: list[str] | None = None
    dev_engines: list[str] | None = None
    paper_engines: list[str] | None = None

    async def __call__(
        self,
        query: str,
        mode: SearchMode = "web",
        num_results: int = 8,
        time_range: TimeRange | None = None,
    ) -> list[SearxngSearchResult]:
        """Search SearxNG for the given query and return normalized results.

        Args:
            query: 検索クエリ。
            mode: 検索モード ('web' | 'dev' | 'paper')。
            num_results: 返す最大件数。
            time_range: 'day', 'week', 'month', 'year' など期間を絞る場合に指定。

        Returns:
            TypedDict ベースの検索結果リスト。

        """
        # 1. mode から engines を決定
        engines = self._engines_for_mode(mode)

        # 2. クエリパラメータ組み立て
        params: dict[str, Any] = {
            "q": query,
            "format": "json",
        }
        if self.default_language:
            params["language"] = self.default_language

        if engines:
            params["engines"] = ",".join(engines)

        if self.default_safesearch is not None:
            params["safesearch"] = self.default_safesearch

        if time_range:
            params["time_range"] = time_range

        # 3. HTTP 呼び出し
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/search", params=params)
            resp.raise_for_status()
            data = resp.json()

        # 4. 正規化
        raw_results = data.get("results", [])
        normalized: list[SearxngSearchResult] = []

        for item in raw_results[:num_results]:
            url = item.get("url")
            if not url:
                continue

            normalized.append(
                {
                    "title": item.get("title") or url,
                    "url": url,
                    "content": item.get("content") or item.get("snippet") or "",
                    "engine": item.get("engine"),
                    "score": float(item["score"]) if "score" in item else None,
                }
            )

        # TypedDict リストとして validate
        return searxng_search_ta.validate_python(normalized)

    # 内部ヘルパ
    def _engines_for_mode(self, mode: SearchMode) -> list[str] | None:
        """モードごとにエンジンセットを返す."""
        if mode == "web":
            return self.web_engines or [
                "google",
                "duckduckgo",
                "brave",
                "goo",
            ]
        if mode == "dev":
            return self.dev_engines or [
                "github",
                "gitlab",
                "stackoverflow",
                "pypi",
                "npm",
                "mdn",
            ]
        if mode == "paper":
            return self.paper_engines or [
                "arxiv",
                "semantic_scholar",
                "google_scholar",
            ]
        # 型的にはここに来ないはず
        return None


def searxng_search_tool(
    searxng_settings: SearxngSettings,
    *,
    timeout: float = 10.0,
    default_language: str | None = "ja",
    default_safesearch: int = 1,
    web_engines: list[str] | None = None,
    dev_engines: list[str] | None = None,
    paper_engines: list[str] | None = None,
) -> Tool[Any]:
    """Create a SearxNG search tool with mode-based presets.

    Args:
        searxng_settings: SearxNG の設定。
        timeout: HTTP タイムアウト秒数。
        default_language: language パラメータのデフォルト。
        default_safesearch: safesearch のデフォルト (0,1,2)。
        web_engines: 'web' モード用のエンジンセット (未指定ならデフォルトを使用)。
        dev_engines: 'dev' モード用のエンジンセット。
        paper_engines: 'paper' モード用のエンジンセット。

    Returns:
        PydanticAI 用の Tool[Any]。

    """
    tool_impl = SearxngSearchTool(
        base_url=str(searxng_settings.base_url),
        timeout=timeout,
        default_language=default_language,
        default_safesearch=default_safesearch,
        web_engines=web_engines,
        dev_engines=dev_engines,
        paper_engines=paper_engines,
    )

    return Tool[Any](
        tool_impl.__call__,
        name="searxng_search",
        description=(
            "Searches SearxNG for the given query. Use `mode` to choose between 'web', 'dev', or 'paper' presets."
        ),
    )
