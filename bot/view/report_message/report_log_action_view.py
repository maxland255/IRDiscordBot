import logging

from typing import TYPE_CHECKING
from datetime import datetime, UTC

from discord import ComponentType, SelectOption, InputTextStyle, Interaction, Guild
from discord.ui import DesignerModal, Label, InputText, Select

from bot.database.schemas import GravityLevelSchema, ReportSchema, ReportUpdate, ReportStatus, ReportAction
from bot.cogs import Moderation
from bot.utils.get_channel import get_channel
from bot.utils.get_member import get_member

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class ReportLogActionView(DesignerModal):
    def __init__(self, bot: "IRBot", report: ReportSchema, gravity_levels: list[GravityLevelSchema],
                 update_report_message_status,
                 timeout: bool = False):
        """
        Show a modal to enter the action parameters.
        If timeout is False, show a modal to enter the warning reason.
        If timeout is True, show a modal to enter the timeout gravity level and reason.
        :param timeout:
        """
        super().__init__(
            timeout=300,
            title="Log Report Action",
        )
        self.bot = bot
        self.report = report
        self.gravity_levels = gravity_levels
        self.update_report_message_status = update_report_message_status
        self.timeout = timeout

        self.select_delete_message = Select(
            placeholder="Select Delete Message Action",
            min_values=1,
            max_values=1,
            required=True,
            options=[
                SelectOption(
                    label="Yes",
                    value="yes",
                    description="Delete the reported message.",
                ),
                SelectOption(
                    label="No",
                    value="no",
                    description="Do not delete the reported message.",
                ),
            ]
        )

        self.select_label = Label(
            label="Delete Reported Message",
            item=self.select_delete_message,
        )

        self.add_item(self.select_label)

        if self.timeout:
            self.select_gravity_level = Select(
                select_type=ComponentType.string_select,
                placeholder="Select Gravity Level",
                min_values=1,
                max_values=1,
                options=[SelectOption(
                    label=g.name,
                    value=str(g.id),
                    description=g.description,
                ) for g in self.gravity_levels]
            )

            self.select_gravity_level_label = Label(
                label="Gravity Level",
                item=self.select_gravity_level,
            )

            self.add_item(self.select_gravity_level_label)

        self.reason_input = InputText(
            placeholder="Enter the reason for this action...",
            max_length=512,
            style=InputTextStyle.long,
        )

        self.reason_label = Label(
            label="Reason",
            item=self.reason_input,
        )

        self.add_item(self.reason_label)

    async def callback(self, interaction: Interaction):
        report = await self.bot.db_reports.get_report_by_id(self.report.id)

        if report is None or report.status != ReportStatus.OPEN:
            await interaction.response.send_message(
                "This report has already been processed or is no longer available.",
                ephemeral=True,
            )
            return

        delete_message = self.select_delete_message.values[0] == "yes"
        reason = self.reason_input.value

        report_update = ReportUpdate(
            id=self.report.id,
            status=ReportStatus.HANDLED,
            handler_id=interaction.user.id,
            handler_action=ReportAction.warned,
            handled_at=datetime.now(UTC),
        )

        outcome_text = ""

        if delete_message:
            outcome_text += "Message supprimé."
            await self.delete_message(interaction.guild)

        member = await get_member(interaction.guild, report.offender_id)

        if self.timeout:
            gravity_level_id = int(self.select_gravity_level.values[0])

            gravity_level = self.find_gravity_level(gravity_level_id)
            if gravity_level is None:
                await interaction.response.send_message(
                    "Selected gravity level not found. Please try again.",
                    ephemeral=True,
                )
                return

            result, message, infraction_detail, timeout_until = await Moderation.timeout_member(
                self.bot,
                interaction.guild,
                interaction.user,
                member,
                gravity_level,
                reason
            )

            if not result:
                await interaction.response.send_message(
                    f"Failed to timeout member: {message}",
                    ephemeral=True,
                )
                return

            report_update.handler_action = ReportAction.timeout

            await self.bot.db_reports.update_report(report_update)

            outcome_text += f"\nMembre timeout jusqu'à {timeout_until.strftime('%Y-%m-%d %H:%M:%S')}."

            self.update_report_message_status(interaction, outcome_text.strip(), interaction.user)
            return

        result, message, infraction_detail = await Moderation.warn_member(
            self.bot,
            interaction.guild,
            interaction.user,
            member,
            reason,
        )

        if not result:
            await interaction.response.send_message(
                f"Failed to warn member: {message}",
                ephemeral=True,
            )
            return

        await self.bot.db_reports.update_report(report_update)

        outcome_text += "\nMembre averti."
        self.update_report_message_status(interaction, outcome_text.strip(), interaction.user)

    def find_gravity_level(self, gravity_level_id: int) -> GravityLevelSchema | None:
        for gravity_level in self.gravity_levels:
            if gravity_level.id == gravity_level_id:
                return gravity_level
        return None

    async def delete_message(self, guild: Guild) -> bool:
        channel = await get_channel(guild, self.report.reported_channel_id)

        if channel is None:
            return False

        try:
            message = await channel.fetch_message(self.report.reported_message_id)
            await message.delete(reason="Reported message deleted by moderator action.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete reported message: {e}", exc_info=True)
            return False
