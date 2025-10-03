import logging

from discord import Cog, ApplicationContext, SlashCommandGroup, Option, Member, guild_only, Permissions, \
    InteractionContextType

from typing import TYPE_CHECKING

from datetime import datetime, timedelta, UTC

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


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
    ):
        try:
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

    # Listener / Event
    # @Cog.listener()
    # async def on_message(self, message):
    #     print("Message from Moderation Cogs")
    #     print(message.content)
