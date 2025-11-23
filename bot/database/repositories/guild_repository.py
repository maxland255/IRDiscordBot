from typing import Protocol, Union
from abc import abstractmethod
from datetime import datetime, UTC

from bot.database.schemas import GuildSchema, GuildUpdate
from bot.database.models import Guild as GuildModel
from bot.exception import GuildNotFound

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker


class GuildRepository(Protocol):
    """
    Declare all methods used by the bot to interact with the database.
    The data could be from a database or an api.
    """

    @abstractmethod
    async def get_all_guilds(self) -> list[GuildSchema]:
        """
        Get all guilds.
        :return:
        """
        ...

    @abstractmethod
    async def get_guild_by_id(self, guild_id: int, raise_if_not_found: bool = False) -> Union[GuildSchema, None]:
        """
        Get a guild by its id.
        :param guild_id:
        :param raise_if_not_found: Get the guild or raise an exception if not found.
        :return:
        """
        ...

    @abstractmethod
    async def create_guild(self, guild: GuildSchema) -> GuildSchema:
        """
        Create a guild.
        :param guild:
        :return:
        """
        ...

    @abstractmethod
    async def update_guild(self, guild: GuildUpdate) -> GuildSchema:
        """
        Update a guild data.
        :param guild:
        :return:
        """
        ...

    @abstractmethod
    async def remove_guild(self, guild: GuildSchema) -> None:
        """
        Remove a guild.
        :param guild:
        :return:
        """
        ...


class SQLAlchemyGuildRepository(GuildRepository):
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def get_all_guilds(self) -> list[GuildSchema]:
        async with self.session_factory() as session:
            result = await session.execute(select(GuildModel))

            db_guilds = result.scalars().all()

            return [GuildSchema.model_validate(db_guild) for db_guild in db_guilds]

    async def get_guild_by_id(self, guild_id: int, raise_if_not_found: bool = False) -> Union[GuildSchema, None]:
        async with self.session_factory() as session:
            result = await session.execute(select(GuildModel).where(GuildModel.id == guild_id))

            db_guild = result.scalar_one_or_none()

            if db_guild is None:
                if raise_if_not_found:
                    raise GuildNotFound(guild_id)
                else:
                    return None

            return GuildSchema.model_validate(db_guild)

    async def create_guild(self, guild: GuildSchema) -> GuildSchema:
        async with self.session_factory() as session:
            new_db_user = GuildModel(**guild.model_dump())

            session.add(new_db_user)
            await session.commit()
            await session.refresh(new_db_user)

            return GuildSchema.model_validate(new_db_user)

    async def update_guild(self, guild: GuildUpdate) -> GuildSchema:
        async with self.session_factory() as session:
            db_guild = await session.get(GuildModel, guild.id)

            if db_guild is None or db_guild.deleted_at is not None:
                raise GuildNotFound(guild)

            update_data = guild.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_guild, key, value)

            session.add(db_guild)
            await session.commit()
            await session.refresh(db_guild)

            return GuildSchema.model_validate(db_guild)

    async def remove_guild(self, guild: GuildSchema) -> None:
        async with self.session_factory() as session:
            db_guild = await session.get(GuildModel, guild.id)

            if db_guild is None or db_guild.deleted_at is not None:
                raise GuildNotFound(guild)

            db_guild.deleted_at = datetime.now(UTC)

            session.add(db_guild)
            await session.commit()
