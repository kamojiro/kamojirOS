"""PydanticAI model factory."""

from typing import TYPE_CHECKING, Literal

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

if TYPE_CHECKING:
    from kamojiros.config.settings import GeminiSettings


def create_pydantic_ai_model(gemini_settings: GeminiSettings, model_name: Literal["gemini-2.5-pro"] = "gemini-2.5-pro") -> GoogleModel:
    """Create PydanticAI model."""
    provider = GoogleProvider(project=gemini_settings.project_id, location="us-central1")
    return GoogleModel(model_name, provider=provider)
