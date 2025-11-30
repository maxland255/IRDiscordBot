import logging

from typing import TYPE_CHECKING

from discord import SelectOption, ButtonStyle, Interaction
from discord.ui import DesignerView, ActionRow, Select

from bot.database.schemas import EmbedsSchema, EmbedFieldsSchema
from bot.view.components import ActionButton

from .edit_embed_modal import EditEmbedModal
from .edit_author_modal import EditAuthorModal
from .edit_images_modal import EditImagesModal
from .edit_footer_modal import EditFooterModal
from .edit_embed_field_modal import EditEmbedFieldModal
from .delete_embed_field_modal import DeleteEmbedFieldModal

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.embeds import Embeds

logger = logging.getLogger(__name__)


class EditEmbedView(DesignerView):
    def __init__(self, bot: "IRBot", embed_cog: "Embeds", embed: EmbedsSchema, embed_field: list[EmbedFieldsSchema]):
        super().__init__(
            timeout=600,
        )

        self.bot = bot
        self.embed_cog = embed_cog
        self.embed = embed
        self.embed_field = embed_field

        self.edit_embed_button = ActionButton(
            label="Edit Embed",
            custom_id="embed:edit:edit_embed",
            on_click=self._button_callback,
        )

        self.edit_author_button = ActionButton(
            label="Edit Author",
            custom_id="embed:edit:edit_author",
            on_click=self._button_callback,
        )

        self.edit_images_button = ActionButton(
            label="Edit Images",
            custom_id="embed:edit:edit_images",
            on_click=self._button_callback,
        )

        self.edit_footer_button = ActionButton(
            label="Edit Footer",
            custom_id="embed:edit:edit_footer",
            on_click=self._button_callback,
        )

        self.delete_field_button = ActionButton(
            label="Delete Field",
            custom_id="embed:edit:delete_field",
            style=ButtonStyle.danger,
            on_click=self._button_callback,
        )

        self.select_option = [
            SelectOption(
                label=field.name[:100],
                description=field.value[:100] if field.value else None,
                value=str(field.id),
            )
            for field in self.embed_field
        ]

        if len(self.select_option) < 25:
            self.select_option.append(
                SelectOption(
                    label="Create New Field",
                    description="Create a new embed field",
                    value="create_new_field",
                )
            )

        self.select_field_button = Select(
            placeholder="Select a field to edit or create",
            options=self.select_option,
            custom_id="embed:edit:select_field",
            min_values=1,
            max_values=1,
        )
        self.select_field_button.callback = self._handle_select_field

        self.action_row = ActionRow(
            self.edit_embed_button,
            self.edit_author_button,
            self.edit_images_button,
            self.edit_footer_button,
            self.delete_field_button,
        )
        self.add_item(self.action_row)
        self.add_item(ActionRow(
            self.select_field_button,
        ))

    async def _button_callback(self, interaction: Interaction):
        try:
            button_id = interaction.custom_id

            match button_id:
                case "embed:edit:edit_embed":
                    await interaction.response.send_modal(
                        EditEmbedModal(
                            EditEmbedView,
                            self.bot,
                            self.embed_cog,
                            self.embed,
                            self.embed_field,
                        )
                    )
                case "embed:edit:edit_author":
                    await interaction.response.send_modal(
                        EditAuthorModal(
                            EditEmbedView,
                            self.bot,
                            self.embed_cog,
                            self.embed,
                            self.embed_field,
                        )
                    )
                case "embed:edit:edit_images":
                    await interaction.response.send_modal(
                        EditImagesModal(
                            EditEmbedView,
                            self.bot,
                            self.embed_cog,
                            self.embed,
                            self.embed_field,
                        )
                    )
                case "embed:edit:edit_footer":
                    await interaction.response.send_modal(
                        EditFooterModal(
                            EditEmbedView,
                            self.bot,
                            self.embed_cog,
                            self.embed,
                            self.embed_field,
                        )
                    )
                case "embed:edit:delete_field":
                    await interaction.response.send_modal(
                        DeleteEmbedFieldModal(
                            EditEmbedView,
                            self.bot,
                            self.embed_cog,
                            self.embed,
                            self.embed_field,
                        )
                    )
                case _:
                    await interaction.response.send_message(
                        "Unknown action. Please contact an administrator.",
                        ephemeral=True,
                    )
        except Exception as e:
            logger.error(f"Error handling button interaction", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while processing your request. Please contact an administrator.",
                ephemeral=True,
            )

    async def _handle_select_field(self, interaction: Interaction):
        selected_value = self.select_field_button.values[0]

        if selected_value == "create_new_field":
            await interaction.response.send_modal(
                EditEmbedFieldModal(
                    EditEmbedView,
                    self.bot,
                    self.embed_cog,
                    self.embed,
                    self.embed_field,
                    None,
                )
            )
        else:
            embed_field = await self.bot.db_embeds.get_specific_embed_field(selected_value)

            if embed_field is None:
                await interaction.response.send_message(
                    "Selected embed field not found. Please try again.",
                    ephemeral=True,
                )
                return

            await interaction.response.send_modal(
                EditEmbedFieldModal(
                    EditEmbedView,
                    self.bot,
                    self.embed_cog,
                    self.embed,
                    self.embed_field,
                    embed_field,
                )
            )
