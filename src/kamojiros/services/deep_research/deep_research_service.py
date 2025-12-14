"""Deep research report service."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Self

from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import RunUsage

from kamojiros.infrastructure.genai.pydantic_ai_factory import create_pydantic_ai_model
from kamojiros.infrastructure.tools.searxng_search_tool import searxng_search_tool
from kamojiros.services.deep_research.models import (
    DeepResearchResult,
    DeepResearchState,
    Draft,
    ResearchPlan,
    SearchAnswer,
    SearchQuestion,
)
from kamojiros.utils.time import JST

if TYPE_CHECKING:
    from pydantic import HttpUrl

    from kamojiros.config.settings import GeminiSettings, SearxngSettings
    from kamojiros.services.rag.activity_retrieve_service import (
        ActivityRetrieveService,
    )

logger = logging.getLogger(__name__)

# --- 1. Dependencies ---


@dataclass
class DeepResearchDependencies:
    """DeepResearch Agent が使う依存オブジェクト."""

    activity_retriever: ActivityRetrieveService
    now: datetime  # 現在時刻（テスト時に固定値を注入可能）
    state: DeepResearchState | None = None


# --- 2. Constants & Helpers ---


@dataclass(frozen=True)
class GeminiPrice:
    """Gemini model pricing configuration."""

    input_per_m_token: float  # USD / 1,000,000 tokens
    output_per_m_token: float


GEMINI_FLASH_PRICE = GeminiPrice(input_per_m_token=0.30, output_per_m_token=2.50)
GEMINI_PRO_PRICE = GeminiPrice(input_per_m_token=1.25, output_per_m_token=10.00)

LOG_TRUNCATE_LEN_SHORT = 120
LOG_TRUNCATE_LEN_LONG = 400


def estimate_cost_usd(usage: RunUsage, price: GeminiPrice) -> float:
    """Gemini のトークン使用量から USD コストをざっくり見積もる."""
    input_cost = usage.input_tokens * (price.input_per_m_token / 1_000_000)
    output_cost = usage.output_tokens * (price.output_per_m_token / 1_000_000)
    return input_cost + output_cost


PLAN_AGENT_SYSTEM_PROMPT = (
    "You are a research planner. "
    "Given a complex topic, URLs, and user's known info, "
    "produce a structured research plan with 3-7 sections. "
    "Each section should have: id, title, description, priority, status='pending'. "
    "Also set the `strategy` field to explain the overall research strategy in 3-5 sentences."
)

INITIAL_DRAFT_AGENT_SYSTEM_PROMPT = (
    "You are a deep research writer.\n"
    "Write a rough, noisy initial draft in Markdown for the given topic, "
    "mainly from the model's internal knowledge and the research plan.\n"
    "It's okay to be incomplete; explicitly mark unknown parts as 'TODO:' or 'TBD:'.\n"
    "\n"
    "Requirements:\n"
    "- Aim for at least 3,000-5,000 Japanese characters in total.\n"
    "- For each plan section, write 2-4 subsections with concrete details.\n"
    "- Prefer technical depth over brevity: include mechanisms, examples, and trade-offs.\n"
)

SEARCH_QUESTION_AGENT_SYSTEM_PROMPT = (
    "You look at the current draft, research plan, and Q/A history, "
    "and propose the next search question that will most improve the draft.\n"
    "Pick ONE plan section that is still shallow or missing important details, "
    "and craft a focused, technical question.\n"
    "Examples of 'shallow' sections:\n"
    "- Only high-level bullet points with no concrete mechanisms\n"
    "- No comparison with alternatives\n"
    "- No real-world examples or case studies\n"
    "\n"
    "Use the `id` of that section as `section_id`.\n"
    "If and only if all sections have enough technical depth, "
    "set section_id='DONE' and text='NO_MORE_QUESTIONS'."
)

ANSWER_AGENT_SYSTEM_PROMPT = (
    "You are a RAG-style answer generator.\n"
    "Use the available tools to search the user's activity, "
    "then synthesize a concise but information-dense answer in Markdown.\n"
    "Set `answer_markdown` to the final answer.\n"
    "Fill `used_urls` with URLs you actually referenced in your reasoning, "
    "and set `notes` if there are limitations or TODOs.\n"
    "Prefer precise facts, avoid speculation."
)

DRAFT_DENOISER_AGENT_SYSTEM_PROMPT = (
    "You are a draft denoiser in a Test-Time Diffusion deep research agent.\n"
    "Given the current noisy draft, the research plan, and all Q/A history, "
    "update the draft in-place:\n"
    "- Integrate new factual information at appropriate places\n"
    "- Remove or correct hallucinations and inconsistencies\n"
    "- Reduce redundancy\n"
    "- Identify shallow sections and expand them with mechanisms, examples, or comparisons\n"
    "- Explicitly list remaining open questions in `open_issues`\n"
    "Return the FULL updated draft in `markdown`.\n"
)

FINAL_REPORT_AGENT_SYSTEM_PROMPT = (
    "You are the final report generator of a deep research agent.\n"
    "Given the latest draft, the research plan, and all Q/A pairs, "
    "produce a polished, coherent Markdown report in Japanese.\n"
    "\n"
    "The report must:\n"
    "- Directly answer the user's topic and intent\n"
    "- Be well-structured with headings and subheadings\n"
    "- Include limitations and remaining uncertainties\n"
    "- Have enough depth and length: aim for at least 4,000-6,000 Japanese characters.\n"
    "- For technical topics, explain:\n"
    "  - Background and motivation\n"
    "  - Architecture / components or key concepts\n"
    "  - Detailed mechanisms, with step-by-step descriptions\n"
    "  - Pros/cons, trade-offs, and alternatives\n"
    "  - Practical tips / examples / pitfalls\n"
    "  - Open questions and future directions\n"
    "\n"
    "Set:\n"
    "- `title` to a concise report title\n"
    "- `final_report_markdown` to the full report body\n"
    "- `plan` to the final version of the research plan\n"
    "- `qa_history` to the final list of Q/A pairs\n"
    "- `type` to the appropriate report type (one of: 'tech', 'paper', 'food', 'life', 'meta')\n"
    "- `tags` to a list of relevant tags\n"
    "- `source_urls` to a list of fully qualified URLs (HttpUrl) referenced in the report"
)


# --- 2. Tool Definition ---


def register_answer_agent_tools(agent: Agent[DeepResearchDependencies, SearchAnswer]) -> None:
    """Answer Agent 用ツールの登録."""

    @agent.system_prompt(dynamic=True)
    def add_current_time(ctx: RunContext[DeepResearchDependencies]) -> str:
        """現在時刻を動的に system prompt に追加する."""
        now = ctx.deps.now
        return f"# 現在時刻\n現在時刻 (JST): {now.isoformat()}\n今日の日付: {now.date().isoformat()}"

    @agent.tool
    async def search_activities(
        ctx: RunContext[DeepResearchDependencies],
        query: str,
        days: int | None = 30,
        top_k: int | None = 10,
    ) -> list[str]:
        r"""ユーザーのメモをベクトル検索して返すツール.

        返り値は以下形式の文字列のリスト:
        "<created_at ISO8601> <source_url>\\n<content>"
        - ユーザーのメモはユーザーから与えられた URL やキーワードをもとに、検索を使って LLM によって生成されている
        - ユーザーの「最近の投稿」「最近考えていること」「これまでに学んだことがあること」
          「これまでに興味を持ったもの」などに答えるときに使う
        - query にはユーザーの質問内容、またはその要約を入れる
        - days が None のときは全期間から検索する
        - top_k は多くの情報やより多くの情報が必要な場合に大きくする
        """
        activities = await ctx.deps.activity_retriever.search_recent_misskey_activity(
            query=query,
            days=days,
            top_k=top_k,
        )
        return [f"{a.created_at.isoformat()} {a.source_url}\n{a.content}" for a in activities]


# --- 3. Service Implementation ---


class DeepResearchService:
    """Deep research service (TTD-DR implementation)."""

    def __init__(
        self,
        activity_retrieve_service: ActivityRetrieveService,
        plan_agent: Agent[DeepResearchDependencies, ResearchPlan],
        initial_draft_agent: Agent[DeepResearchDependencies, Draft],
        search_question_agent: Agent[DeepResearchDependencies, SearchQuestion],
        answer_agent: Agent[DeepResearchDependencies, SearchAnswer],
        draft_denoiser_agent: Agent[DeepResearchDependencies, Draft],
        final_report_agent: Agent[DeepResearchDependencies, DeepResearchResult],
        *,
        max_iterations: int = 8,
    ) -> None:
        """Initialize."""
        self._activity_retrieve_service = activity_retrieve_service
        self._plan_agent = plan_agent
        self._initial_draft_agent = initial_draft_agent
        self._search_question_agent = search_question_agent
        self._answer_agent = answer_agent
        self._draft_denoiser_agent = draft_denoiser_agent
        self._final_report_agent = final_report_agent
        self._max_iterations = max_iterations

    @classmethod
    def create(
        cls,
        gemini_settings: GeminiSettings,
        searxng_settings: SearxngSettings,
        activity_retrieve_service: ActivityRetrieveService,
    ) -> Self:
        """Create service with all agents."""
        flash_model = create_pydantic_ai_model(gemini_settings, model_name="gemini-2.5-flash")
        pro_model = create_pydantic_ai_model(gemini_settings, model_name="gemini-2.5-pro")

        searxng_tool = searxng_search_tool(searxng_settings)

        # 1. Plan Agent
        plan_agent = Agent(
            flash_model,
            deps_type=DeepResearchDependencies,
            output_type=ResearchPlan,
            system_prompt=PLAN_AGENT_SYSTEM_PROMPT,
        )

        # 2. Initial Draft Agent
        initial_draft_agent = Agent(
            flash_model,
            deps_type=DeepResearchDependencies,
            output_type=Draft,
            system_prompt=INITIAL_DRAFT_AGENT_SYSTEM_PROMPT,
        )

        # 3. Search Question Generator (Stage 2a)
        search_question_agent = Agent(
            flash_model,
            deps_type=DeepResearchDependencies,
            output_type=SearchQuestion,
            system_prompt=SEARCH_QUESTION_AGENT_SYSTEM_PROMPT,
        )

        # 4. Answer Agent (Stage 2b) - RAG
        answer_agent = Agent(
            flash_model,
            deps_type=DeepResearchDependencies,
            output_type=SearchAnswer,
            tools=[searxng_tool],
            system_prompt=ANSWER_AGENT_SYSTEM_PROMPT,
        )
        register_answer_agent_tools(answer_agent)

        # 5. Draft Denoiser (Stage 2c)
        draft_denoiser_agent = Agent(
            flash_model,
            deps_type=DeepResearchDependencies,
            output_type=Draft,
            system_prompt=DRAFT_DENOISER_AGENT_SYSTEM_PROMPT,
        )

        # 6. Final Report Agent (Stage 3)
        final_report_agent = Agent(
            pro_model,
            deps_type=DeepResearchDependencies,
            output_type=DeepResearchResult,
            system_prompt=FINAL_REPORT_AGENT_SYSTEM_PROMPT,
        )

        return cls(
            activity_retrieve_service=activity_retrieve_service,
            plan_agent=plan_agent,
            initial_draft_agent=initial_draft_agent,
            search_question_agent=search_question_agent,
            answer_agent=answer_agent,
            draft_denoiser_agent=draft_denoiser_agent,
            final_report_agent=final_report_agent,
        )

    async def run_deep_research(
        self,
        *,
        topic: str,
        urls: list[HttpUrl] | None = None,
        known_info: str | None = None,
    ) -> DeepResearchResult:
        """Run the TTD-DR research loop."""
        state = DeepResearchState(
            topic=topic,
            urls=urls or [],
            known_info=known_info,
        )

        logger.info(
            "DeepResearch start: topic=%r urls=%d known_info_len=%d",
            topic,
            len(state.urls),
            len(known_info or ""),
        )

        deps = DeepResearchDependencies(
            activity_retriever=self._activity_retrieve_service,
            now=datetime.now(tz=JST),
            state=state,
        )

        # Usage tracking
        flash_usage = RunUsage()
        pro_usage = RunUsage()

        # --- Stage 1 & 2: Plan + Initial Draft ---
        await self._run_plan_and_initial_draft(
            topic=topic,
            known_info=known_info,
            state=state,
            deps=deps,
            flash_usage=flash_usage,
        )

        # --- Stage 3: Diffusion Loop (Denoising with Retrieval) ---
        await self._run_diffusion_loop(
            topic=topic,
            state=state,
            deps=deps,
            flash_usage=flash_usage,
        )

        # --- Stage 4: Final report ---
        result = await self._run_final_report(
            topic=topic,
            state=state,
            deps=deps,
            pro_usage=pro_usage,
        )

        # Usage / cost logging
        self._log_usage_and_cost(flash_usage=flash_usage, pro_usage=pro_usage)

        return result

    async def _run_plan_and_initial_draft(
        self,
        *,
        topic: str,
        known_info: str | None,
        state: DeepResearchState,
        deps: DeepResearchDependencies,
        flash_usage: RunUsage,
    ) -> None:
        """Stage 1 & 2: Plan + initial draft."""
        # --- Stage 1: Plan ---
        plan_result = await self._plan_agent.run(
            (
                f"Topic: {topic}\n"
                f"User-known info:\n{known_info or '(none)'}\n"
                f"Seed URLs:\n" + "\n".join(map(str, state.urls))
            ),
            deps=deps,
        )
        flash_usage += plan_result.usage()
        state.plan = plan_result.output

        if state.plan:
            logger.info(
                "DeepResearch plan generated: sections=%d",
                len(state.plan.sections),
            )
            logger.info("DeepResearch plan JSON: %s", state.plan.model_dump_json(indent=2))

        # --- Stage 2: Initial Draft ---
        draft0 = await self._initial_draft_agent.run(
            (f"Write an initial rough draft for topic '{topic}'. Use the research plan above as a scaffold."),
            deps=deps,
        )
        flash_usage += draft0.usage()
        state.draft = draft0.output

    async def _run_diffusion_loop(
        self,
        *,
        topic: str,
        state: DeepResearchState,
        deps: DeepResearchDependencies,
        flash_usage: RunUsage,
    ) -> None:
        """Stage 3: TTD-DR の拡散/デノイズループ."""
        for i in range(self._max_iterations):
            state.iterations = i + 1

            if not state.draft or not state.plan:
                logger.warning(
                    "DeepResearch: missing draft/plan at iteration=%d, breaking loop",
                    state.iterations,
                )
                break

            logger.info("DeepResearch iteration %d: start", state.iterations)

            plan_text = state.plan.model_dump_json(indent=2)
            qa_text = (
                "\n".join(
                    f"- [{a.section_id}] Q: {a.question}\n  A: {a.answer_markdown[:1000]}..." for a in state.qa_history
                )
                or "(none)"
            )

            # 2a: decide next search question
            question = await self._run_search_question(
                state=state,
                deps=deps,
                plan_text=plan_text,
                qa_text=qa_text,
                flash_usage=flash_usage,
            )

            if question.section_id == "DONE":
                logger.info(
                    "DeepResearch iteration %d: all sections sufficiently covered, stopping loop",
                    state.iterations,
                )
                break

            # 2b: search & synthesize answer (RAG)
            answer = await self._run_answer_step(
                topic=topic,
                question=question,
                state=state,
                deps=deps,
                flash_usage=flash_usage,
            )
            state.qa_history.append(answer)

            # 2c: denoise draft
            await self._run_denoise_step(
                topic=topic,
                state=state,
                deps=deps,
                plan_text=plan_text,
                flash_usage=flash_usage,
            )

    async def _run_search_question(
        self,
        *,
        state: DeepResearchState,
        deps: DeepResearchDependencies,
        plan_text: str,
        qa_text: str,
        flash_usage: RunUsage,
    ) -> SearchQuestion:
        """Stage 3-1: Search question generation."""
        q_result = await self._search_question_agent.run(
            (
                "Based on the current state, propose the next search question.\n"
                f"Current draft:\n{state.draft.markdown if state.draft else ''}\n\n"
                f"Plan (JSON):\n{plan_text}\n\n"
                f"Q/A history (may be empty):\n{qa_text}\n"
            ),
            deps=deps,
        )
        flash_usage += q_result.usage()
        question = q_result.output

        logger.info(
            "DeepResearch iteration %d: search question -> section_id=%s text=%s",
            state.iterations,
            question.section_id,
            (question.text[:LOG_TRUNCATE_LEN_SHORT] + "…")
            if len(question.text) > LOG_TRUNCATE_LEN_SHORT
            else question.text,
        )
        return question

    async def _run_answer_step(
        self,
        *,
        topic: str,
        question: SearchQuestion,
        state: DeepResearchState,
        deps: DeepResearchDependencies,
        flash_usage: RunUsage,
    ) -> SearchAnswer:
        """Stage 3-2: Answer (RAG) step."""
        a_result = await self._answer_agent.run(
            (
                f"Topic: {topic}\n"
                f"Target plan section: {question.section_id}\n"
                f"Question: {question.text}\n"
                f"Current draft:\n{state.draft.markdown if state.draft else ''}\n"
            ),
            deps=deps,
        )
        flash_usage += a_result.usage()
        answer = a_result.output

        logger.info(
            "DeepResearch iteration %d: answer (first %d chars): %s",
            state.iterations,
            LOG_TRUNCATE_LEN_LONG,
            (answer.answer_markdown[:LOG_TRUNCATE_LEN_LONG] + "…")
            if len(answer.answer_markdown) > LOG_TRUNCATE_LEN_LONG
            else answer.answer_markdown,
        )
        return answer

    async def _run_denoise_step(
        self,
        *,
        topic: str,
        state: DeepResearchState,
        deps: DeepResearchDependencies,
        plan_text: str,
        flash_usage: RunUsage,
    ) -> None:
        """Stage 3-3: Draft denoising step."""
        qa_text = (
            "\n".join(
                f"- [{a.section_id}] Q: {a.question}\n  A: {a.answer_markdown[:1000]}..." for a in state.qa_history
            )
            or "(none)"
        )

        d_result = await self._draft_denoiser_agent.run(
            (
                f"Topic: {topic}\n"
                f"Plan (JSON): {plan_text}\n"
                f"Current draft:\n{state.draft.markdown if state.draft else ''}\n"
                f"All Q/A pairs:\n{qa_text}\n"
            ),
            deps=deps,
        )
        flash_usage += d_result.usage()
        state.draft = d_result.output

        logger.info(
            "DeepResearch iteration %d: updated draft (first %d chars): %s",
            state.iterations,
            LOG_TRUNCATE_LEN_LONG,
            (state.draft.markdown[:LOG_TRUNCATE_LEN_LONG] + "…")
            if len(state.draft.markdown) > LOG_TRUNCATE_LEN_LONG
            else state.draft.markdown,
        )

    async def _run_final_report(
        self,
        *,
        topic: str,
        state: DeepResearchState,
        deps: DeepResearchDependencies,
        pro_usage: RunUsage,
    ) -> DeepResearchResult:
        """Stage 4: Final report generation."""
        plan_text = state.plan.model_dump_json(indent=2) if state.plan else "(none)"
        qa_text = "\n".join(f"- [{a.section_id}] Q: {a.question}\n  A: {a.answer_markdown}" for a in state.qa_history)

        final_result = await self._final_report_agent.run(
            (
                f"Topic: {topic}\n"
                f"Final draft to polish:\n{state.draft.markdown if state.draft else ''}\n"
                f"Plan (JSON): {plan_text}\n"
                f"Q/A history (Markdown list): {qa_text}\n"
            ),
            deps=deps,
        )
        pro_usage += final_result.usage()

        result = final_result.output
        logger.debug(
            "DeepResearch final report body (first %d chars): %s",
            LOG_TRUNCATE_LEN_LONG,
            (result.final_report_markdown[:LOG_TRUNCATE_LEN_LONG] + "…")
            if len(result.final_report_markdown) > LOG_TRUNCATE_LEN_LONG
            else result.final_report_markdown,
        )
        return result

    def _log_usage_and_cost(self, *, flash_usage: RunUsage, pro_usage: RunUsage) -> None:
        """Log usage and estimated cost."""
        flash_cost = estimate_cost_usd(flash_usage, GEMINI_FLASH_PRICE)
        pro_cost = estimate_cost_usd(pro_usage, GEMINI_PRO_PRICE)
        total_cost = flash_cost + pro_cost
        total_usage = flash_usage + pro_usage

        logger.info(
            "deep_research usage (Total): input=%d, output=%d, requests=%d",
            total_usage.input_tokens,
            total_usage.output_tokens,
            total_usage.requests,
        )
        logger.info(
            "deep_research usage (Flash): input=%d, output=%d, requests=%d",
            flash_usage.input_tokens,
            flash_usage.output_tokens,
            flash_usage.requests,
        )
        logger.info(
            "deep_research usage (Pro)  : input=%d, output=%d, requests=%d",
            pro_usage.input_tokens,
            pro_usage.output_tokens,
            pro_usage.requests,
        )
        logger.info(
            "deep_research cost estimate: $%.4f (flash=$%.4f, pro=$%.4f)",
            total_cost,
            flash_cost,
            pro_cost,
        )
