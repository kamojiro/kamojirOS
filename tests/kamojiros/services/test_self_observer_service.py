"""SelfObserverService の単体テスト."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from pydantic import AnyHttpUrl

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

from kamojiros.config.settings import SelfObserverSettings
from kamojiros.models import Activity, ActivitySource, ActivityType, Report, ReportAuthor, ReportType
from kamojiros.services.self_observer_service import SelfObserverService


def _make_activity(
    created_at: datetime,
    content: str = "test note",
) -> Activity:
    """テスト用の Activity を作成するヘルパー."""
    return Activity(
        id="test-id",
        source=ActivitySource.MISSKEY,  # Added
        source_id="test-source-id",  # Added
        type=ActivityType.NOTE,
        content=content,
        created_at=created_at,
        author_id="test-author-id",  # Added
        author_username="test-user",  # Added
        source_url=AnyHttpUrl("https://example.com/notes/test-id"),
        raw_data={},
    )


def test_observe_creates_report(mocker: MockerFixture) -> None:
    """Observe が正しくレポートを作成・保存することを検証する."""
    # Mock Dependencies
    mock_report_service = mocker.Mock()
    mock_activity_repo = mocker.Mock()

    # Prepare data
    tz = ZoneInfo("Asia/Tokyo")
    now = datetime(2025, 11, 20, 10, 0, 0, tzinfo=tz)

    # Target date: yesterday
    target_date = now - timedelta(days=1)
    start_dt = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Mock activities
    activities = [
        _make_activity(start_dt + timedelta(hours=10), "Morning note"),
        _make_activity(start_dt + timedelta(hours=15), "Afternoon note"),
    ]
    mock_activity_repo.get_activities.return_value = activities

    # Initialize Service
    settings = SelfObserverSettings(timezone="Asia/Tokyo")
    service = SelfObserverService(mock_report_service, mock_activity_repo, settings)

    # Execute
    service.observe(target_date)

    # Verify get_activities called with correct range
    mock_activity_repo.get_activities.assert_called_once_with(start_dt, end_dt)

    # Verify save_report called
    mock_report_service.save_report.assert_called_once()
    saved_report: Report = mock_report_service.save_report.call_args[0][0]

    # Check report content
    assert saved_report.meta.type == ReportType.META
    assert saved_report.meta.author == ReportAuthor.SELF_OBSERVER
    assert "daily-report" in saved_report.meta.tags
    assert f"Daily Report: {start_dt.strftime('%Y-%m-%d')}" == saved_report.meta.title

    # Check body content
    body = saved_report.body_markdown
    assert "Morning note" in body
    assert "Afternoon note" in body
    assert start_dt.strftime("%Y-%m-%d") in body


def test_observe_no_activities(mocker: MockerFixture) -> None:
    """活動がない場合でもレポートが作成されることを検証する."""
    mock_report_service = mocker.Mock()
    mock_activity_repo = mocker.Mock()
    mock_activity_repo.get_activities.return_value = []

    settings = SelfObserverSettings(timezone="Asia/Tokyo")
    service = SelfObserverService(mock_report_service, mock_activity_repo, settings)

    target_date = datetime(2025, 11, 19, tzinfo=ZoneInfo("Asia/Tokyo"))
    service.observe(target_date)

    mock_report_service.save_report.assert_called_once()
    saved_report = mock_report_service.save_report.call_args[0][0]
    assert "活動記録はありませんでした" in saved_report.body_markdown
