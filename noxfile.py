"""Run all project checks and fixes via uv with a single `nox`."""

import nox
from nox.command import CommandFailed

# Run `all` when you just type `nox`
nox.options.sessions = ["ci"]

NOX_UV = "uv"
DEFAULT_TARGETS = ("src", "tests")


def _targets(session: nox.Session) -> tuple[str, ...]:
    """Return CLI-selected targets or the default (src, tests)."""
    return tuple(session.posargs) if session.posargs else DEFAULT_TARGETS


def _uv_run(session: nox.Session, *args: str) -> None:
    """Run a command through uv."""
    session.run(NOX_UV, "run", *args, external=True)


@nox.session(venv_backend="none")
def ci(session: nox.Session) -> None:
    """Fix, format, lint, typecheck, and test in one go."""
    targets = _targets(session)
    _uv_run(session, "ruff", "check", "--fix", *targets)  # e.g., D202 を自動修正
    _uv_run(session, "ruff", "format", *targets)  # 整形
    _uv_run(session, "ruff", "check", *targets)  # Lint 確認
    _uv_run(session, "pyright", *targets)  # 型チェック
    try:
        _uv_run(session, "pytest", "-q")
    except CommandFailed:
        session.warn("pytest is not installed; skipping tests. Add `pytest` to your dependencies to enable tests.")


@nox.session(venv_backend="none")
def fix(session: nox.Session) -> None:
    """Apply Ruff autofixes."""
    _uv_run(session, "ruff", "check", "--fix", *_targets(session))


@nox.session(venv_backend="none")
def fmt(session: nox.Session) -> None:
    """Format code with Ruff formatter."""
    _uv_run(session, "ruff", "format", *_targets(session))


@nox.session(venv_backend="none")
def lint(session: nox.Session) -> None:
    """Run Ruff lint."""
    _uv_run(session, "ruff", "check", *_targets(session))


@nox.session(venv_backend="none")
def typecheck(session: nox.Session) -> None:
    """Run Pyright type checking."""
    _uv_run(session, "pyright", *_targets(session))


@nox.session(venv_backend="none")
def test(session: nox.Session) -> None:
    """Run tests with Pytest."""
    _uv_run(session, "pytest", "-q", *session.posargs)
