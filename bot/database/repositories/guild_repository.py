from typing import Protocol
from abc import abstractmethod

from bot.database.schemas import Guild


class DiscordServerRepository(Protocol):
    """
    Declare all methods used by the bot to interact with the database.
    The data could be from a database or an api.
    """

    @abstractmethod
    def get_discord_server_by_id(self, discord_server_id: int) -> DiscordServer:
        """
        Get a discord server by its id.
        :param discord_server_id:
        :return:
        """
        ...

    @abstractmethod
    def create_discord_server(self, discord_server: DiscordServer) -> DiscordServer:
        """
        Create a discord server.
        :param discord_server:
        :return:
        """
        ...

    @abstractmethod
    def update_discord_server(self, discord_server: DiscordServer) -> DiscordServer:
        """
        Update a discord server data.
        :param discord_server:
        :return:
        """
        ...

    @abstractmethod
    def remove_discord_server(self, discord_server: DiscordServer) -> None:
        """
        Remove a discord server.
        :param discord_server:
        :return:
        """
        ...
