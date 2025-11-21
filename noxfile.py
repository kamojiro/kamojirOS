"""Run all project checks and fixes via Nox + uv."""

from __future__ import annotations

import nox
from nox import Session, options
from nox.command import CommandFailed
from nox_uv import session  # uv sync ベースの @session デコレータ

# すべてのセッションで uv をバックエンドに使う
options.default_venv_backend = "uv"

# デフォルトで走らせるセッション
nox.options.sessions = ["ci"]

PYTHON_VERSIONS = ["3.14"]
DEFAULT_TARGETS: tuple[str, ...] = ("src", "tests")

# Node / cspell 関連
NODE_VERSION = "24.5.0"
CSPELL_TARGETS: tuple[str, ...] = (".",)  # 対象は cspell.json 側で細かく制御する前提


def _targets(session: Session) -> tuple[str, ...]:
    """Return CLI-selected targets or the default (src, tests)."""
    return tuple(session.posargs) if session.posargs else DEFAULT_TARGETS


@session(
    venv_backend="uv",
    python=PYTHON_VERSIONS,
    uv_groups=["dev"],  # dev グループを uv sync でインストール
    tags=["ci"],
)
def ci(session: Session) -> None:
    """Fix, format, lint, typecheck, and test in one go."""
    targets = _targets(session)

    # Ruff: autofix -> format -> lint
    session.run("ruff", "check", "--fix", *targets)
    session.run("ruff", "format", *targets)
    session.run("ruff", "check", *targets)

    # Pyright
    session.run("pyright", *targets)

    # Pytest
    try:
        session.run("pytest", "-q")
    except CommandFailed:
        session.warn(
            "pytest is not installed; add it to the `dev` dependency group "
            "to enable tests."
        )


@session(
    venv_backend="uv",
    python=PYTHON_VERSIONS,
    uv_groups=["dev"],
    tags=["format"],
)
def fix(session: Session) -> None:
    """Apply Ruff autofixes."""
    session.run("ruff", "check", "--fix", *_targets(session))


@session(
    venv_backend="uv",
    python=PYTHON_VERSIONS,
    uv_groups=["dev"],
    tags=["format"],
)
def fmt(session: Session) -> None:
    """Format code with Ruff formatter."""
    session.run("ruff", "format", *_targets(session))


@session(
    venv_backend="uv",
    python=PYTHON_VERSIONS,
    uv_groups=["dev"],
    tags=["lint"],
)
def lint(session: Session) -> None:
    """Run Ruff lint."""
    session.run("ruff", "check", *_targets(session))


@session(
    venv_backend="uv",
    python=PYTHON_VERSIONS,
    uv_groups=["dev"],
    tags=["typecheck"],
)
def typecheck(session: Session) -> None:
    """Run Pyright type checking."""
    session.run("pyright", *_targets(session))


@session(
    venv_backend="uv",
    python=PYTHON_VERSIONS,
    uv_groups=["dev"],
    tags=["test"],
)
def test(session: Session) -> None:
    """Run tests with Pytest."""
    session.run("pytest", "-q", *session.posargs)


@session(
    venv_backend="uv",
    python=PYTHON_VERSIONS,
    uv_groups=["dev"],  # dev グループに nodeenv が含まれている想定
    tags=["spell", "ci"],
)
def spell_check(session: Session) -> None:
    """Run cspell via nodeenv + npx inside the uv-managed venv."""
    # 1. このセッションの venv (.nox/spell_check-3-14/...) に Node を結合
    session.run(
        "nodeenv",
        "-p",  # --python-virtualenv: 現在の venv に Node を組み込む
        "--prebuilt",
        f"--node={NODE_VERSION}",
    )

    # 2. venv 内に入った npx + cspell を実行
    #
    #    - cspell 自体は package.json / node_modules 側で管理
    #    - どのファイルを見るか / ignore は cspell.json 側で調整
    #
    session.run("npx", "cspell", *CSPELL_TARGETS)
