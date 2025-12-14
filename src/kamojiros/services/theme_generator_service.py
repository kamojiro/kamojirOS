"""Theme generator service."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic_ai import Agent

from kamojiros.infrastructure.genai.pydantic_ai_factory import create_pydantic_ai_model
from kamojiros.models import ActivitySource, ThemeSuggestion
from kamojiros.services.search_service import SearchService

if TYPE_CHECKING:
    from kamojiros.config.settings import GeminiSettings, SearxngSettings
    from kamojiros.models import Activity
    from kamojiros.services.rag.activity_retrieve_service import ActivityRetrieveService

__all__ = ("ThemeGeneratorService",)

# 定数
DAYS = 14  # Activity 参照期間
N = 10  # 候補数（デフォルト）


class ThemeSuggestionsResult(BaseModel):
    """Theme suggestions result from LLM."""

    suggestions: list[ThemeSuggestion]


@dataclass
class ThemeGeneratorDependencies:
    """Dependencies for theme generator."""

    activities: list[Activity]


# System prompt for theme generation
THEME_GENERATION_PROMPT = """
あなたはユーザーの活動履歴から調査価値のあるテーマを提案するアシスタントです。

ユーザーの最近の Activity（Misskey の投稿など）を分析して、DeepResearch で調査する価値のあるテーマを提案してください。

# 提案の観点

1. **recent_search**: ユーザーが最近よく調べている内容をさらに深掘りする
2. **next_step**: 現在の興味から「次に調べたくなる」切り口を提案
   - 比較（A vs B）
   - 設計指針・ベストプラクティス
   - 失敗事例・落とし穴
   - ユースケース・実装手順

# 出力形式

- 各テーマは `topic`, `known_info`, `rationale`, `confidence`, `tags` を含む
- `topic`: DeepResearch で調査するトピック（具体的に）
- `known_info`: ユーザーがすでに知っていること（Activity から抽出）
- `rationale`: なぜこのテーマを提案するか（観点を明記）
- `confidence`: 0.0-1.0 の信頼度
- `tags`: 関連タグのリスト

# 注意事項

- 抽象的すぎるテーマは避ける
- ユーザーの興味に沿った具体的なテーマを提案
- 重複を避ける
""".strip()


class ThemeGeneratorService:
    """Theme generator service."""

    def __init__(
        self,
        activity_retrieve_service: ActivityRetrieveService,
        search_service: SearchService,
        agent: Agent[ThemeGeneratorDependencies, ThemeSuggestionsResult],
    ) -> None:
        """Initialize."""
        self._activity_retrieve = activity_retrieve_service
        self._search = search_service
        self._agent = agent

    @classmethod
    def create(
        cls,
        gemini_settings: GeminiSettings,
        searxng_settings: SearxngSettings,
        activity_retrieve_service: ActivityRetrieveService,
    ) -> ThemeGeneratorService:
        """Create theme generator service."""
        search_service = SearchService.create(searxng_settings)

        # Model 作成
        flash_model = create_pydantic_ai_model(gemini_settings, model_name="gemini-2.5-flash")

        # Agent 作成
        agent: Agent[ThemeGeneratorDependencies, ThemeSuggestionsResult] = Agent(
            flash_model,
            deps_type=ThemeGeneratorDependencies,
            output_type=ThemeSuggestionsResult,
            system_prompt=THEME_GENERATION_PROMPT,
        )

        return cls(activity_retrieve_service, search_service, agent)

    async def suggest(self, query: str | None = None, *, num_suggestions: int = N) -> list[ThemeSuggestion]:
        """Suggest themes.

        Args:
            query: クエリ文字列（将来の拡張用、現在は未使用）
            num_suggestions: 生成する候補数

        Returns:
            テーマ提案のリスト

        """
        del query  # 将来の拡張用

        # 直近 DAYS 日間の Activity を取得
        now = datetime.now(UTC)
        start = now - timedelta(days=DAYS)
        activities = await self._activity_retrieve.list_between_activity(
            start=start,
            end=now,
            source=ActivitySource.MISSKEY,
            limit=200,
        )

        if not activities:
            # Activity がない場合は空リストを返す
            return []

        # Dependencies を作成
        deps = ThemeGeneratorDependencies(activities=activities)

        # LLM で提案生成
        user_prompt = f"過去{DAYS}日間のActivityから、{num_suggestions}件程度のテーマを提案してください。"
        result = await self._agent.run(user_prompt, deps=deps)

        return result.output.suggestions

    async def select_best(self, suggestions: list[ThemeSuggestion]) -> ThemeSuggestion:
        """Select the best theme from suggestions.

        Args:
            suggestions: テーマ提案のリスト

        Returns:
            選択されたテーマ

        """
        if not suggestions:
            msg = "No suggestions to select from"
            raise ValueError(msg)

        # 現時点では confidence が最も高いものを選択
        return max(suggestions, key=lambda s: s.confidence)
