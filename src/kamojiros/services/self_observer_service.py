"""self_observer_service モジュール."""

from datetime import timedelta
from typing import TYPE_CHECKING

from kamojiros.core.naming import make_note_id
from kamojiros.core.time import now_jst
from kamojiros.models import (
    Report,
    ReportAuthor,
    ReportMeta,
    ReportStats,
    ReportType,
)

if TYPE_CHECKING:
    from kamojiros.interfaces.reports import ReportRepository


class SelfObserverService:
    """self_observer 用のサービス."""

    def __init__(self, report_repo: ReportRepository) -> None:
        """初期化."""
        self._report_repo = report_repo

    def analyze_daily_activity(self) -> Report:
        """直近24時間の活動を分析し、METAレポートを作成する."""
        now = now_jst()
        since = now - timedelta(hours=24)

        # 直近のレポートを取得
        recent_reports = self._report_repo.find_recent(since)

        # 集計
        stats = ReportStats.from_reports(recent_reports, period_start=since, period_end=now)

        # レポート本文作成
        lines = [
            f"# Daily Activity Report ({now.strftime('%Y-%m-%d')})",
            "",
            f"**集計期間**: {since.strftime('%Y-%m-%d %H:%M')} ~ {now.strftime('%H:%M')}",
            "",
            "## Summary",
            "",
            f"- **Total Reports**: {stats.total_count}",
            "",
            "### By Type",
            "",
        ]
        for t, c in sorted(stats.by_type.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{t}**: {c}")

        lines.extend(["", "### By Author", ""])
        for a, c in sorted(stats.by_author.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{a}**: {c}")

        lines.extend(["", "### Top Tags", ""])
        for tag, c in sorted(stats.top_tags.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{tag}**: {c}")

        lines.append("")
        body = "\n".join(lines)

        # 保存
        note_id = make_note_id(ReportType.META, "daily-report")
        meta = ReportMeta(
            note_id=note_id,
            title=f"Daily Activity Report {now.strftime('%Y-%m-%d')}",
            created_at=now,
            updated_at=now,
            type=ReportType.META,
            author=ReportAuthor.SELF_OBSERVER,
            tags=["daily-report", "meta"],
        )

        report = Report(meta=meta, body_markdown=body)
        self._report_repo.save(report)
        return report
