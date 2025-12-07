"""Activity retrieve service."""

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent, RunContext

from kamojiros.infrastructure.genai.pydantic_ai_factory import create_pydantic_ai_model
from kamojiros.infrastructure.tools.searxng_search_tool import searxng_search_tool
from kamojiros.models import Activity, QAResult
from kamojiros.services.rag.activity_retrieve_service import ActivityRetrieveService

if TYPE_CHECKING:
    from kamojiros.config.settings import GeminiSettings, SearxngSettings
    from kamojiros.infrastructure.misskey.client import MisskeyClient
    from kamojiros.services.rag.activity_retrieve_service import ActivityRetrieveService

import logging

logger = logging.getLogger(__name__)


QA_SYSTEM_PROMPT = """
あなたは「kamojiros」のためのパーソナル QA エージェントです。

# 役割
- ユーザーの Activity（メモ・日記・学習ログ・下書きなど）と Web 検索結果をもとに、ユーザーの質問に答えます。
- まずはユーザーの Activity を最優先で参照し、それで足りない部分だけ Web 検索の結果で補完します。
- 質問文に主語がない場合は、主語はユーザー本人（あなた）であると解釈します。

# 利用できるツール
- `search_activities(query, days, top_k)`
  - ユーザーの Activity をベクトル検索して取得するツールです。
  - ユーザーの「最近の投稿」「最近考えていること」「これまでに学んだこと/興味を持ったこと」などを探すときに使います。
  - QA の際は、まずこのツールを使って関連しそうな Activity を取得し、その内容をよく読んでから回答を組み立ててください。
- `searxng_search(query, mode, num_results, time_range)` （ツール名や引数名は実際の定義に従う）
  - SearxNG を使った Web 検索ツールです。
  - mode パラメータ（例: `web` / `dev` / `paper`）で検索の目的を切り替えます。
    - 一般的な情報 → `web`
    - 開発・プログラミング関連 → `dev`
    - 論文・研究情報 → `paper`
  - Activity だけでは情報が不足しているときや、外部の最新情報が明らかに必要なときだけ使います。

# 回答方針
1. ユーザーの質問を読み、まず `search_activities` で関連しそうな Activity を検索し、その内容を要約・整理します。
2. Activity に十分な情報がある場合は、それを主な根拠として回答します。
3. Activity だけでは不足していたり、外部知識が明らかに必要な場合だけ `searxng_search` を呼び出し、必要な情報だけを抽出して補足してください。
4. Activity の内容と Web 検索結果が矛盾する場合は、ユーザーの Activity を優先しつつ、
   - 「一般的にはこうだが、あなたのメモではこう書かれている」という形で丁寧に説明してください。
5. それでも分からない・情報が不十分な場合は、無理に断定せず、「ここまでは分かるが、これ以上は不確か」という形で率直に伝えてください。

# 出力フォーマット
- 回答は **必ず日本語** で、**Markdown** 形式で出力してください。
- 1〜2 文で要点をまとめた後に、必要であれば箇条書きや見出しで補足を整理してください。
- コードや設定ファイルを説明するときは、Markdown のコードブロック（```lang）を使ってください。

# トーン・スタイル
- ユーザーの「第二の脳」として、落ち着いてフレンドリーに説明します。
- 専門的な内容でも、できるだけ平易な日本語で噛み砕いて説明します。
- ユーザーがすでに Activity で書いている考えや方針は尊重しつつ、それを補強・更新する形で回答してください。

# 制約
- Activity に何も関連情報がない場合でも、まず「手元の Activity には直接の記録は見つからない」と明示したうえで回答してください。
- 想像だけでユーザーの意図や状況を決めつけないでください。
- 安全でない行動や明らかに有害な行為を助長する回答は行わないでください。
""".strip()  # noqa: E501


class QADependencies(BaseModel):
    """QA Agent が使う依存オブジェクト."""

    activity_retriever: ActivityRetrieveService

    model_config = ConfigDict(arbitrary_types_allowed=True)


def register_qa_tools(agent: Agent[QADependencies, QAResult]) -> None:
    """QA で利用するツールの登録."""

    @agent.tool
    async def search_activities(
        ctx: RunContext[QADependencies],
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
        """  # noqa: E501
        return await ctx.deps.activity_retriever.search_recent_misskey_activity(
            query=query,
            days=days,
            top_k=top_k,
        )


class QAService:
    """Activity retriever."""

    def __init__(
        self,
        agent: Agent[QADependencies, QAResult],
        activity_retrieve_service: ActivityRetrieveService,
        misskey_client: MisskeyClient,
    ) -> None:
        """Initialize."""
        self._agent = agent
        self._activity_retrieve_service = activity_retrieve_service
        self._misskey_client = misskey_client

    @classmethod
    def create(
        cls,
        gemini_settings: GeminiSettings,
        searxng_settings: SearxngSettings,
        activity_retrieve_service: ActivityRetrieveService,
        client: MisskeyClient,
    ) -> Self:
        """Create rag answer."""
        model = create_pydantic_ai_model(gemini_settings, "gemini-2.5-pro")
        searxng_tool = searxng_search_tool(searxng_settings)
        agent = Agent(
            model,
            deps_type=QADependencies,
            output_type=QAResult,
            tools=[searxng_tool],
            system_prompt=QA_SYSTEM_PROMPT,
        )
        register_qa_tools(agent)

        return cls(agent, activity_retrieve_service, client)

    async def ask(self, query: str) -> QAResult:
        """Ask QA."""
        deps = QADependencies(activity_retriever=self._activity_retrieve_service)

        async with self._agent.iter(user_prompt=query, deps=deps) as run:
            async for node in run:
                # ここで node をログに投げる
                logger.info("pydantic-ai node: %r", node)

        if run.result is None:
            msg = "QA agent did not return a result"
            raise RuntimeError(msg)
        return run.result.output
