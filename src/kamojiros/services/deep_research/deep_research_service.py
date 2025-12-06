"""Deep research report service."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from kamojiros.infrastructure.genai.pydantic_ai_factory import create_pydantic_ai_model
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from kamojiros.models import Activity, QAResult, ReportType

if TYPE_CHECKING:
    from kamojiros.config.settings import GeminiSettings
    from kamojiros.infrastructure.misskey.client import MisskeyClient
    from kamojiros.services.rag.activity_retrieve_service import ActivityRetrieveService


@dataclass
class DeepResearchDependencies:
    """DeepResearch Agent が使う依存オブジェクト."""

    activity_retriever: ActivityRetrieveService

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DeepResearchResult(BaseModel):
    """レポート."""

    title: str = Field(..., description="レポートのタイトル")
    type: ReportType = Field(..., description="レポートの種類")
    tags: list[str] = Field(..., description="レポートのタグ")


def register_deep_research_tools(agent: Agent[DeepResearchDependencies, BaseModel]) -> None:
    """Deep research で利用するツールの登録."""

    @agent.tool
    async def search_activities(
        ctx: RunContext[DeepResearchDependencies],
        query: str,
        days: int | None = 30,
        top_k: int | None = 10,
    ) -> list[Activity]:
        """ユーザーのメモをベクトル検索して返すツール.

        - ユーザーのメモはユーザーから与えられた URL やキーワードをもとに、検索を使って LLM によって生成されている
        - ユーザーの「最近の投稿」「最近考えていること」「これまでに学んだことがあること」「これまでに興味を持ったもの」などに答えるときに使う
        - query にはユーザーの質問内容、またはその要約を入れる
        - days が None のときは全期間から検索する
        - top_k は多くの情報やより多くの情報が必要な場合に大きくする
        """# noqa: E501
        return await ctx.deps.activity_retriever.search_recent_misskey_activity(
            query=query,
            days=days,
            top_k=top_k,
        )


class DeepResearchService:
    """Deep research service."""

    def __init__(self, agent: Agent, activity_retrieve_service: ActivityRetrieveService) -> None:
        """Initialize."""
        self._agent = agent
        self._activity_retrieve_service = activity_retrieve_service

    @classmethod
    def create(
        cls, gemini_settings: GeminiSettings, activity_retrieve_service: ActivityRetrieveService, client: MisskeyClient
    ) -> Self:
        """Create rag answer."""
        model = create_pydantic_ai_model(gemini_settings, "gemini-2.5-pro")
        agent = Agent(
            model,
            deps_type=DeepResearchDependencies,
            output_type=QAResult,
            system_prompt=(
                "あなたは kamojiros の QA エージェントです。"
                "ユーザの質問に対して、与えられた Activity の内容を優先的に使って日本語で回答してください。"
                "答えは Markdown で返してください。"
            ),
        )

        return cls(agent, activity_retrieve_service, client)
