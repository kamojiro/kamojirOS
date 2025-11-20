"""ReportService - CLI用のビジネスロジック."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from kamojiros.core.time import now_jst
from kamojiros.models import Report, ReportAuthor, ReportMeta, ReportType

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
        note_id = now.strftime(f"%Y-%m-%d-%H%M-{report_type.value}-{title[:20]}")
        # note_idはファイル名に使うので安全な文字のみ
        note_id = note_id.replace(" ", "-").replace("/", "-")

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

    def get_statistics(self, since: datetime | None = None) -> dict:
        """統計情報を取得する."""
        if since is None:
            since = now_jst() - timedelta(days=30)

        reports = self._report_repo.find_recent(since)

        # 型別集計
        type_counts: dict[str, int] = {}
        for report in reports:
            type_counts[report.meta.type.value] = type_counts.get(report.meta.type.value, 0) + 1

        # 著者別集計
        author_counts: dict[str, int] = {}
        for report in reports:
            author_counts[report.meta.author.value] = author_counts.get(report.meta.author.value, 0) + 1

        # タグ別集計
        tag_counts: dict[str, int] = {}
        for report in reports:
            for tag in report.meta.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # タグを頻度順にソート
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_count": len(reports),
            "period_start": since.isoformat(),
            "period_end": now_jst().isoformat(),
            "by_type": type_counts,
            "by_author": author_counts,
            "top_tags": dict(sorted_tags[:10]),  # 上位10タグ
        }
