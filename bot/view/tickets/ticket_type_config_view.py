import logging

from typing import TYPE_CHECKING

from discord import InputTextStyle, ComponentType, ChannelType, Interaction, SelectOption, Embed, Color, \
    CategoryChannel, Guild, Role
from discord.ui import DesignerModal, Label, InputText, Select, RoleSelect
from discord.utils import get_or_fetch

from bot.database.schemas import TicketTypeSchema, TicketTypeCreate, TicketTypeUpdate

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class TicketTypeConfigView(DesignerModal):
    def __init__(self, bot: "IRBot", ticket_type: TicketTypeSchema | None = None):
        super().__init__(
            title="Ticket Type Configuration",
            timeout=300,
        )
        self.bot = bot
        self.ticket_type = ticket_type

        # Name Input
        self.name_input = InputText(
            placeholder="Ticket Type Name",
            max_length=16,
            required=True,
            value=None if ticket_type is None else ticket_type.name,
        )

        self.name_label = Label(
            label="Ticket Type Name",
            item=self.name_input,
        )

        # Description Input
        self.description_input = InputText(
            placeholder="Ticket Type Description",
            style=InputTextStyle.long,
            max_length=4000,
            required=True,
            value=None if ticket_type is None else ticket_type.description,
        )

        self.description_label = Label(
            label="Ticket Type Description",
            item=self.description_input,
        )

        # Category Select
        self.category_select = Select(
            placeholder="Select where ticket channels will be created",
            select_type=ComponentType.channel_select,
            required=True,
            max_values=1,
            channel_types=[ChannelType.category],
        )
        if ticket_type is not None:
            self.category_select.add_default_value(id=ticket_type.ticket_channel_category_id)

        self.category_label = Label(
            label="Ticket Channel Category",
            item=self.category_select,
        )

        # Require Initial Reason Input
        self.requires_initial_reason_select = Select(
            placeholder="Ticket requires initial reason?",
            required=True,
            options=[
                SelectOption(
                    label="Yes",
                    value="yes",
                    description="Users must provide an initial reason when creating a ticket",
                    default=False if ticket_type is None else ticket_type.requires_initial_reason,
                ),
                SelectOption(
                    label="No",
                    value="no",
                    description="Users are not required to provide an initial reason when creating a ticket",
                    default=False if ticket_type is None else not ticket_type.requires_initial_reason,
                ),
            ],
        )

        self.requires_initial_reason_label = Label(
            label="Requires Initial Reason",
            item=self.requires_initial_reason_select,
        )

        # Moderator Role
        self.moderator_role_select = RoleSelect(
            placeholder="Select the moderator role for this ticket type",
            required=True,
            max_values=1,
        )
        if ticket_type is not None:
            self.moderator_role_select.add_default_value(id=ticket_type.moderator_role_id)

        self.moderator_role_label = Label(
            label="Moderator Role",
            item=self.moderator_role_select,
        )

        # Add items
        self.add_item(self.name_label)
        self.add_item(self.description_label)
        self.add_item(self.category_label)
        self.add_item(self.requires_initial_reason_label)
        self.add_item(self.moderator_role_label)

    async def callback(self, interaction: Interaction):
        if self.ticket_type is None:
            await self.create_ticket_type_from_interaction(interaction)
        else:
            await self.update_ticket_type_from_interaction(interaction)

    async def create_ticket_type_from_interaction(self, interaction: Interaction):
        try:
            new_ticket_type = TicketTypeCreate(
                guild_id=interaction.guild_id,
                name=self.name_input.value,
                description=self.description_input.value,
                ticket_channel_category_id=self.category_select.values[0].id,
                requires_initial_reason=self.requires_initial_reason_select.values[0] == "yes",
                moderator_role_id=self.moderator_role_select.values[0].id,
            )

            ticket_type = await self.bot.db_ticket_type.create_ticket_type(new_ticket_type)

            ticket_type_embed = await self.create_ticket_type_embed(self.bot, interaction.guild, ticket_type)

            await interaction.response.send_message(
                content="Ticket type created!",
                embed=ticket_type_embed,
                ephemeral=True,
            )
        except Exception as e:
            logger.exception(f"Failed to create ticket type", exc_info=e)
            await interaction.response.send_message(
                content="An error occurred while creating the ticket type.",
                ephemeral=True,
            )

    async def update_ticket_type_from_interaction(self, interaction: Interaction):
        try:
            update_ticket_type = TicketTypeUpdate(
                id=self.ticket_type.id,
            )

            if self.ticket_type.name != update_ticket_type.name:
                update_ticket_type.name = self.name_input.value

            if self.ticket_type.description != update_ticket_type.description:
                update_ticket_type.description = self.description_input.value

            category_id = self.category_select.values[0].id
            if self.ticket_type.ticket_channel_category_id != category_id:
                update_ticket_type.ticket_channel_category_id = category_id

            requires_initial_reason = self.requires_initial_reason_select.values[0] == "yes"
            if self.ticket_type.requires_initial_reason != requires_initial_reason:
                update_ticket_type.requires_initial_reason = requires_initial_reason

            moderator_role_id = self.moderator_role_select.values[0].id
            if self.ticket_type.moderator_role_id != moderator_role_id:
                update_ticket_type.moderator_role_id = moderator_role_id

            ticket_type = await self.bot.db_ticket_type.update_ticket_type(update_ticket_type)

            await interaction.response.send_message(
                content="Ticket type updated!",
                embed=await self.create_ticket_type_embed(self.bot, interaction.guild, ticket_type),
                ephemeral=True,
            )
        except Exception as e:
            logger.exception(f"Failed to update ticket type", exc_info=e)
            await interaction.response.send_message(
                content="An error occurred while updating the ticket type.",
                ephemeral=True,
            )

    @staticmethod
    async def create_ticket_type_embed(bot: "IRBot", guild: Guild, ticket_type: TicketTypeSchema) -> Embed:
        ticket_type_embed = Embed(
            title=ticket_type.name,
            description=ticket_type.description,
            color=Color.blurple(),
        )

        ticket_type_embed.add_field(
            name="Ticket Type ID",
            value=str(ticket_type.id),
            inline=False,
        )

        category = await get_or_fetch(bot, CategoryChannel, ticket_type.ticket_channel_category_id, None)

        ticket_type_embed.add_field(
            name="Channel Category",
            value=category.name if category is not None else "Deleted Category",
            inline=False,
        )

        ticket_type_embed.add_field(
            name="Requires Initial Reason",
            value="Yes" if ticket_type.requires_initial_reason else "No",
            inline=False,
        )

        moderator_role = await get_or_fetch(guild, Role, ticket_type.moderator_role_id, None)

        ticket_type_embed.add_field(
            name="Moderator Role",
            value=moderator_role.mention if moderator_role is not None else "Deleted Role",
            inline=False,
        )

        ticket_type_embed.add_field(
            name="Enabled",
            value="Yes" if ticket_type.enabled else "No",
            inline=False,
        )

        ticket_type_embed.add_field(
            name="System Ticket Type",
            value="Yes" if ticket_type.is_system else "No",
            inline=False,
        )

        return ticket_type_embed
