from discord import Embed, Member
from datetime import datetime, UTC

from bot.database.schemas import InfractionsSchema, InfractionType


async def format_infraction_embed(infraction: InfractionsSchema, member: Member, moderator: Member) -> Embed:
    infraction_embed = Embed(
        title=f"Logs: {infraction.infraction_type.value}",
        description=f"{member.mention} has been {infraction.infraction_type.value} by {moderator.mention}.",
        colour=infraction.infraction_type.get_color(),
        timestamp=datetime.now(UTC),
    )

    infraction_embed.add_field(
        name="Infraction ID",
        value=str(infraction.id),
        inline=False,
    )

    infraction_embed.add_field(
        name="Reason",
        value=infraction.reason,
        inline=False,
    )

    infraction_embed.add_field(
        name="Member",
        value=f"{member.mention} ({member.id})",
        inline=False,
    )

    infraction_embed.add_field(
        name="Moderator",
        value=f"{moderator.mention} ({moderator.id})",
        inline=False,
    )

    if infraction.infraction_type == InfractionType.warn:
        infraction_embed.add_field(
            name="Infraction result",
            value=infraction.infraction_result.value,
            inline=False,
        )

    if infraction.infraction_type == InfractionType.timeout:
        infraction_embed.add_field(
            name="Gravity",
            value=f"{infraction.gravity.name} gravity level",
            inline=False,
        )

        infraction_embed.add_field(
            name="Timeout until",
            value=f"<t:{int(infraction.timeout_until.timestamp())}:R> | {infraction.timeout_until.strftime('%Y-%m-%d %H:%M:%S')}",
            inline=False,
        )

    return infraction_embed
