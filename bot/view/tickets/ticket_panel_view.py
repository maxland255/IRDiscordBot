import logging

from typing import TYPE_CHECKING, Optional
from datetime import datetime, UTC

from discord import ButtonStyle, Interaction, Embed
from discord.ui import DesignerView, ActionRow

from bot.view.components import ActionButton
from bot.database.schemas import TicketTypeSchema
from bot.view.tickets import TicketReasonView

if TYPE_CHECKING:
    from bot.cogs.tickets import Tickets
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class TicketPanelView(DesignerView):
    def __init__(self, bot: "IRBot", ticket_type: TicketTypeSchema | None = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_type = ticket_type

        self.action_row = ActionRow(
            ActionButton(
                style=ButtonStyle.primary,
                label=f"Open {ticket_type.name} ticket" if ticket_type is not None else "Open Ticket",
                custom_id="ticket_panel:open_ticket",
                emoji="🎫",
                on_click=self._on_open_ticket,
            )
        )

        self.add_item(self.action_row)

    async def _on_open_ticket(self, interaction: Interaction):
        ticket_panel = await self.bot.db_ticket_panel.get_ticket_panel_by_message_id(interaction.message.id)

        if ticket_panel is None:
            await interaction.response.send_message(
                "This ticket panel is not configured properly. Please contact an administrator.",
                ephemeral=True
            )
            return

        ticket_type = ticket_panel.ticket_type

        if ticket_type.deleted_at is not None:
            await interaction.response.send_message(
                "The ticket type associated with this panel has been deleted. Please contact an administrator.",
                ephemeral=True
            )
            return

        if not ticket_type.enabled:
            await interaction.response.send_message(
                "The ticket type associated with this panel is currently disabled. Please contact an administrator.",
                ephemeral=True
            )
            return

        existing_ticket = await self.bot.db_tickets.find_open_ticket_by_member_id_guild_id_and_type_id(
            interaction.guild_id, interaction.user.id, ticket_type.id)

        if existing_ticket:
            await interaction.response.send_message(
                "You already have an open ticket of this type. Please close your existing ticket before opening a new one.",
                ephemeral=True
            )
            return

        if ticket_type.requires_initial_reason:
            await interaction.response.send_modal(
                TicketReasonView(self.bot, ticket_type)
            )
            return

        try:
            tickets_cog: Optional["Tickets"] = self.bot.get_cog("Tickets")

            if tickets_cog is None:
                raise RuntimeError("Tickets cog is not loaded.")

            ticket_channel = await tickets_cog.create_ticket_from_interaction(interaction, ticket_type)

            await interaction.response.send_message(
                f"Your ticket has been created successfully. Please check your channels: {ticket_channel.mention}",
                ephemeral=True,
            )
        except ValueError as e:
            logger.error("Failed to create ticket", exc_info=e)
            await interaction.response.send_message(
                "Failed to create ticket, the ticket type may be inactive or misconfigured.",
                ephemeral=True,
            )
        except RuntimeError as e:
            logger.error("Failed to create ticket", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while creating the ticket. Please try again later.",
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("Unexpected error occurred while creating ticket", exc_info=e)
            await interaction.response.send_message(
                "An unexpected error occurred. Please contact an administrator.",
                ephemeral=True,
            )

    def create_panel_embed(self) -> Embed:
        if self.ticket_type is None:
            raise ValueError("Ticket type is not set for this panel view.")

        ticket_panel_embed = Embed(
            title=f"{self.ticket_type.name} Ticket",
            description=self.ticket_type.description,
            timestamp=datetime.now(UTC),
            colour=0x3498db,
        )

        return ticket_panel_embed
