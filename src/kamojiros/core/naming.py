"""命名規則に関するヘルパー関数群."""

from kamojiros.core.time import now_jst
from kamojiros.models import ReportType  # noqa: TC001


def make_note_id(report_type: ReportType, slug: str) -> str:
    """Generate Note ID.

    Format: YYYY-MM-DD-HHMM-{type}-{slug}
    """
    now = now_jst()
    # 安全な文字のみにする
    safe_slug = slug.replace(" ", "-").replace("/", "-")
    # 長すぎる場合は切り詰める (40文字程度)
    safe_slug = safe_slug[:40]

    return now.strftime(f"%Y-%m-%d-%H%M-{report_type.value}-{safe_slug}")
