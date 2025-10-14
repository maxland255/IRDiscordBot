import logging

from typing import TYPE_CHECKING, Literal
from datetime import datetime, UTC

from discord import TextChannel, Member, Color

from bot.utils.get_guild import get_guild
from bot.utils.get_channel import get_channel
from .embeds import format_infraction_embed, generic_embed
from bot.database.schemas import InfractionsSchema, LogEntryCreate, LogEntryType

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class ModerationLogger:
    def __init__(self, bot: "IRBot"):
        self.bot = bot

    async def _get_log_channel(self, guild_id: int) -> TextChannel | None:
        guild_config = await self.bot.db_guilds.get_guild_by_id(guild_id)

        if guild_config is None:
            return None

        logs_channel_id = guild_config.logs_moderation

        if logs_channel_id is None:
            return None

        guild = await get_guild(self.bot, guild_id)

        if guild is None:
            logger.error(f"Error fetching guild {guild_id} for moderation logs.")
            return None

        logs_channel = await get_channel(guild, logs_channel_id)

        return logs_channel

    async def moderation_command(self, infraction: InfractionsSchema, member: Member, moderator: Member):
        try:
            new_log_entry = LogEntryCreate(
                guild_id=infraction.guild_id,
                log_type=infraction.infraction_result.to_log_entry_type(),
                actor_id=moderator.id,
                target_id=member.id,
                details={
                    "infraction": infraction.model_dump_json(indent=None),
                },
                created_at=datetime.now(UTC),
            )

            logs_channel = await self._get_log_channel(infraction.guild_id)

            if logs_channel is not None:
                embed_log = await format_infraction_embed(infraction, member, moderator)

                await logs_channel.send(embed=embed_log)

            await self.bot.db_logs_entries.create_log_entry(new_log_entry)
        except Exception as e:
            logger.error(
                f"Error when creating the logs entry for infraction with id: {infraction.id}\nInfraction: {infraction.model_dump_json()}\nMember: {member.id}\nModerator: {moderator.id}\nError: {e}",
                exc_info=True
            )

    async def moderation_command_failed(
            self,
            guild_id: int,
            member: Member,
            target_member: Member,
            action: Literal["kick", "ban", "unban", "timeout", "warn"],
            reason: str,
            failed_reason: Literal["missing_permissions", "hierarchy", "code_error", "unknown"] = "unknown",
            error: str | None = None,
    ):
        try:
            log_entry_type = {
                "kick": LogEntryType.infraction_kick,
                "ban": LogEntryType.infraction_ban,
                "unban": LogEntryType.unknown,
                "timeout": LogEntryType.infraction_timeout,
                "warn": LogEntryType.infraction_warn,
            }.get(action, LogEntryType.unknown)

            new_log_entry = LogEntryCreate(
                guild_id=guild_id,
                log_type=log_entry_type,
                actor_id=member.id,
                target_id=target_member.id,
                details={
                    "reason": reason,
                    "action": action,
                    "failed_reason": failed_reason,
                    "error": error,
                },
                created_at=datetime.now(UTC),
            )

            logs_channel = await self._get_log_channel(guild_id)

            if logs_channel is not None:
                embed_log = await generic_embed(
                    title="Moderation Action Failed",
                    description=f"A moderation action could not be completed due to the following reason: ***{failed_reason}***.",
                    color=Color.dark_red(),
                    member=member.mention,
                    target_member=target_member.mention,
                    action=action,
                    reason=reason,
                    failed_reason=failed_reason,
                    error=error,
                )

                await logs_channel.send(embed=embed_log)

            await self.bot.db_logs_entries.create_log_entry(new_log_entry)
        except Exception as e:
            logger.error(
                f"Error when creating the logs entry for failed moderation action: {action} on member {target_member.id} by {member.id} in guild {guild_id}\nReason: {reason}\nFailed reason: {failed_reason}\nError: {e}",
                exc_info=True
            )
