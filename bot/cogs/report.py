import logging

from typing import TYPE_CHECKING

from discord import Cog, SlashCommandGroup, InteractionContextType, ApplicationContext, Message, commands

from bot.view.report_message.report_message_view import ReportMessageView

from .cogs_base import CogsBase

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class Report(Cog, CogsBase):
    def __init__(self, bot: "IRBot"):
        self.bot = bot

    report = SlashCommandGroup(
        name="report",
        description="Commands related to reporting issues or users.",
        contexts={InteractionContextType.guild}
    )

    @commands.message_command(
        name="Report Message",
    )
    async def report_message(self, ctx: ApplicationContext, message: Message):
        try:
            guild_config = await self.bot.db_guilds.get_guild_by_id(ctx.guild.id)

            if guild_config is None:
                await ctx.respond(
                    "Guild configuration not found. Please contact the bot administrator.",
                    ephemeral=True,
                )
                return

            report_message_view = ReportMessageView(
                bot=self.bot,
                reporter=ctx.author,
                message=message,
            )

            await ctx.send_modal(report_message_view)
        except Exception as e:
            logger.error("An error occurred while running the report message command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the report message command", ephemeral=True)

    # Method
