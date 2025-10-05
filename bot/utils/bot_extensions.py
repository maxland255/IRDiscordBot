from typing import Union

from discord import Role, Bot, Guild


async def get_bot_top_role(bot: Bot, guild: Guild) -> Union[Role, None]:
    """
    Get the bot top role in a guild.
    :param bot:
    :param guild:
    :return:
    """

    bot_member = guild.get_member(bot.user.id)

    if bot_member is None:
        bot_member = await guild.fetch_member(bot.user.id)

    if bot_member is None:
        return None

    return bot_member.top_role
