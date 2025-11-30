import logging

from typing import TYPE_CHECKING, Literal
from datetime import datetime, UTC
from functools import partial

from discord import ButtonStyle, Interaction, Embed, Member, Guild
from discord.ui import DesignerView, ActionRow

from bot.view.components import ActionButton
from bot.database.schemas import TicketsSchema

from .verif_reason_modals import VerifReasonModals

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class TicketVerifResultPanelView(DesignerView):
    def __init__(self, bot: "IRBot"):
        super().__init__(timeout=None)
        self.bot = bot

        self.verify_alumni = ActionButton(
            style=ButtonStyle.primary,
            label="Verified as Alumni",
            custom_id="ticket:verify:alumni",
            on_click=partial(self._handle_button, action="verified_alumni"),
        )

        self.verify_external = ActionButton(
            style=ButtonStyle.primary,
            label="Verified as External",
            custom_id="ticket:verify:external",
            on_click=partial(self._handle_button, action="verified_external"),
        )

        self.kick_user = ActionButton(
            style=ButtonStyle.danger,
            label="Kick User",
            custom_id="ticket:verify:kick",
            on_click=partial(self._handle_button, action="kick_user"),
        )

        self.other_button = ActionButton(
            style=ButtonStyle.success,
            label="Other",
            custom_id="ticket:verify:other",
            on_click=partial(self._handle_button, action="other"),
        )

        self.action_row = ActionRow(
            self.verify_alumni,
            self.verify_external,
            self.kick_user,
            self.other_button,
        )

        self.add_item(self.action_row)

    async def _handle_button(self, interaction: Interaction,
                             action: Literal["verified_alumni", "verified_external", "kick_user", "other"]):
        try:
            ticket = await self.bot.db_tickets.get_ticket_by_channel_id(interaction.channel_id)

            if ticket is None:
                await interaction.response.send_message(
                    "Ticket not found for this channel. Please contact an administrator.",
                    ephemeral=True,
                )
                return

            if not await self._check_member_permissions(interaction.user, ticket):
                await interaction.response.send_message(
                    "You do not have permission to perform this action.",
                    ephemeral=True,
                )
                return

            await interaction.response.send_modal(VerifReasonModals(self.bot, ticket, action))
        except Exception as e:
            logger.error(f"Error verifying user as student", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while trying to verify the user as a student. Please contact an administrator.",
                ephemeral=True,
            )

    @staticmethod
    async def _check_member_permissions(member: Member, ticket: TicketsSchema) -> bool:
        if member.guild_permissions.administrator:
            return True

        moderator_role = await member.guild.get_or_fetch(Guild, ticket.ticket_type.moderator_role_id)

        if moderator_role in member.roles:
            return True

        return False

    @staticmethod
    def create_ticket_verif_result_panel_embed(member: Member) -> Embed:
        panel_embed = Embed(
            title="Verification Ticket - Action Panel",
            description="Use the buttons below to take action on this verification ticket.",
            color=0x3498db,
            timestamp=datetime.now(UTC),
        )

        panel_embed.set_author(
            name=member.display_name,
            icon_url=member.avatar.url,
        )

        return panel_embed
