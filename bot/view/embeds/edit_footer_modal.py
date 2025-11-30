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


class EditFooterModal(DesignerModal):
    def __init__(self, edit_embed_view: "Type[EditEmbedView]", bot: "IRBot", embed_cog: "Embeds", embed: EmbedsSchema,
                 embed_fields: list[EmbedFieldsSchema]):
        super().__init__(
            title="Edit Embed Footer",
            timeout=600,
        )
        self.edit_embed_view = edit_embed_view
        self.bot = bot
        self.embed_cog = embed_cog
        self.embed = embed
        self.embed_fields = embed_fields

        self.footer_text_input = InputText(
            placeholder="Footer text",
            required=False,
            max_length=2048,
            value=embed.footer_text or "",
        )
        self.footer_text_label = Label(
            label="Footer Text",
            item=self.footer_text_input,
        )
        self.add_item(self.footer_text_label)

        self.footer_icon_url_input = InputText(
            placeholder="Footer Icon URL",
            required=False,
            max_length=2048,
            value=embed.footer_icon_url or "",
        )
        self.footer_icon_url_label = Label(
            label="Footer Icon URL",
            item=self.footer_icon_url_input,
        )
        self.add_item(self.footer_icon_url_label)

    async def callback(self, interaction: Interaction):
        try:
            footer_text = self._value_or_none(self.footer_text_input.value)
            footer_icon_url = self._value_or_none(self.footer_icon_url_input.value)

            embed_update = EmbedsUpdate(
                id=self.embed.id,
            )

            if footer_text != self.embed.footer_text:
                embed_update.footer_text = footer_text

            if footer_icon_url != self.embed.footer_icon_url:
                embed_update.footer_icon_url = footer_icon_url

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
            logger.error("Error updating embed footer", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while updating the embed footer. Please try again later.",
                ephemeral=True,
            )

    @staticmethod
    def _value_or_none(value: str) -> str | None:
        return value if value != "" else None
