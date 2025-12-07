"""Self Observer Service."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from kamojiros.config.settings import SelfObserverSettings
from kamojiros.models import Report, ReportAuthor, ReportMeta, ReportType
from kamojiros.utils.naming import make_note_id

if TYPE_CHECKING:
    from kamojiros.infrastructure.files.activity_repository import ActivityRepository
    from kamojiros.services.report_service import ReportService


class SelfObserverService:
    """自己観察エージェントのサービス."""

    def __init__(
        self,
        report_service: ReportService,
        activity_repository: ActivityRepository,
        settings: SelfObserverSettings | None = None,
    ) -> None:
        """Initialize SelfObserverService."""
        self.report_service = report_service
        self.activity_repository = activity_repository
        self.settings = settings or SelfObserverSettings()
        self.tz = ZoneInfo(self.settings.timezone)

    def observe(self, target_date: datetime | None = None) -> Report:
        """指定日の活動を収集・分析してレポートを作成する."""
        if target_date is None:
            # デフォルトは「昨日」のレポートを作成
            now = datetime.now(self.tz)
            target_date = now - timedelta(days=1)

        # 1日の範囲を設定 (00:00:00 - 23:59:59)
        start_dt = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # 1. 活動履歴の収集
        activities = self.activity_repository.get_activities(start_dt, end_dt)

        # 2. レポート本文の生成
        title = f"Daily Report: {start_dt.strftime('%Y-%m-%d')}"
        body = self._generate_report_body(start_dt, activities)

        # 3. レポート保存
        note_id = make_note_id(ReportType.META, f"daily-{start_dt.strftime('%Y-%m-%d')}")

        meta = ReportMeta(
            note_id=note_id,
            title=title,
            date=start_dt.date(),
            created_at=datetime.now(self.tz),
            updated_at=datetime.now(self.tz),
            type=ReportType.META,
            author=ReportAuthor.SELF_OBSERVER,
            tags=["daily-report", "self-observer"],
        )

        report = Report(meta=meta, body_markdown=body)
        self.report_service.save_report(report)

        return report

    def _generate_report_body(self, date: datetime, activities: list) -> str:
        """レポート本文を生成する."""
        lines = [
            f"# {date.strftime('%Y-%m-%d')} の活動報告",
            "",
            "## 活動ログ (Misskey)",
            "",
        ]

        if not activities:
            lines.append("活動記録はありませんでした。")
        else:
            for act in activities:
                time_str = act.created_at.astimezone(self.tz).strftime("%H:%M")
                content = act.content.replace("\n", " ")[:100]  # 1行にまとめる
                lines.append(f"- `{time_str}` {content}")

        lines.append("")
        lines.append("## 所感")
        lines.append("(ここにエージェントの分析が入る予定)")

        return "\n".join(lines)
