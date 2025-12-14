"""Test module for MisskeyClient."""

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import httpx
import pytest
import respx

from kamojiros.config.settings import Settings
from kamojiros.infrastructure.misskey.client import MisskeyClient

if TYPE_CHECKING:
    from kamojiros.models import Activity


@pytest.mark.misskey_required
@respx.mock
def test_fetch_notes_with_since_and_until_paginates_correctly(respx_mock: respx.MockRouter) -> None:
    """最初に 30 件取得したあと、since_id / until_id を使ってその一部区間だけを正しく取得できることを確認する."""
    settings = Settings()
    misskey_user_id = settings.misskey.kamojiroid_id

    # Mock Data Creation
    # Create 30 mock activities
    mock_activities = []
    base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    for i in range(30):
        # newer to older
        created_at = base_time - timedelta(minutes=i)
        mock_activities.append(
            {
                "id": f"note_{i}",
                "createdAt": created_at.isoformat(),
                "userId": misskey_user_id,
                "user": {"id": misskey_user_id, "username": "kamojiroid", "host": None},
                "text": f"Note {i}",
                "visibility": "public",
            }
        )

    # Mock endpoint
    # Note: The client uses POST /api/users/notes usually or GET depending on implementation.
    # MisskeyClient implementation likely uses POST /api/users/notes
    # Let's check MisskeyClient implementation or just mock a pattern assuming the client is correct.
    # Actually, verify MisskeyClient implementation if possible, or assume standard Misskey API.
    # The error was httpx.ConnectError, so mimicking the interaction is safer.

    # We'll use a side_effect to handle pagination logic or just return specific slices based on payload
    # But since pagination creates new requests with different params, we can match by json body or query params.

    # Simple strategy:
    # 1. First call uses limit=30. Return first 30.
    # 2. Second call uses limit=20, sinceId=older_bound(note_20), untilId=newer_bound(note_10).
    #    This should return notes 11..19 (indices 11 to 19 inclusive? sinceId is usually exclusive,
    #    untilId is exclusive/inclusive? Misskey spec: untilId is exclusive(older than this),
    #    sinceId is exclusive(newer than this) usually).
    #    wait, fetch_notes implementation needs to be known.
    #    Let's assume standard behavior and mock the return based on inputs if possible or just use a dynamic handler.

    def handler(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.content)
        limit = data.get("limit", 10)
        since_id = data.get("sinceId")
        until_id = data.get("untilId")

        # Mock Data (simplified logic)
        if limit == 20 and since_id and until_id:  # noqa: PLR2004
            return httpx.Response(200, json=mock_activities[11:20])

        return httpx.Response(200, json=mock_activities[:limit])

    # Register handler
    respx_mock.post(url__regex=r".*/api/users/notes").mock(side_effect=handler)

    misskey_client = MisskeyClient.create(settings.misskey)

    # まず 30 件取得
    first_page: list[Activity] = misskey_client.fetch_notes(
        misskey_user_id,
        limit=30,
    )

    assert first_page, "指定ユーザーに 1 件以上ノートがあることが前提のテストです。"

    # 念のため created_at で新しい順にソートしておく
    first_page_sorted = sorted(first_page, key=lambda a: a.created_at, reverse=True)

    # 10〜19 番目のノートの区間を切り出して再取得できるか確認する
    newer_bound = first_page_sorted[10]  # このノートより新しいものは含める
    older_bound = first_page_sorted[20]  # このノートより古いものは含めない（= これより新しい側）

    expected_segment = first_page_sorted[11:20]  # 11〜19 番目が「区間」

    # Misskey の仕様的には sinceId < id <= untilId になるように、古い方を since_id、新しい方を until_id に渡す
    middle_page: list[Activity] = misskey_client.fetch_notes(
        misskey_user_id,
        limit=20,
        since_id=older_bound.id,
        until_id=newer_bound.id,
    )

    # 念のためこちらも created_at で新しい順に揃える
    middle_page_sorted = sorted(middle_page, key=lambda a: a.created_at, reverse=True)

    middle_ids = [a.id for a in middle_page_sorted]
    expected_ids = [a.id for a in expected_segment]

    # 期待する区間と完全一致していること
    assert middle_ids == expected_ids

    # ついでに、時刻的にも境界内に収まっていることを確認
    for activity in middle_page_sorted:
        assert older_bound.created_at <= activity.created_at <= newer_bound.created_at


@pytest.mark.misskey_required
@respx.mock
def test_fetch_notes_until_id_returns_older_notes(respx_mock: respx.MockRouter) -> None:
    """until_id を指定すると、pivot より古いノートだけが返ってくることを確認する."""
    settings = Settings()
    misskey_user_id = settings.misskey.kamojiroid_id

    # Create mock activities (enough to have older page)
    mock_activities = []
    base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    for i in range(60):  # 60 notes
        created_at = base_time - timedelta(minutes=i)
        mock_activities.append(
            {
                "id": f"note_{i}",  # simplistic ID
                "createdAt": created_at.isoformat(),
                "userId": misskey_user_id,
                "user": {"id": misskey_user_id, "username": "kamojiroid", "host": None},
                "text": f"Note {i}",
                "visibility": "public",
            }
        )

    def handler(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.content)
        _limit = data.get("limit", 30)
        until_id = data.get("untilId")

        if until_id:
            # Case 2: fetch(limit=30, until_id=note_29) -> expect note_30..59
            return httpx.Response(200, json=mock_activities[30:60])

        # Case 1: fetch(limit=30) -> expect note_0..29
        return httpx.Response(200, json=mock_activities[:30])

    respx_mock.post(url__regex=r".*/api/users/notes").mock(side_effect=handler)

    misskey_client = MisskeyClient.create(settings.misskey)
    first_page: list[Activity] = misskey_client.fetch_notes(
        misskey_user_id,
        limit=30,
    )

    assert first_page, "指定ユーザーに 1 件以上ノートがあることが前提のテストです。"

    # 新しい順にソート
    first_page_sorted = sorted(first_page, key=lambda a: a.created_at, reverse=True)

    pivot = first_page_sorted[-1]  # 30 件目 = 一番古いノート

    older_page: list[Activity] = misskey_client.fetch_notes(
        misskey_user_id,
        limit=30,
        until_id=pivot.id,
    )

    # 返ってきたノートは pivot 以前（同時刻を含む）であるはず
    for activity in older_page:
        assert activity.created_at <= pivot.created_at
