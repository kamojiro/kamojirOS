"""Deep research models."""

from typing import Literal

from pydantic import BaseModel, HttpUrl


class ResearchPlanSection(BaseModel):
    """Research plan section."""

    id: str
    title: str
    description: str
    priority: int = 0
    status: Literal["pending", "in_progress", "done"] = "pending"


class ResearchPlan(BaseModel):
    """Research plan."""

    sections: list[ResearchPlanSection]


class SearchQuestion(BaseModel):
    """Search question."""

    section_id: str
    text: str
    rationale: str  # なぜこの質問が必要か


class SearchAnswer(BaseModel):
    """Search result."""

    section_id: str
    question: str
    answer_markdown: str
    used_urls: list[HttpUrl] = []
    notes: str | None = None  # 限界や TODO など


class Draft(BaseModel):
    """Draft."""

    markdown: str


class DeepResearchState(BaseModel):
    """Deep research state."""

    topic: str
    urls: list[HttpUrl] = []
    known_info: str | None = None

    plan: ResearchPlan | None = None
    draft: Draft | None = None
    qa_history: list[SearchAnswer] = []
    iterations: int = 0


class DeepResearchResult(BaseModel):
    """Deep research result."""

    final_report_markdown: str
    plan: ResearchPlan
    qa_history: list[SearchAnswer]
