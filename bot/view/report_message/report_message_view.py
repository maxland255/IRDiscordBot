import logging

from typing import TYPE_CHECKING

from datetime import datetime, UTC

from bot.database.schemas import ReportCreate
from bot.utils.get_guild import get_guild
from bot.utils.get_channel import get_channel

from discord import Member, Message, InputTextStyle, Interaction, Embed, Color, TextChannel
from discord.ui import InputText, Label, TextDisplay, DesignerModal

from .report_log_view import ReportLogView

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class ReportMessageView(DesignerModal):
    def __init__(self, bot: "IRBot", reporter: Member, message: Message):
        super().__init__(
            title="Report message",
            timeout=180,
        )

        self.bot = bot

        self.reporter = reporter
        self.message = message

        self.message_author = TextDisplay(
            content="**Author**\n" + str(message.author),
        )
        self.message_text = TextDisplay(
            content="**Message**\n" + (message.content if message.content else "[No Text Content]"),
        )

        self.reason_input = Label(
            label="Reason",
            item=InputText(
                placeholder="Enter the reason for reporting this message...",
                max_length=512,
                style=InputTextStyle.long,
            ),
        )

        self.add_item(self.message_author)
        self.add_item(self.message_text)
        self.add_item(self.reason_input)

    async def callback(self, interaction: Interaction):
        try:
            reason = self.reason_input.item.value

            report_embed = await self.print_report(author=self.reporter, message=self.message, reason=reason)

            report_log_view = ReportLogView(self.bot)

            report_channel = await self._get_report_channel(interaction.guild_id)

            report_message = await report_channel.send(
                embed=report_embed,
                view=report_log_view,
            )

            report = ReportCreate(
                guild_id=interaction.guild.id,
                reporter_id=interaction.user.id,
                report_reason=reason,
                offender_id=self.message.author.id,
                reported_channel_id=self.message.channel.id,
                reported_message_id=self.message.id,
                log_message_id=report_message.id,
            )

            await self.bot.db_reports.create_report(report)

            await interaction.response.send_message(
                "Your report has been submitted successfully. Thank you for helping us keep the community safe!",
                ephemeral=True,
            )
        except Exception as e:
            logger.error("An error occurred while submitting a message report: %s", e, exc_info=True)
            await interaction.response.send_message(
                "An error occurred while submitting your report. Please try again later.",
                ephemeral=True,
            )

    @staticmethod
    async def print_report(author: Member, message: Message, reason: str) -> Embed:
        report_embed = Embed(
            title="Message Report",
            description=f"A message has been reported by {author.mention}.",
            color=Color.dark_red(),
            timestamp=datetime.now(UTC),
        )

        report_embed.add_field(name="Reported Message", value=message.content or "No content", inline=False)
        report_embed.add_field(name="Message link", value=message.jump_url, inline=False)
        report_embed.add_field(name="Message Author", value=f"{message.author.mention} | {message.author.id}",
                               inline=False)

        report_embed.add_field(name="Reported by", value=f"{author.mention} | {author.id}", inline=False)
        report_embed.add_field(name="Reason", value=reason, inline=False)

        return report_embed

    async def _get_report_channel(self, guild_id: int) -> TextChannel | None:
        guild_config = await self.bot.db_guilds.get_guild_by_id(guild_id)

        if guild_config is None:
            return None

        report_channel_id = guild_config.report_channel_id

        if report_channel_id is None:
            return None

        guild = await get_guild(self.bot, guild_id)

        if guild is None:
            logger.error(f"Error fetching guild {guild_id} for reports logs.")
            return None

        report_channel = await get_channel(guild, report_channel_id)

        return report_channel
