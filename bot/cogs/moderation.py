import logging

from discord import Cog, ApplicationContext, SlashCommandGroup, Option, Member, guild_only, Permissions, \
    InteractionContextType, AutocompleteContext

from typing import TYPE_CHECKING

from datetime import datetime, timedelta, UTC

from bot.database.schemas import GravityLevelSchema
from bot.utils.bot_extensions import get_bot_top_role

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
        name="timeout",
        description="Test command",
    )
    @guild_only()
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

            if member.top_role >= await get_bot_top_role(self.bot, ctx.guild):
                await ctx.respond(f"I do not have permission to timeout {member.mention}.")
                return

            if member.guild_permissions.administrator:
                await ctx.respond(f"{member.mention} is an administrator, they cannot be timed out.")
                return

            gravity_level = await self.bot.db_gravity_levels.get_gravity_level_by_name(gravity)

            if gravity_level is None:
                await ctx.respond(f"Gravity level with name {gravity} not found.")
                return

            ###############################

            member_roles = member.roles

            for role in member_roles:
                if role.permissions.administrator:
                    await ctx.respond(f"{member.mention} is an administrator, they cannot be timed out.",
                                      ephemeral=True)
                    return

            until = datetime.now(UTC) + timedelta(days=28)

            await member.timeout(until=until, reason="Timeout command")

            await ctx.respond(f"{member.mention} has been timed out until {until.strftime('%Y-%m-%d %H:%M:%S')}.",
                              ephemeral=True)
        except Exception as e:
            logger.error("An error occurred while running the timeout command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the timeout command", ephemeral=True)

    # @staticmethod
    # def autocomplete(ctx: AutocompleteContext):
    #     print(ctx.command)
    #     print(ctx.value)
    #     print(ctx.interaction)
    #     print(ctx.options)
    #     print(type(ctx.bot))
    #
    #     return ["low", "medium", "high"]
    #
    # @moderator.command(
    #     name="test"
    # )
    # async def test(
    #         self,
    #         ctx: ApplicationContext,
    #         member: Member = Option(Member),
    #         gravity: str = Option(
    #             str,
    #             autocomplete=autocomplete
    #         )
    # ):
    #     await ctx.respond(f"Testing {gravity}.", ephemeral=True)

    # Listener / Event
    # @Cog.listener()
    # async def on_message(self, message):
    #     print("Message from Moderation Cogs")
    #     print(message.content)
