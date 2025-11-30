import logging

from typing import TYPE_CHECKING, Type

from discord import Interaction, SelectOption
from discord.ui import DesignerModal, Label, Select

from bot.database.schemas import EmbedsSchema, EmbedFieldsSchema

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.embeds import Embeds
    from .edit_embed_view import EditEmbedView

logger = logging.getLogger(__name__)


class DeleteEmbedFieldModal(DesignerModal):
    def __init__(self, edit_embed_view: "Type[EditEmbedView]", bot: "IRBot", embed_cog: "Embeds", embed: EmbedsSchema,
                 embed_fields: list[EmbedFieldsSchema]):
        super().__init__(
            title="Delete Embed Field",
            timeout=600,
        )
        self.edit_embed_view = edit_embed_view
        self.bot = bot
        self.embed_cog = embed_cog
        self.embed = embed
        self.embed_fields = embed_fields

        self.fields_select = Select(
            placeholder="Select a field to delete",
            options=[
                SelectOption(
                    label=field.name[:100],
                    description=field.value[:100] if field.value else "No value",
                    value=str(field.id),
                ) for field in embed_fields
            ],
            min_values=1,
            max_values=1,
        )
        self.fields_label = Label(
            label="Embed Fields",
            item=self.fields_select,
        )
        self.add_item(self.fields_label)

    async def callback(self, interaction: Interaction):
        try:
            embed_field_id = int(self.fields_select.values[0])

            await self.bot.db_embeds.delete_embed_fields_by_id(embed_field_id)

            self.embed_fields = await self.bot.db_embeds.get_all_embed_fields(self.embed.id)

            discord_embed = self.embed_cog.create_embed(self.embed, self.embed_fields)

            await interaction.response.edit_message(
                embed=discord_embed,
                view=self.edit_embed_view(
                    self.bot,
                    self.embed_cog,
                    self.embed,
                    self.embed_fields,
                ),
            )
        except Exception as e:
            logger.error(f"Error deleting embed field: {e}", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while trying to delete the embed field.",
                ephemeral=True,
            )
