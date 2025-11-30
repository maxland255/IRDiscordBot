import logging

from typing import TYPE_CHECKING, Type

from discord import InputTextStyle, Interaction
from discord.ui import DesignerModal, Label, InputText

from bot.database.schemas import EmbedsSchema, EmbedsUpdate, EmbedFieldsSchema

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.embeds import Embeds
    from .edit_embed_view import EditEmbedView

logger = logging.getLogger(__name__)


class EditEmbedModal(DesignerModal):
    def __init__(self, edit_embed_view: "Type[EditEmbedView]", bot: "IRBot", embed_cog: "Embeds", embed: EmbedsSchema,
                 embed_fields: list[EmbedFieldsSchema]):
        super().__init__(
            title="Edit Embed details",
            timeout=600,
        )
        self.edit_embed_view = edit_embed_view
        self.bot = bot
        self.embed_cog = embed_cog
        self.embed = embed
        self.embed_fields = embed_fields

        self.title_input = InputText(
            placeholder="Embed title",
            required=True,
            max_length=256,
            value=self.embed.title,
        )
        self.title_label = Label(
            label="Title",
            item=self.title_input,
        )
        self.add_item(self.title_label)

        self.description_input = InputText(
            placeholder="Embed description",
            style=InputTextStyle.long,
            required=False,
            max_length=4000,
            value=self.embed.description or "",
        )
        self.description_label = Label(
            label="Description",
            item=self.description_input,
        )
        self.add_item(self.description_label)

        self.color_input = InputText(
            placeholder="Embed color in HEX (e.g., #FF5733)",
            required=False,
            max_length=7,
            value=f"#{self.embed.color:06X}" if self.embed.color is not None
            else "",
        )
        self.color_label = Label(
            label="Color",
            item=self.color_input,
        )
        self.add_item(self.color_label)

        self.url_input = InputText(
            placeholder="Embed URL",
            required=False,
            max_length=2048,
            value=self.embed.url or "",
        )
        self.url_label = Label(
            label="URL",
            item=self.url_input,
        )
        self.add_item(self.url_label)

    async def callback(self, interaction: Interaction):
        try:
            title = self.title_input.value
            description = self._value_or_none(self.description_input.value)
            color_value = self._value_or_none(self.color_input.value.lstrip('#'))
            color = int(color_value, 16) if color_value and color_value != "" else None
            url = self._value_or_none(self.url_input.value)

            embed_update = EmbedsUpdate(
                id=self.embed.id,
            )

            if title != self.embed.title:
                embed_update.title = title

            if description != self.embed.description:
                embed_update.description = description

            if color != self.embed.color:
                embed_update.color = color

            if url != self.embed.url:
                embed_update.url = url

            updated_embed = await self.bot.db_embeds.update_embeds(embed_update)

            discord_embed = self.embed_cog.create_embed(updated_embed, self.embed_fields)

            await interaction.response.edit_message(
                embed=discord_embed,
                view=self.edit_embed_view(
                    self.bot,
                    self.embed_cog,
                    updated_embed,
                    self.embed_fields,
                ),
            )
        except Exception as e:
            logger.error(f"Error updating embed from modal", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while updating the embed. Please contact an administrator.",
                ephemeral=True,
            )

    @staticmethod
    def _value_or_none(value: str) -> str | None:
        return value if value != "" else None
