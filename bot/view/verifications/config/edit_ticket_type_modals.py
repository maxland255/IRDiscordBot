import logging

from typing import TYPE_CHECKING

from discord import ComponentType, ChannelType, Interaction
from discord.ui import DesignerModal, Label, Select

from bot.database.schemas import GuildSchema, GuildUpdate, TicketTypeSchema, TicketTypeCreate, TicketTypeUpdate

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.verifications import Verifications

logger = logging.getLogger(__name__)


class EditVerificationTicketTypeModal(DesignerModal):
    def __init__(self, bot: "IRBot", guild_config: GuildSchema, ticket_type: TicketTypeSchema | None):
        super().__init__(
            title="Edit Verification Ticket Type",
        )
        self.bot = bot
        self.guild_config = guild_config
        self.ticket_type = ticket_type

        self.moderator_role_select = Select(
            placeholder="Select a moderator role",
            select_type=ComponentType.role_select,
            required=True,
            min_values=1,
            max_values=1,
        )
        if self.ticket_type is not None:
            self.moderator_role_select.add_default_value(id=self.ticket_type.moderator_role_id)
        self.moderator_role_label = Label(
            label="Moderator Role",
            item=self.moderator_role_select,
        )
        self.add_item(self.moderator_role_label)

        self.category_select = Select(
            placeholder="Select the ticket category",
            select_type=ComponentType.channel_select,
            required=True,
            min_values=1,
            max_values=1,
            channel_types=[ChannelType.category],
        )
        if self.ticket_type is not None:
            self.category_select.add_default_value(id=self.ticket_type.ticket_channel_category_id)
        self.category_label = Label(
            label="Ticket Category",
            item=self.category_select,
        )
        self.add_item(self.category_label)

    async def callback(self, interaction: Interaction):
        try:
            guild_config = await self.bot.db_guilds.get_guild_by_id(self.guild_config.id)

            if guild_config is None:
                await interaction.response.send_message(
                    "Guild configuration not found. Please set up the bot again.",
                    ephemeral=True,
                )
                return

            ticket_type: TicketTypeSchema | None = None

            if guild_config.verification_ticket_type_id is not None:
                ticket_type = await self.bot.db_ticket_type.get_ticket_type_by_id(
                    guild_config.verification_ticket_type_id)

            if ticket_type is None:
                ticket_type = await self.create_new_ticket_type(interaction)

                guild_update = GuildUpdate(
                    id=guild_config.id,
                    name=interaction.guild.name,
                    verification_ticket_type_id=ticket_type.id,
                )

                await self.bot.db_guilds.update_guild(guild_update)
            else:
                ticket_type_update = TicketTypeUpdate(
                    id=ticket_type.id,
                    ticket_channel_category_id=self.category_select.values[0].id,
                    moderator_role_id=self.moderator_role_select.values[0].id,
                )

                await self.bot.db_ticket_type.update_ticket_type(ticket_type_update)

            verification_cog: "Verifications | None" = self.bot.get_cog("Verifications")

            if verification_cog is None:
                await interaction.response.send_message(
                    "✅ Verification roles updated successfully.",
                    ephemeral=True,
                )
            else:
                await interaction.response.edit_message(
                    embed=await verification_cog.create_embed_config_view(self.bot, interaction.guild),
                )
        except Exception as e:
            logger.exception(f"Error in EditVerificationTicketTypeModal callback", exc_info=e)
            await interaction.response.send_message(
                "An unexpected error occurred while trying to edit verification ticket type. Please contact an administrator.",
                ephemeral=True,
            )

    async def create_new_ticket_type(self, interaction: Interaction) -> TicketTypeSchema:
        new_ticket_type = TicketTypeCreate(
            guild_id=interaction.guild_id,
            name="Verifications",
            description="Ticket type for verifications requests. Do not edit or delete this ticket type if you are using the verification system.",
            ticket_channel_category_id=self.category_select.values[0].id,
            requires_initial_reason=False,
            moderator_role_id=self.moderator_role_select.values[0].id,
            is_system=True,
        )

        created_ticket_type = await self.bot.db_ticket_type.create_ticket_type(new_ticket_type)

        return created_ticket_type
