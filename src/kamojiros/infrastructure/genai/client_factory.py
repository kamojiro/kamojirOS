"""Google Cloud GenAI クライアント作成ファクトリ."""

from google import genai
from google.genai import types as genai_types


def create_genai_client(
    project_id: str,
    *,
    api_key: str | None = None,
    location: str = "us-central1",
    api_version: str = "v1",
) -> genai.Client:
    """Google Cloud GenAI の genai.Client を作る."""
    if api_key is not None:
        return genai.Client(
            api_key=api_key,
        )
    return genai.Client(
        vertexai=True,
        project=project_id,
        location=location,
        http_options=genai_types.HttpOptions(api_version=api_version),
    )
