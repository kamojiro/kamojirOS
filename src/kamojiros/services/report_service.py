"""ReportService - CLI用のビジネスロジック."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from kamojiros.core.naming import make_note_id
from kamojiros.core.time import now_jst
from kamojiros.models import Report, ReportAuthor, ReportMeta, ReportStats, ReportType

if TYPE_CHECKING:
    from kamojiros.interfaces.reports import ReportRepository


class ReportService:
    """レポート操作のビジネスロジック."""

    def __init__(self, report_repo: ReportRepository) -> None:
        """初期化."""
        self._report_repo = report_repo

    def create_report(
        self,
        title: str,
        body: str,
        report_type: ReportType,
        author: ReportAuthor = ReportAuthor.USER,
        tags: list[str] | None = None,
    ) -> Report:
        """新しいレポートを作成して保存する."""
        now = now_jst()
        note_id = make_note_id(report_type, title)

        meta = ReportMeta(
            note_id=note_id,
            title=title,
            created_at=now,
            updated_at=now,
            type=report_type,
            author=author,
            tags=tags or [],
            source_urls=[],
        )

        report = Report(meta=meta, body_markdown=body)
        self._report_repo.save(report)
        return report

    def list_reports(
        self,
        limit: int | None = None,
        since: datetime | None = None,
        report_type: ReportType | None = None,
        author: ReportAuthor | None = None,
        tags: list[str] | None = None,
    ) -> list[Report]:
        """レポート一覧を取得する（フィルタリング付き）."""
        # sinceが指定されていない場合は過去30日間
        if since is None:
            since = now_jst() - timedelta(days=30)

        reports = self._report_repo.find_recent(since)

        # フィルタリング
        if report_type is not None:
            reports = [r for r in reports if r.meta.type == report_type]

        if author is not None:
            reports = [r for r in reports if r.meta.author == author]

        if tags:
            reports = [r for r in reports if any(tag in r.meta.tags for tag in tags)]

        # 新しい順にソート
        reports = sorted(reports, key=lambda r: r.meta.updated_at, reverse=True)

        # limit適用
        if limit is not None:
            reports = reports[:limit]

        return reports

    def search_reports(
        self,
        keyword: str,
        *,
        search_in_title: bool = True,
        search_in_body: bool = True,
        search_in_tags: bool = True,
    ) -> list[Report]:
        """キーワードでレポートを検索する."""
        # 過去1年分を検索対象とする
        since = now_jst() - timedelta(days=365)
        reports = self._report_repo.find_recent(since)

        keyword_lower = keyword.lower()
        results = []

        for report in reports:
            match = False

            if search_in_title and keyword_lower in report.meta.title.lower():
                match = True

            if search_in_body and keyword_lower in report.body_markdown.lower():
                match = True

            if search_in_tags:
                for tag in report.meta.tags:
                    if keyword_lower in tag.lower():
                        match = True
                        break

            if match:
                results.append(report)

        # 新しい順にソート
        return sorted(results, key=lambda r: r.meta.updated_at, reverse=True)

    def get_statistics(self, since: datetime | None = None) -> ReportStats:
        """統計情報を取得する."""
        if since is None:
            since = now_jst() - timedelta(days=30)

        reports = self._report_repo.find_recent(since)
        return ReportStats.from_reports(reports, period_start=since, period_end=now_jst())
