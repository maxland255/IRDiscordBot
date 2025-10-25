import logging

from datetime import datetime, UTC

from typing import TYPE_CHECKING

from discord import Interaction, SelectOption, Color, Member, Embed
from discord.ui import DesignerView, Select, ActionRow

from bot.database.schemas import ReportSchema, ReportStatus, ReportUpdate, ReportAction
from bot.utils.get_channel import get_channel

from .report_log_action_view import ReportLogActionView

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class SelectAction(Select):
    def __init__(self, bot: "IRBot", parent_view: "ReportLogView"):
        super().__init__(
            custom_id="report_log:action",
            min_values=1,
            max_values=1,
            placeholder="Select an action",
            options=[
                SelectOption(
                    label="Avertir (Warn)",
                    value="action:warn",
                    description="Envoyer un avertissement au membre.",
                    emoji="⚠️",
                ),
                SelectOption(
                    label="Exclure (Timeout)",
                    value="action:timeout",
                    description="Exclure temporairement le membre.",
                    emoji="⏳"
                ),
                SelectOption(
                    label="Supprimer le message",
                    value="action:delete_message",
                    description="Supprimer le message signalé.",
                    emoji="🗑️"
                ),
                SelectOption(
                    label="Classer sans suite",
                    value="action:dismiss",
                    description="Clore le signalement sans action.",
                    emoji="✅"
                ),
            ],
        )

        self.bot = bot
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        try:
            report = await self.parent_view.get_report_from_interaction(interaction)

            if report is None:
                await interaction.response.send_message(
                    "This report has already been processed or is no longer available.",
                    ephemeral=True,
                )
                return

            selected_action = self.values[0]

            report_update = ReportUpdate(
                id=report.id,
                status=ReportStatus.DISMISSED,
                handler_id=interaction.user.id,
                handler_action=ReportAction.none,
                handled_at=datetime.now(UTC),
            )

            if selected_action == "action:warn":
                report_action_view = ReportLogActionView(
                    bot=self.bot,
                    report=report,
                    gravity_levels=[],
                    update_report_message_status=self.update_report_message_status,
                    timeout=False,
                )

                await interaction.response.send_modal(report_action_view)
            elif selected_action == "action:timeout":
                gravity_levels = await self.bot.db_gravity_levels.get_all_gravity_level(interaction.guild_id)

                if len(gravity_levels) < 1:
                    await interaction.response.send_message(
                        "No gravity levels are configured for this server. Please set them up before using this action.",
                        ephemeral=True,
                    )
                    return

                report_action_view = ReportLogActionView(
                    bot=self.bot,
                    report=report,
                    gravity_levels=gravity_levels,
                    update_report_message_status=self.update_report_message_status,
                    timeout=True,
                )

                await interaction.response.send_modal(report_action_view)
            elif selected_action == "action:delete_message":
                channel = await get_channel(interaction.guild, report.reported_channel_id)

                if channel is None:
                    await interaction.response.send_message(
                        "The channel where the reported message was located could not be found.",
                        ephemeral=True,
                    )
                    return

                message = channel.get_partial_message(report.reported_message_id)
                await message.delete(reason="Reported message deletion by moderator.")

                report_update.status = ReportStatus.HANDLED
                report_update.handler_action = ReportAction.deleted

                await self.bot.db_reports.update_report(report_update)

                await self.update_report_message_status(interaction, "Message supprimé", interaction.user)
            elif selected_action == "action:dismiss":
                await self.bot.db_reports.update_report(report_update)

                await self.update_report_message_status(interaction, "Classé sans suite", interaction.user)
        except Exception as e:
            await interaction.response.send_message(
                "An error occurred while processing the report. Please try again later.",
                ephemeral=True,
            )
            logger.error(f"An error occurred while processing a report action: {e}", exc_info=True)

    @staticmethod
    async def update_report_message_status(interaction: Interaction, outcome_text: str, moderator: Member):
        embed: Embed = interaction.message.embeds[0]
        embed.colour = Color.green()
        embed.add_field(name="Statut", value=f"**Traité par :** {moderator.mention}\n**Action :** {outcome_text}")

        await interaction.response.edit_message(embed=embed, view=None)


class ReportLogView(DesignerView):
    def __init__(self, bot: "IRBot"):
        super().__init__(timeout=None)

        self.bot = bot

        self.action_row = ActionRow()

        self.action_row.add_item(SelectAction(bot, self))

        self.add_item(self.action_row)

    async def get_report_from_interaction(self, interaction: Interaction) -> ReportSchema | None:
        log_message_id = interaction.message.id

        report = await self.bot.db_reports.get_report_by_log_message_id(log_message_id)

        if report.status == ReportStatus.OPEN:
            return report

        return None
