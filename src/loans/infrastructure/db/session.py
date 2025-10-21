"""Async SQLAlchemy session management."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import AsyncIterator

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


@lru_cache
def get_database_url() -> str:
    """Return the configured database URL, defaulting to asyncpg for PostgreSQL."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://loans:loans@postgres:5432/loans",
    )


class Base(DeclarativeBase):
    """Base class for declarative ORM models."""


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return a singleton async engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_database_url(), echo=False, future=True)
    return _engine


def create_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (and cache) an async session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
        )
    return _session_factory


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope around a series of operations."""
    session = create_session_factory()()
    try:
        yield session
        await session.commit()
    except Exception:  # pragma: no cover - defensive rollback
        await session.rollback()
        raise
    finally:
        await session.close()


async def initialize_database() -> None:
    """Create database schema if it does not yet exist."""
    # Import models so that metadata is populated prior to create_all.
    from . import models  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
