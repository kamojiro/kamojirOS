"""Test module for MisskeyClient."""

from typing import TYPE_CHECKING

import pytest

from kamojiros.config.settings import Settings
from kamojiros.infrastructure.misskey.client import MisskeyClient

if TYPE_CHECKING:
    from kamojiros.models import Activity


@pytest.mark.misskey_required
def test_fetch_notes_with_since_and_until_paginates_correctly() -> None:
    """最初に 30 件取得したあと、since_id / until_id を使ってその一部区間だけを正しく取得できることを確認する."""
    settings = Settings()
    misskey_client = MisskeyClient.create(settings.misskey)
    misskey_user_id = settings.misskey.kamojiroid_id

    # まず 30 件取得
    first_page: list[Activity] = misskey_client.fetch_notes(
        misskey_user_id,
        limit=30,
    )

    assert first_page, "指定ユーザーに 1 件以上ノートがあることが前提のテストです。"

    # 中間区間を取りたいので、ある程度ノートが必要
    if len(first_page) < 25:  # noqa: PLR2004
        pytest.skip("ノート数が少なすぎてページング挙動を検証できないのでスキップします。")

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
def test_fetch_notes_until_id_returns_older_notes() -> None:
    """until_id を指定すると、pivot より古いノートだけが返ってくることを確認する."""
    settings = Settings()
    misskey_client = MisskeyClient.create(settings.misskey)
    misskey_user_id = settings.misskey.kamojiroid_id
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
