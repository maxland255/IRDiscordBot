from typing import Union

from discord import Member, Guild


async def get_member(guild: Guild, member_id: int) -> Union[Member, None]:
    """
    Get a member from bot cache or fetch from API if not found in cache.
    :param guild:
    :param member_id:
    :return:
    """

    member = guild.get_member(member_id)

    if member is None:
        member = await guild.fetch_member(member_id)

    return member
