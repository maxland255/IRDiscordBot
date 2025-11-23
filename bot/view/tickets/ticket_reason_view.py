import logging

from typing import TYPE_CHECKING

from discord import InputTextStyle, Interaction
from discord.ui import DesignerModal, InputText, Label, TextDisplay

from bot.database.schemas import TicketTypeSchema

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
            tickets_cog: "Tickets | None" = self.bot.get_cog("Tickets")

            if tickets_cog is None:
                raise RuntimeError("Tickets cog is not loaded.")

            ticket_channel = await tickets_cog.create_ticket_from_interaction(interaction, self.ticket_type,
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
