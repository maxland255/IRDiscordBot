import logging

from typing import TYPE_CHECKING

from discord import InputTextStyle, Interaction, CategoryChannel, TextChannel
from discord.utils import get_or_fetch
from discord.ui import DesignerModal, InputText, Label, TextDisplay

from bot.cogs.tickets import Tickets
from bot.database.schemas import TicketTypeSchema, TicketsCreate, TicketsUpdate
from bot.utils.ticket_permissions import get_member_permissions, get_default_role_permissions, get_moderator_permissions
from bot.utils.get_role import get_role
from bot.view.tickets.ticket_manage_panel_view import TicketManagePanelView

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class TicketReasonView(DesignerModal):
    def __init__(self, bot: "IRBot", ticket_type: TicketTypeSchema):
        super().__init__(
            title="Ticket Reason",
            timeout=300,
        )
        self.bot = bot
        self.ticket_type = ticket_type

        self.information = TextDisplay(
            content="Please does not abuse the ticket system. Provide a valid reason for opening this ticket."
                    "\nYou need to open the correct ticket type for your issue."
                    "\nIf you open multiple tickets without a valid reason, you may be blocked from opening tickets in the future."
                    "\nThank you for your understanding.",
        )

        self.ticket_name = TextDisplay(
            content=f"You are opening a ticket of type: **{self.ticket_type.name}**",
        )

        self.reason_input = InputText(
            required=True,
            max_length=1024,
            placeholder="Enter the reason for opening this ticket",
            style=InputTextStyle.long,
        )
        self.reason_label = Label(
            label="Reason",
            item=self.reason_input,
        )

        self.add_item(self.information)
        self.add_item(self.ticket_name)
        self.add_item(self.reason_label)

    async def callback(self, interaction: Interaction):
        try:
            ticket_channel = await self.create_ticket(interaction, self.bot, self.ticket_type,
                                                      reason=self.reason_input.value)

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

    @staticmethod
    async def create_ticket(interaction: Interaction, bot: "IRBot", ticket_type: TicketTypeSchema,
                            reason: str | None = None) -> TextChannel:
        # Check if the ticket type exists and is active

        ticket_type = await bot.db_ticket_type.get_ticket_type_by_id(ticket_type.id)

        if ticket_type is None or ticket_type.deleted_at is not None:
            raise ValueError("Ticket type does not exist or is inactive.")

        existing_ticket = await bot.db_tickets.find_open_ticket_by_member_id_guild_id_and_type_id(
            interaction.guild_id, interaction.user.id, ticket_type.id)

        if existing_ticket:
            await interaction.response.send_message(
                "You already have an open ticket of this type. Please close your existing ticket before opening a new one.",
                ephemeral=True
            )
            return

        new_ticket = TicketsCreate(
            ticket_type_id=ticket_type.id,
            member_id=interaction.user.id,
        )

        try:
            ticket = await bot.db_tickets.create_ticket(new_ticket)
        except Exception as e:
            logger.exception("Failed to create ticket", exc_info=e)
            raise RuntimeError("An error occurred while creating the ticket.") from e

        ticket_category = await get_or_fetch(interaction.guild, CategoryChannel, ticket_type.ticket_channel_category_id)

        if ticket_category is None:
            raise ValueError("Ticket category channel not found.")

        moderator_role = await get_role(interaction.guild, ticket_type.moderator_role_id)

        if moderator_role is None:
            raise ValueError("Moderator role not found.")

        ticket_channel = await ticket_category.create_text_channel(
            name=f"{ticket_type.name} - {ticket.id}",
            overwrites={
                interaction.guild.default_role: get_default_role_permissions(),
                interaction.user: get_member_permissions(),
                moderator_role: get_moderator_permissions(),
            },
            reason=f"Creating ticket channel for ticket ID {ticket.id} ({interaction.user.display_name})",
        )

        # Add the ticket channel ID to the in-memory set
        tickets_cog: Tickets | None = bot.get_cog("Tickets")

        if tickets_cog is None:
            logger.error("Failed to load tickets cog")
        else:
            tickets_cog.add_ticket_channel_id(ticket_channel.id)

        ticket_panel_view = TicketManagePanelView(bot)

        ticket_panel_message = await ticket_channel.send(
            embed=ticket_panel_view.create_panel_embed(ticket_type, author=interaction.user, reason=reason),
            view=ticket_panel_view,
        )

        try:
            await ticket_panel_message.pin()
        except Exception as e:
            logger.warning(f"Failed to pin ticket panel message in channel {ticket_channel.id}: {e}", exc_info=e)

        update_ticket = TicketsUpdate(
            id=ticket.id,
            channel_id=ticket_channel.id,
            panel_message_id=ticket_panel_message.id,
        )

        await bot.db_tickets.update_ticket(update_ticket)

        return ticket_channel
