import logging

from typing import TYPE_CHECKING, Union

from discord import Guild

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


async def get_guild(bot: "IRBot", guild_id: int) -> Union[Guild, None]:
    try:
        guild = bot.get_guild(guild_id)

        if guild is None:
            guild = await bot.fetch_guild(guild_id)

        return guild
    except Exception as e:
        logger.error(f"Error fetching guild {guild_id}: {e}", exc_info=True)
        return None
