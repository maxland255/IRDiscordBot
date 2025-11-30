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


class EditAuthorModal(DesignerModal):
    def __init__(self, edit_embed_view: "Type[EditEmbedView]", bot: "IRBot", embed_cog: "Embeds", embed: EmbedsSchema,
                 embed_fields: list[EmbedFieldsSchema]):
        super().__init__(
            title="Edit Embed Author",
            timeout=600,
        )
        self.edit_embed_view = edit_embed_view
        self.bot = bot
        self.embed_cog = embed_cog
        self.embed = embed
        self.embed_fields = embed_fields

        self.author_name_input = InputText(
            placeholder="Author name",
            required=False,
            max_length=256,
            value=embed.author_name or "",
        )
        self.author_name_label = Label(
            label="Author Name",
            item=self.author_name_input,
        )
        self.add_item(self.author_name_label)

        self.author_url_input = InputText(
            placeholder="Author URL",
            required=False,
            max_length=2048,
            value=embed.author_url or "",
        )
        self.author_url_label = Label(
            label="Author URL",
            item=self.author_url_input,
        )
        self.add_item(self.author_url_label)

        self.author_icon_url_input = InputText(
            placeholder="Author Icon URL",
            required=False,
            max_length=2048,
            value=embed.author_icon_url or "",
        )
        self.author_icon_url_label = Label(
            label="Author Icon URL",
            item=self.author_icon_url_input,
        )
        self.add_item(self.author_icon_url_label)

    async def callback(self, interaction: Interaction):
        try:
            author_name = self._value_or_none(self.author_name_input.value)
            author_url = self._value_or_none(self.author_url_input.value)
            author_icon_url = self._value_or_none(self.author_icon_url_input.value)

            embed_update = EmbedsUpdate(
                id=self.embed.id,
            )

            if author_name != self.embed.author_name:
                embed_update.author_name = author_name

            if author_url != self.embed.author_url:
                embed_update.author_url = author_url

            if author_icon_url != self.embed.author_icon_url:
                embed_update.author_icon_url = author_icon_url

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
            logger.error(f"Error updating embed author", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while trying to update the embed author. Please contact an administrator.",
                ephemeral=True,
            )

    @staticmethod
    def _value_or_none(value: str) -> str | None:
        return value if value != "" else None
