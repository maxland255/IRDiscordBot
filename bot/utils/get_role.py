from typing import Union

from discord import Role, Guild, HTTPException


async def get_role(guild: Guild, role_id: int) -> Union[Role, None]:
    """
    Get a role from bot cache or fetch from API if not found in cache.
    :param guild:
    :param role_id:
    :return:
    """

    role = guild.get_role(role_id)

    if role is None:
        try:
            role = await guild.fetch_role(role_id)
        except HTTPException:
            role = None

    return role
