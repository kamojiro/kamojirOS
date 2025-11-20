"""SelfObserverService の単体テスト."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from kamojiros.core.time import JST
from kamojiros.models import Report, ReportAuthor, ReportMeta, ReportType
from kamojiros.services.self_observer_service import SelfObserverService

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def _make_report(
    created_at: datetime,
    report_type: ReportType = ReportType.TECH,
    author: ReportAuthor = ReportAuthor.USER,
    tags: list[str] | None = None,
) -> Report:
    """テスト用の Report を作成するヘルパー."""
    if tags is None:
        tags = []

    meta = ReportMeta(
        note_id="test-note",
        title="Test Note",
        created_at=created_at,
        updated_at=created_at,
        type=report_type,
        author=author,
        tags=tags,
        source_urls=[],
    )
    return Report(meta=meta, body_markdown="body")


def test_analyze_daily_activity_aggregates_correctly(mocker: MockerFixture) -> None:
    """analyze_daily_activity が正しく集計してレポートを保存することを検証する."""
    # Mock Repository
    mock_repo = mocker.Mock()

    # 準備: find_recent が返すレポート
    now = datetime.now(tz=JST)
    reports = [
        _make_report(now, report_type=ReportType.TECH, author=ReportAuthor.USER, tags=["python", "agent"]),
        _make_report(now, report_type=ReportType.TECH, author=ReportAuthor.USER, tags=["python"]),
        _make_report(now, report_type=ReportType.LIFE, author=ReportAuthor.USER, tags=["food"]),
    ]
    mock_repo.find_recent.return_value = reports

    # Service 実行
    service = SelfObserverService(report_repo=mock_repo)

    # 時間固定 (now_jst を mock)
    mock_now = datetime(2025, 11, 20, 19, 0, 0, tzinfo=JST)
    mocker.patch("kamojiros.services.self_observer_service.now_jst", return_value=mock_now)

    service.analyze_daily_activity()

    # 検証: find_recent が呼ばれたか
    expected_since = mock_now - timedelta(hours=24)
    mock_repo.find_recent.assert_called_once_with(expected_since)

    # 検証: save が呼ばれたか
    mock_repo.save.assert_called_once()
    saved_report: Report = mock_repo.save.call_args[0][0]

    # Check saved report content
    assert saved_report.meta.type == ReportType.META
    assert saved_report.meta.author == ReportAuthor.SELF_OBSERVER
    assert "daily-report" in saved_report.meta.tags

    # 本文に集計結果が含まれているか
    body = saved_report.body_markdown
    assert "Total Reports**: 3" in body
    assert "tech**: 2" in body
    assert "life**: 1" in body
    assert "user**: 3" in body
    assert "python**: 2" in body
    assert "food**: 1" in body
