from typing import Protocol
from abc import abstractmethod

from bot.database.schemas import Guild

from sqlalchemy.ext.asyncio import async_sessionmaker


class GuildRepository(Protocol):
    """
    Declare all methods used by the bot to interact with the database.
    The data could be from a database or an api.
    """

    @abstractmethod
    async def get_guild_by_id(self, guild_id: int) -> Guild:
        """
        Get a guild by its id.
        :param guild_id:
        :return:
        """
        ...

    @abstractmethod
    async def create_guild(self, guild: Guild) -> Guild:
        """
        Create a guild.
        :param guild:
        :return:
        """
        ...

    @abstractmethod
    async def update_guild(self, guild: Guild) -> Guild:
        """
        Update a guild data.
        :param guild:
        :return:
        """
        ...

    @abstractmethod
    async def remove_guild(self, guild: Guild) -> None:
        """
        Remove a guild.
        :param guild:
        :return:
        """
        ...


class SQLAlchemyGuildRepository:
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory
