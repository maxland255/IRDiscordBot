import logging

from typing import TYPE_CHECKING

from discord import TextChannel

from bot.utils.get_channel import get_channel
from bot.utils.get_guild import get_guild

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class ModerationLogger:
    def __init__(self, bot: "IRBot"):
        self.bot = bot

    async def _get_log_channel(self, guild_id: int) -> TextChannel | None:
        logs_channel_id = await self.bot.db_guilds.get_guild_by_id(guild_id)

        if logs_channel_id is None:
            return None

        guild = await get_guild(self.bot, guild_id)

        if guild is None:
            logger.error(f"Error fetching guild {guild_id} for moderation logs.")
            return None

        logs_channel = await get_channel(guild, logs_channel_id)
        
        return logs_channel
