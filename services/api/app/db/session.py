"""
Database Session Configuration
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Engine kwargs - SQLite doesn't support pool_size/max_overflow
_engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
}
if "sqlite" not in settings.DATABASE_URL:
    _engine_kwargs.update(pool_pre_ping=True, pool_size=5, max_overflow=10)

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

