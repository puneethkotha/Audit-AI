"""Async database session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.db import Base

# Import models to register them
from models.db import AuditResult, ClinicalNote, ComplianceRule  # noqa: F401

from core.config import settings


def _ensure_asyncpg_url(url: str) -> str:
    """Convert postgres:// to postgresql+asyncpg:// and fix SSL for Neon."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "sslmode=require" in url and "ssl=require" not in url:
        url = url.replace("sslmode=require", "ssl=require")
    return url


_db_url = _ensure_asyncpg_url(settings.database_url)

engine = create_async_engine(
    _db_url,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
