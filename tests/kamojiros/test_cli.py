"""CLI コマンドのテスト."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from kamojiros.main import app

if TYPE_CHECKING:
    import pytest

runner = CliRunner()


def test_help_command() -> None:
    """ヘルプコマンドが正常に動作することを確認."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Kamojiros" in result.stdout
    assert "create" in result.stdout
    assert "list" in result.stdout
    assert "search" in result.stdout
    assert "stats" in result.stdout


def test_create_help() -> None:
    """Create コマンドのヘルプが表示されることを確認."""
    result = runner.invoke(app, ["create", "--help"])
    assert result.exit_code == 0
    assert "Create a new report" in result.stdout
    assert "--title" in result.stdout
    assert "--type" in result.stdout


def test_list_help() -> None:
    """List コマンドのヘルプが表示されることを確認."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0
    assert "List reports" in result.stdout
    assert "--limit" in result.stdout


def test_search_help() -> None:
    """Search コマンドのヘルプが表示されることを確認."""
    result = runner.invoke(app, ["search", "--help"])
    assert result.exit_code == 0
    assert "Search reports" in result.stdout


def test_stats_help() -> None:
    """Stats コマンドのヘルプが表示されることを確認."""
    result = runner.invoke(app, ["stats", "--help"])
    assert result.exit_code == 0
    assert "Show statistics" in result.stdout


def test_create_command_non_interactive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Create コマンドが非インタラクティブモードで動作することを確認."""
    # 環境変数でnotes_repo_rootを一時ディレクトリに設定
    monkeypatch.setenv("KAMOJIROS_NOTES__REPO_ROOT", str(tmp_path))

    result = runner.invoke(
        app,
        [
            "create",
            "-I",  # non-interactive
            "--title",
            "Test Report",
            "--type",
            "tech",
            "--tags",
            "test",
            "--body",
            "# Test\n\nThis is a test.",
        ],
    )

    assert result.exit_code == 0
    assert "Report created" in result.stdout

    # レポートファイルが作成されたことを確認
    journal_dir = tmp_path / "docs" / "journal"
    assert journal_dir.exists()


def test_list_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """List コマンドが動作することを確認."""
    monkeypatch.setenv("KAMOJIROS_NOTES__REPO_ROOT", str(tmp_path))

    # まずレポートを作成
    runner.invoke(
        app,
        [
            "create",
            "-I",
            "--title",
            "Test Report",
            "--type",
            "tech",
            "--body",
            "Test body",
        ],
    )

    # list コマンド実行
    result = runner.invoke(app, ["list", "--limit", "5"])

    assert result.exit_code == 0
    assert "Reports" in result.stdout or "Test Report" in result.stdout


def test_search_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Search コマンドが動作することを確認."""
    monkeypatch.setenv("KAMOJIROS_NOTES__REPO_ROOT", str(tmp_path))

    # レポートを作成
    runner.invoke(
        app,
        [
            "create",
            "-I",
            "--title",
            "Searchable Report",
            "--type",
            "tech",
            "--body",
            "This contains a unique keyword: FINDME",
        ],
    )

    # search コマンド実行
    result = runner.invoke(app, ["search", "FINDME"])

    assert result.exit_code == 0
    assert "FINDME" in result.stdout or "Searchable Report" in result.stdout


def test_stats_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Stats コマンドが動作することを確認."""
    monkeypatch.setenv("KAMOJIROS_NOTES__REPO_ROOT", str(tmp_path))

    # レポートを作成
    runner.invoke(
        app,
        [
            "create",
            "-I",
            "--title",
            "Stats Test",
            "--type",
            "tech",
            "--body",
            "Test",
        ],
    )

    # stats コマンド実行
    result = runner.invoke(app, ["stats"])

    assert result.exit_code == 0
    assert "Statistics" in result.stdout
    assert "Total Reports" in result.stdout


def test_create_missing_required_args() -> None:
    """必須引数が不足している場合にエラーになることを確認."""
    result = runner.invoke(
        app,
        [
            "create",
            "-I",
            "--title",
            "Test",
            # --type と --body が不足
        ],
    )

    assert result.exit_code == 1
    assert "required" in result.stdout.lower() or "error" in result.stdout.lower()


def test_list_with_json_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """List コマンドのJSON出力が動作することを確認."""
    monkeypatch.setenv("KAMOJIROS_NOTES__REPO_ROOT", str(tmp_path))

    # レポートを作成
    runner.invoke(
        app,
        [
            "create",
            "-I",
            "--title",
            "JSON Test",
            "--type",
            "tech",
            "--body",
            "Test",
        ],
    )

    # JSON形式でlist
    result = runner.invoke(app, ["list", "--json", "--limit", "1"])

    assert result.exit_code == 0
    # JSON形式の出力を確認（簡易チェック）
    assert "{" in result.stdout or "note_id" in result.stdout
