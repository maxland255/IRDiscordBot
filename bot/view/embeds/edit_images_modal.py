import logging

from typing import TYPE_CHECKING, Type

from discord import Interaction
from discord.ui import DesignerModal, Label, InputText

from bot.database.schemas import EmbedsSchema, EmbedsUpdate, EmbedFieldsSchema

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.embeds import Embeds
    from .edit_embed_view import EditEmbedView

logger = logging.getLogger(__name__)


class EditImagesModal(DesignerModal):
    def __init__(self, edit_embed_view: "Type[EditEmbedView]", bot: "IRBot", embed_cog: "Embeds", embed: EmbedsSchema,
                 embed_fields: list[EmbedFieldsSchema]):
        super().__init__(
            title="Edit Embed Images",
            timeout=600,
        )
        self.edit_embed_view = edit_embed_view
        self.bot = bot
        self.embed_cog = embed_cog
        self.embed = embed
        self.embed_fields = embed_fields

        self.image_url_input = InputText(
            placeholder="Image URL",
            required=False,
            max_length=2048,
            value=embed.image_url or "",
        )
        self.image_url_label = Label(
            label="Image URL",
            item=self.image_url_input,
        )
        self.add_item(self.image_url_label)

        self.thumbnail_url_input = InputText(
            placeholder="Thumbnail URL",
            required=False,
            max_length=2048,
            value=embed.thumbnail_url or "",
        )
        self.thumbnail_url_label = Label(
            label="Thumbnail URL",
            item=self.thumbnail_url_input,
        )
        self.add_item(self.thumbnail_url_label)

    async def callback(self, interaction: Interaction):
        try:
            image_url = self._value_or_none(self.image_url_input.value)
            thumbnail_url = self._value_or_none(self.thumbnail_url_input.value)

            embed_update = EmbedsUpdate(
                id=self.embed.id,
            )

            if image_url != self.embed.image_url:
                embed_update.image_url = image_url

            if thumbnail_url != self.embed.thumbnail_url:
                embed_update.thumbnail_url = thumbnail_url

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
            logger.error("Error updating embed images", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while trying to update the embed images. Please contact an administrator.",
                ephemeral=True,
            )

    @staticmethod
    def _value_or_none(value: str) -> str | None:
        return value if value != "" else None
