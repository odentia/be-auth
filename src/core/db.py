from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator

from sqlalchemy import event, select, text
from sqlalchemy.engine import URL as SAURL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


async def init_engine(url: str | SAURL, echo: bool = False) -> AsyncEngine:

    global _engine

    if _engine is not None:
        return _engine
    engine = create_async_engine(url, echo=echo, pool_pre_ping=True)
    _install_sqlite_pragmas_if_needed(engine)

    _engine = engine
    return engine


def init_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:

    global _session_factory

    if _session_factory is not None:
        return _session_factory

    _session_factory = async_sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return _session_factory


def get_engine() -> AsyncEngine | None:
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    return _session_factory


async def close_engine(engine: AsyncEngine | None = None) -> None:

    global _engine

    eng = engine or _engine
    if eng is not None:
        await eng.dispose()
    if engine is None:
        _engine = None


async def db_healthcheck(session_factory: async_sessionmaker[AsyncSession]) -> bool:

    async with session_factory() as session:
        try:
            scalar = await session.scalar(text("SELECT 1"))
            return scalar == 1
        except Exception:
            return False


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> AsyncIterator[AsyncSession]:
    sf = session_factory or _session_factory
    if sf is None:
        raise RuntimeError("Session factory is not initialized")
    async with sf() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _install_sqlite_pragmas_if_needed(engine: AsyncEngine) -> None:
    if not str(engine.url).startswith("sqlite+"):
        return

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()