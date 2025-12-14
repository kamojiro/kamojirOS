"""PydanticAI model factory."""

from functools import lru_cache
from typing import TYPE_CHECKING, Literal

from httpx import AsyncClient, HTTPStatusError, Response
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig
from tenacity import RetryCallState, retry_if_exception, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from kamojiros.config.settings import GeminiSettings


ModelName = Literal["gemini-2.5-pro", "gemini-2.5-flash"]

RESOURCE_EXHAUSTED_STATUS = 429


def _extract_error_json_from_http_status_error(e: HTTPStatusError) -> dict | None:
    try:
        return e.response.json()
    except Exception:  # noqa: BLE001
        return None


def _is_daily_quota(error_json: dict) -> bool:
    """Gemini API の 429 payload の QuotaFailure から PerDay 系か判定する.

    例: quotaId='GenerateRequestsPerDayPerProjectPerModel-FreeTier'
    """
    err = error_json.get("error") or {}
    details = err.get("details") or []
    for d in details:
        if not isinstance(d, dict):
            continue
        t = d.get("@type") or ""
        if t.endswith("QuotaFailure"):
            for v in d.get("violations", []) or []:
                if not isinstance(v, dict):
                    continue
                qid = v.get("quotaId") or ""
                if "PerDay" in qid:
                    return True
    return False


def _extract_retry_delay_seconds(error_json: dict) -> float | None:
    """Gemini API の 429 payload の RetryInfo.retryDelay を読む.

    例: retryDelay='31s' / '31.468721299s'
    """
    err = error_json.get("error") or {}
    details = err.get("details") or []
    for d in details:
        if not isinstance(d, dict):
            continue
        t = d.get("@type") or ""
        if t.endswith("RetryInfo"):
            rd = d.get("retryDelay")
            if isinstance(rd, str) and rd.endswith("s"):
                try:
                    return float(rd[:-1])
                except ValueError:
                    return None
    return None


def _retry_condition(exc: BaseException) -> bool:
    """リトライ判断関数.

    - 429 でも「日次」っぽい場合は retry しない（= 失敗で落とす）
    - 分次/RPM/TPM っぽい 429 は retryDelay を尊重して retry
    """
    if isinstance(exc, HTTPStatusError) and exc.response.status_code == RESOURCE_EXHAUSTED_STATUS:
        j = _extract_error_json_from_http_status_error(exc)
        return not (isinstance(j, dict) and _is_daily_quota(j))

    # ここは好みで.とりあえず一時的な 5xx は retry 対象にしておく
    return isinstance(exc, HTTPStatusError) and exc.response.status_code in (502, 503, 504)


def _wait_using_retry_delay_or_backoff(state: RetryCallState) -> float:
    """429 の body に RetryInfo.retryDelay が入ってたらそれを優先.なければ exponential backoff."""
    exc = state.outcome.exception() if state.outcome else None
    if isinstance(exc, HTTPStatusError) and exc.response.status_code == RESOURCE_EXHAUSTED_STATUS:
        j = _extract_error_json_from_http_status_error(exc)
        if isinstance(j, dict):
            sec = _extract_retry_delay_seconds(j)
            if sec is not None:
                # 念のため上限（1分運用なら 60s cap でもOK）
                return min(sec, 60.0)

    # fallback
    return wait_exponential(multiplier=1, max=60)(state)


@lru_cache(maxsize=1)
def _create_retrying_http_client() -> AsyncClient:
    """AI Studio(Gemini API) 用の httpx client with retry.

    GoogleProvider(http_client=...) に渡すと、そこ経由の Agent 全部に効く.
    """

    def should_retry_status(response: Response) -> None:
        # ここで raise しないと tenacity が retry できないので注意
        if response.status_code in (429, 502, 503, 504):
            response.raise_for_status()

    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception(_retry_condition),
            wait=_wait_using_retry_delay_or_backoff,
            stop=stop_after_attempt(5),
            reraise=True,
        ),
        validate_response=should_retry_status,
    )
    return AsyncClient(transport=transport, timeout=60)


def create_pydantic_ai_model(
    gemini_settings: GeminiSettings,
    *,
    vertex: bool = False,
    model_name: ModelName = "gemini-2.5-flash",
) -> GoogleModel:
    """Create PydanticAI model.

    方針:
    - gemini-2.5-pro は常に Vertex 固定
    - gemini-2.5-flash は、vertex=False かつ api_key があれば AI Studio 優先
      - ただし 429 は body の retryDelay を尊重して retry
      - PerDay(日次) が含まれる 429 は retry せず例外で落とす
    """
    provider: GoogleProvider

    # pro は AI Studio を試さない
    if model_name == "gemini-2.5-pro":
        vertex = True

    if (not vertex) and getattr(gemini_settings, "api_key", None) and model_name == "gemini-2.5-flash":
        # AI Studio (Gemini API / GLA)
        provider = GoogleProvider(
            api_key=gemini_settings.api_key,
            http_client=_create_retrying_http_client(),
        )
    else:
        # Vertex
        provider = GoogleProvider(
            project=gemini_settings.project_id,
            location="us-central1",
        )

    return GoogleModel(model_name, provider=provider)
