"""PostgreSQL Database Engine Helpers."""

from typing import TYPE_CHECKING

from langchain_postgres import PGEngine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

if TYPE_CHECKING:
    from kamojiros.config.settings import PostgreSQLSettings


def build_pg_dsn(pg: PostgreSQLSettings) -> str:
    """PostgreSQLSettings から SQLAlchemy 用 DSN を作る."""
    return f"postgresql+psycopg://{pg.user}:{pg.password}@{pg.host}:{pg.port}/{pg.database}"


def create_async_engine_from_settings(pg: PostgreSQLSettings) -> AsyncEngine:
    """PostgreSQLSettings から SQLAlchemy の AsyncEngine を作る."""
    dsn = build_pg_dsn(pg)
    return create_async_engine(dsn, future=True)


async def create_pg_engine(pg: PostgreSQLSettings) -> PGEngine:
    """PGEngine を作るヘルパー."""
    async_engine = create_async_engine_from_settings(pg)
    return PGEngine.from_engine(engine=async_engine)
