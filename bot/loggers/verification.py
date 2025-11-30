import logging

from typing import TYPE_CHECKING
from datetime import datetime, UTC

from discord import TextChannel, Member, Color, Guild

from bot.utils.get_guild import get_guild
from bot.utils.get_channel import get_channel
from .embeds import generic_embed
from bot.database.schemas import VerificationsSchema, VerificationStatus, LogEntryCreate, LogEntryType

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class VerificationLogger:
    def __init__(self, bot: "IRBot"):
        self.bot = bot

    async def _get_log_channel(self, guild_id: int) -> TextChannel | None:
        guild_config = await self.bot.db_guilds.get_guild_by_id(guild_id)

        if guild_config is None:
            return None

        logs_channel_id = guild_config.logs_server

        if logs_channel_id is None:
            return None

        guild = await get_guild(self.bot, guild_id)

        if guild is None:
            logger.error(f"Error fetching guild {guild_id} for moderation logs.")
            return None

        logs_channel = await get_channel(guild, logs_channel_id)

        return logs_channel

    async def success_manual_verification(self, guild: Guild, member: Member, moderator: Member,
                                          verification: VerificationsSchema, new_status: VerificationStatus,
                                          reason: str):
        try:
            new_log_entry = LogEntryCreate(
                guild_id=guild.id,
                log_type=LogEntryType.verification_manual,
                actor_id=moderator.id,
                target_id=member.id,
                details={
                    "verification": verification.model_dump_json(indent=None),
                    "reason": reason,
                },
                created_at=datetime.now(UTC),
            )

            logs_channel = await self._get_log_channel(guild.id)

            if logs_channel is not None:
                embed_log = await generic_embed(
                    title="Verification Manual",
                    description=f"Member {member.mention} has been manually verified by {moderator.mention}.",
                    color=Color.green(),
                    member=member.mention,
                    moderator=moderator.mention,
                    reason=reason,
                    verification_status=new_status.name,
                )

                await logs_channel.send(embed=embed_log)

            await self.bot.db_logs_entries.create_log_entry(new_log_entry)
        except Exception as e:
            logger.error(f"Error logging manual verification for member {member.id} in guild {guild.id}", exc_info=e)
