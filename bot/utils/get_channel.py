from discord import Guild, VoiceChannel, StageChannel, TextChannel, ForumChannel, CategoryChannel, Thread

from typing import Union


async def get_channel(guild: Guild, channel_id: int | None) -> Union[
    VoiceChannel, StageChannel, TextChannel, ForumChannel, CategoryChannel, Thread, None]:
    if channel_id is None:
        return None
    
    channel = guild.get_channel(channel_id)

    if channel is not None:
        return channel

    return await guild.fetch_channel(channel_id)
