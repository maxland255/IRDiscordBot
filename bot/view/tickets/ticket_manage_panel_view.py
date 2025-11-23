import logging

from typing import TYPE_CHECKING, Optional
from datetime import datetime, UTC

from discord import ButtonStyle, Interaction, Embed, Color, Member
from discord.ui import DesignerView, ActionRow

from bot.view.components import ActionButton
from bot.database.schemas import TicketTypeSchema, TicketsUpdate
from bot.utils.get_role import get_role

if TYPE_CHECKING:
    from bot.cogs.tickets import Tickets
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class TicketManagePanelView(DesignerView):
    def __init__(self, bot: "IRBot"):
        super().__init__(timeout=None)
        self.bot = bot

        self.close_button = ActionButton(
            label="Fermer le ticket",
            style=ButtonStyle.danger,
            custom_id="ticket_control:close",
            on_click=self._on_close_ticket,
        )

        self.assign_button = ActionButton(
            label="Réclamer",
            emoji="🙋",
            custom_id="ticket_control:assign",
            on_click=self._on_assign_ticket
        )

        self.action_row = ActionRow(
            self.close_button,
            self.assign_button,
        )

        self.add_item(self.action_row)

    async def _on_close_ticket(self, interaction: Interaction):
        try:
            tickets_cog: Optional["Tickets"] = self.bot.get_cog("Tickets")

            if tickets_cog is None:
                raise RuntimeError("Tickets cog is not loaded.")

            await tickets_cog.close_ticket_channel(interaction)
        except Exception as e:
            logger.error("Failed to close ticket", exc_info=e)
            await interaction.followup.send(
                "An error occurred while closing the ticket. Please try again later.",
                ephemeral=True,
            )
        else:
            self.restore_default_button_properties()

    async def _on_assign_ticket(self, interaction: Interaction):
        try:
            ticket = await self.bot.db_tickets.get_ticket_by_channel_id(interaction.channel_id)

            if ticket is None:
                await interaction.response.send_message(
                    "Unable to assign ticket: Ticket not found.",
                    ephemeral=True,
                )
                return

            ticket_type = ticket.ticket_type

            moderator_role = await get_role(interaction.guild, ticket_type.moderator_role_id)

            if moderator_role is None:
                await interaction.response.send_message(
                    "Unable to assign ticket: Moderator role not found.",
                    ephemeral=True,
                )
                return

            if moderator_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "You do not have permission to assign this ticket.",
                    ephemeral=True,
                )
                return

            panel_message = interaction.message

            panel_message_embed = panel_message.embeds[0]

            panel_message_embed.add_field(
                name="Handler",
                value=interaction.user.mention,
                inline=False,
            )

            self.assign_button.disabled = True

            await panel_message.edit(
                embed=panel_message_embed,
                view=self,
            )

            update_ticket = TicketsUpdate(
                id=ticket.id,
                handler_id=interaction.user.id,
            )

            await self.bot.db_tickets.update_ticket(update_ticket)

            await interaction.response.send_message(
                f"You have successfully claimed this ticket.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error("Failed to assign ticket", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while assigning the ticket. Please try again later.",
                ephemeral=True,
            )
        else:
            self.restore_default_button_properties()

    def restore_default_button_properties(self):
        self.close_button.disabled = False
        self.assign_button.disabled = False

    @staticmethod
    def create_panel_embed(ticket_type: TicketTypeSchema, author: Member, reason: str | None = None) -> Embed:
        ticket_panel_embed = Embed(
            title="Ticket Panel",
            description=f"Veuillez utiliser les boutons ci-dessous pour gérer votre ticket.",
            colour=Color.dark_red(),
            timestamp=datetime.now(UTC),
        )

        ticket_panel_embed.set_author(
            name=author.display_name,
            icon_url=author.display_avatar.url,
        )

        ticket_panel_embed.add_field(
            name="Type",
            value=ticket_type.name,
        )

        if reason is not None:
            ticket_panel_embed.add_field(
                name="Reason",
                value=reason,
                inline=False,
            )

        ticket_panel_embed.add_field(
            name="Membre",
            value=author.mention,
        )

        return ticket_panel_embed
