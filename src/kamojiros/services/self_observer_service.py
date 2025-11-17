"""self_observer_service モジュール."""

from typing import TYPE_CHECKING

from kamojiros.core.time import now_jst
from kamojiros.models import (
    Report,
    ReportAuthor,
    ReportMeta,
    ReportType,
)

if TYPE_CHECKING:
    from kamojiros.interfaces.reports import ReportRepository


class SelfObserverService:
    """self_observer 用のサービス."""

    def __init__(self, report_repo: ReportRepository) -> None:
        """初期化."""
        self._report_repo = report_repo

    def create_test_report(self) -> Report:
        """自己観察エージェント用のテストレポートを作成して保存する."""
        now = now_jst()
        note_id = now.strftime("%Y-%m-%d-%H%M-meta-self-observer-test")

        meta = ReportMeta(
            note_id=note_id,
            title="self_observer v0 テストノート",
            created_at=now,
            updated_at=now,
            type=ReportType.META,
            author=ReportAuthor.SELF_OBSERVER,
            tags=["test", "self-observer"],
        )

        body = (
            "# self_observer v0 テスト\n\n"
            f"- 生成時刻: {now.isoformat()}\n"
            "- これは最初のテストノートです。\n"
            "- Kamomo Notes に journal として保存されます。\n"
        )

        report = Report(meta=meta, body_markdown=body)
        self._report_repo.save(report)
        return report
