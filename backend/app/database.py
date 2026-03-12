from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# --- Own database (read/write) ---
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# --- WSK Hub database (read-only) ---
wskhub_engine = create_async_engine(
    settings.WSKHUB_DATABASE_URL,
    pool_size=5,
    max_overflow=2,
)

wskhub_async_session = async_sessionmaker(
    wskhub_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency yielding own DB session with commit/rollback."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_wskhub_db():
    """FastAPI dependency yielding WSK Hub read-only session."""
    async with wskhub_async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables in own database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_engines():
    """Cleanup both engines on shutdown."""
    await engine.dispose()
    await wskhub_engine.dispose()
