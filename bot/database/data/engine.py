from bot.core.config import get_settings

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine

_settings = get_settings()

engine: AsyncEngine | None = None

AsyncSession: async_sessionmaker['AsyncSession'] | None = None


async def init_db() -> tuple[AsyncEngine, async_sessionmaker['AsyncSession']]:
    global engine, AsyncSession

    engine = create_async_engine(_settings.DATABASE_URL, echo=_settings.ENV == "dev")

    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

    return engine, AsyncSession
