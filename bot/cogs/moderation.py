import logging

from datetime import datetime

from discord import Cog, ApplicationContext, SlashCommandGroup, Option, Member, Permissions, InteractionContextType, \
    AutocompleteContext, Embed, Guild

from typing import TYPE_CHECKING

from bot.database.schemas import GravityLevelSchema, InfractionsCreate, InfractionType, InfractionResult, \
    InfractionsSchema
from bot.utils.bot_extensions import get_bot_top_role
from bot.utils.get_member import get_member
from bot.utils.calculate_timeout import calculate_timeout_duration

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


async def get_gravity_levels(ctx: AutocompleteContext) -> list[str]:
    gravity_levels: list[GravityLevelSchema] = await ctx.bot.db_gravity_levels.get_all_gravity_level(
        ctx.interaction.guild.id)

    return [g.name for g in gravity_levels]


class Moderation(Cog):
    def __init__(self, bot: "IRBot"):
        self.bot = bot

    moderator = SlashCommandGroup(
        name="moderator",
        description="Moderation commands",
        default_member_permissions=Permissions(moderate_members=True),
        contexts={InteractionContextType.guild},
    )

    # Commands

    @moderator.command(
        name="warn",
        description="Warn a member in the server",
    )
    async def warn(
            self,
            ctx: ApplicationContext,
            member: Member = Option(
                Member,
                required=True,
            ),
            reason: str = Option(
                str,
                required=True,
            )
    ):
        try:
            await ctx.defer(ephemeral=True)

            result, message, infraction_detail = await self.warn_member(self.bot, ctx.guild, ctx.author, member, reason)

            if not result:
                await ctx.respond(message, ephemeral=True)
                return

            await ctx.respond(
                f"{member.mention} has been warned.",
                embed=await self.print_infractions_details(ctx.guild, infraction_detail, moderator_view=True),
            )
        except Exception as e:
            logger.error("An error occurred while deferring the warn command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the warn command", ephemeral=True)

    @moderator.command(
        name="timeout",
        description="Timeout a member in the server",
    )
    async def timeout(
            self,
            ctx: ApplicationContext,
            member: Member = Option(
                Member,
                required=True,
            ),
            gravity: str = Option(
                str,
                autocomplete=get_gravity_levels,
                required=True,
            ),
            reason: str = Option(
                str,
                required=True,
            )
    ):
        try:
            await ctx.defer(ephemeral=True)

            result, message, infraction_detail, timeout_until = await self.timeout_member(self.bot, ctx.guild,
                                                                                          ctx.author, member, gravity,
                                                                                          reason)

            if not result:
                await ctx.respond(message, ephemeral=True)
                return

            await ctx.respond(
                f"{member.mention} has been timed out until {timeout_until.strftime('%Y-%m-%d %H:%M:%S')}.",
                embed=await self.print_infractions_details(ctx.guild, infraction_detail, moderator_view=True)
            )
        except Exception as e:
            logger.error("An error occurred while running the timeout command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the timeout command", ephemeral=True)

    # Methode

    @staticmethod
    async def warn_member(bot: "IRBot", guild: Guild, author: Member, member: Member, reason: str) -> tuple[
        bool, str, InfractionsSchema | None]:
        guild_config = await bot.db_guilds.get_guild_by_id(guild.id)

        if guild_config is None:
            return False, "Guild configuration not found. Please contact the bot administrator.", None

        result = await Moderation.check_member_permissions(bot, guild, member)

        if not result[0]:
            await bot.logger.moderation.moderation_command_failed(
                guild.id,
                author,
                member,
                "warn",
                reason,
                failed_reason="hierarchy",
                error="I do not have permission to warn this member.",
            )
            return False, result[1], None

        new_infraction = InfractionsCreate(
            guild_id=guild.id,
            user_id=member.id,
            moderator_id=author.id,
            reason=reason,
            infraction_type=InfractionType.warn,
            gravity_id=None,
            infraction_result=InfractionResult.warn,
        )

        member_infractions = await bot.db_infractions.get_all_infractions_by_user(guild.id, member.id)

        timeout_duration = await calculate_timeout_duration(
            member_infractions,
            guild_config,
            weight=guild_config.warn_height,
        )

        if timeout_duration is not None:
            new_infraction.infraction_result = InfractionResult.timeout
            new_infraction.timeout_end = timeout_duration

            await member.timeout(timeout_duration, reason=reason)

        infraction_detail = await bot.db_infractions.create_infraction(new_infraction)

        member_infraction_view = await Moderation.print_infractions_details(guild, infraction_detail,
                                                                            moderator_view=False)

        await member.send(
            f"You have been warned in {guild.name}.",
            embed=member_infraction_view,
        )

        return True, "Member has been warned successfully.", infraction_detail

    @staticmethod
    async def timeout_member(bot: "IRBot", guild: Guild, author: Member, member: Member,
                             gravity_level: GravityLevelSchema | str, reason: str) -> tuple[
        bool, str, InfractionsSchema | None, datetime | None]:
        guild_config = await bot.db_guilds.get_guild_by_id(guild.id)

        if guild_config is None:
            return False, "Guild configuration not found. Please contact the bot administrator.", None, None

        result = await Moderation.check_member_permissions(bot, guild, member)

        if not result[0]:
            await bot.logger.moderation.moderation_command_failed(
                guild.id,
                author,
                member,
                "timeout",
                reason,
                failed_reason="hierarchy",
                error="I do not have permission to timeout this member.",
            )
            return False, result[1], None, None

        gravity_level = await bot.db_gravity_levels.get_gravity_level_by_name(gravity_level) if isinstance(
            gravity_level, str) else gravity_level

        if gravity_level is None:
            await bot.logger.moderation.moderation_command_failed(
                guild.id,
                author,
                member,
                "timeout",
                reason,
                failed_reason="code_error",
                error=f"Gravity level with name {gravity_level} not found.",
            )
            return False, f"Gravity level with name {gravity_level} not found.", None, None

        member_infractions = await bot.db_infractions.get_all_infractions_by_user(guild.id, member.id)

        timeout_until = await calculate_timeout_duration(member_infractions, guild_config,
                                                         gravity_level=gravity_level)

        if timeout_until is None:
            await bot.logger.moderation.moderation_command_failed(
                guild.id,
                author,
                member,
                "timeout",
                reason,
                failed_reason="code_error",
                error=f"An error occurred while calculating the timeout duration. (timeout_until is None)",
            )
            return False, "An error occurred while calculating the timeout duration.", None, None

        if member.timed_out:
            return False, f"{member.mention} is already timed out.", None, None

        await member.timeout(timeout_until, reason=reason)

        new_infraction = InfractionsCreate(
            guild_id=guild.id,
            user_id=member.id,
            moderator_id=author.id,
            reason=reason,
            infraction_type=InfractionType.timeout,
            gravity_id=gravity_level.id,
            timeout_end=timeout_until,
            infraction_result=InfractionResult.timeout,
        )

        infraction_detail = await bot.db_infractions.create_infraction(new_infraction)

        member_infraction_view = await Moderation.print_infractions_details(guild, infraction_detail,
                                                                            moderator_view=False)

        await member.send(
            f"You have been timed out in {guild.name} until {timeout_until.strftime('%Y-%m-%d %H:%M:%S')}.",
            embed=member_infraction_view,
        )

        return True, "Member has been timed out successfully.", infraction_detail, timeout_until

    @staticmethod
    async def print_infractions_details(guild: Guild, infraction: InfractionsSchema,
                                        moderator_view: bool = False) -> Embed:
        infraction_embed = Embed(
            title="Infraction Details",
            color=infraction.infraction_type.get_color(),
        )

        member = await get_member(guild, infraction.user_id)

        description = f"""
**Type:** {infraction.infraction_type.value}
**User:** {member.mention if member is not None else infraction.user_id}
**Reason:** `{infraction.reason}`
**Date:** {infraction.created_at.strftime('%Y-%m-%d %H:%M:%S')}
**Result:** {infraction.infraction_result.value}"""

        if infraction.gravity_id is not None:
            description += f"\n**Gravity:** {infraction.gravity.name}{f" ({infraction.gravity.weight})" if moderator_view else ""}"
        else:
            description += f"\n**Gravity:** None"

        if infraction.infraction_type == InfractionType.timeout or infraction.infraction_result == InfractionResult.timeout:
            description += f"\n**Timeout until:** {infraction.timeout_end.astimezone().strftime('%Y-%m-%d %H:%M:%S')}"

        infraction_embed.description = description

        if moderator_view:
            infraction_embed.add_field(
                name="Infraction ID",
                value=f"{infraction.id}",
                inline=False,
            )

            moderator = await get_member(guild, infraction.moderator_id)

            infraction_embed.add_field(
                name="Moderator",
                value=f"{moderator.mention if moderator is not None else infraction.moderator_id}",
                inline=False,
            )

        return infraction_embed

    @staticmethod
    async def check_member_permissions(bot: "IRBot", guild: Guild, member: Member) -> tuple[bool, str | None]:
        if member.top_role >= await get_bot_top_role(bot, guild):
            return False, f"I do not have permission to timeout {member.mention}."

        if member.guild_permissions.administrator:
            return False, f"{member.mention} is an administrator, they cannot be timed out."

        return True, None
