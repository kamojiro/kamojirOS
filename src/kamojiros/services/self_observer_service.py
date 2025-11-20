"""self_observer_service モジュール."""

from datetime import timedelta
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

    def analyze_daily_activity(self) -> Report:
        """直近24時間の活動を分析し、METAレポートを作成する."""
        now = now_jst()
        since = now - timedelta(hours=24)

        # 直近のレポートを取得
        recent_reports = self._report_repo.find_recent(since)

        # 集計
        total_count = len(recent_reports)
        type_counts: dict[str, int] = {}
        author_counts: dict[str, int] = {}
        tag_counts: dict[str, int] = {}

        for r in recent_reports:
            # Type
            t = r.meta.type.value
            type_counts[t] = type_counts.get(t, 0) + 1

            # Author
            a = r.meta.author.value
            author_counts[a] = author_counts.get(a, 0) + 1

            # Tags
            for tag in r.meta.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # レポート本文作成
        lines = [
            f"# Daily Activity Report ({now.strftime('%Y-%m-%d')})",
            "",
            f"**集計期間**: {since.strftime('%Y-%m-%d %H:%M')} ~ {now.strftime('%H:%M')}",
            "",
            "## Summary",
            "",
            f"- **Total Reports**: {total_count}",
            "",
            "### By Type",
            "",
        ]
        for t, c in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{t}**: {c}")

        lines.extend(["", "### By Author", ""])
        for a, c in sorted(author_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{a}**: {c}")

        lines.extend(["", "### Top Tags", ""])
        for tag, c in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"- **{tag}**: {c}")

        lines.append("")
        body = "\n".join(lines)

        # 保存
        note_id = now.strftime("%Y-%m-%d-%H%M-meta-daily-report")
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
