from bot.core.config import get_settings

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

_settings = get_settings()

engine = create_async_engine(_settings.DATABASE_URL, echo=_settings.ENV == "dev")

AsyncSession = async_sessionmaker(engine, expire_on_commit=False)
