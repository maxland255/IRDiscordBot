import logging

from typing import TYPE_CHECKING, Type

from discord import Interaction, InputTextStyle, SelectOption
from discord.ui import DesignerModal, Label, InputText, Select

from bot.database.schemas import EmbedsSchema, EmbedFieldsCreate, EmbedFieldsSchema, EmbedFieldsUpdate

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.embeds import Embeds
    from .edit_embed_view import EditEmbedView

logger = logging.getLogger(__name__)


class EditEmbedFieldModal(DesignerModal):
    def __init__(self, edit_embed_view: "Type[EditEmbedView]", bot: "IRBot", embed_cog: "Embeds", embed: EmbedsSchema,
                 embed_fields: list[EmbedFieldsSchema], embed_field: EmbedFieldsSchema | None):
        super().__init__(
            title="Edit Embed Field",
            timeout=600,
        )
        self.edit_embed_view = edit_embed_view
        self.bot = bot
        self.embed_cog = embed_cog
        self.embed = embed
        self.embed_fields = embed_fields
        self.embed_field = embed_field

        self.field_name_input = InputText(
            placeholder="Field name",
            required=True,
            max_length=256,
            value=embed_field.name if embed_field is not None else "",
        )
        self.field_name_label = Label(
            label="Field Name",
            item=self.field_name_input,
        )
        self.add_item(self.field_name_label)

        self.field_value_input = InputText(
            placeholder="Field value",
            style=InputTextStyle.long,
            required=True,
            max_length=1024,
            value=embed_field.value if embed_field is not None else "",
        )
        self.field_value_label = Label(
            label="Field Value",
            item=self.field_value_input,
        )
        self.add_item(self.field_value_label)

        self.field_inline_select = Select(
            placeholder="Field is Inline?",
            options=[
                SelectOption(
                    label="Yes",
                    value="true",
                    default=embed_field.inline if embed_field is not None else True,
                ),
                SelectOption(
                    label="No",
                    value="false",
                    default=not embed_field.inline if embed_field is not None else False,
                ),
            ],
            min_values=1,
            max_values=1,
            required=True,
        )
        self.field_inline_label = Label(
            label="Field Inline",
            item=self.field_inline_select,
        )
        self.add_item(self.field_inline_label)

    async def callback(self, interaction: Interaction):
        try:
            field_name = self.field_name_input.value
            field_value = self.field_value_input.value
            field_inline = self.field_inline_select.values[0] == "true"

            if self.embed_field is None:
                embed_field = EmbedFieldsCreate(
                    embed_id=self.embed.id,
                    name=field_name,
                    value=field_value,
                    inline=field_inline,
                    position=await self.bot.db_embeds.get_next_position(self.embed.id),
                )

                embed_field = await self.bot.db_embeds.create_embed_fields(embed_field)

                self.embed_fields.append(embed_field)

                discord_embed = self.embed_cog.create_embed(self.embed, self.embed_fields)
            else:
                embed_field_update = EmbedFieldsUpdate(
                    id=self.embed_field.id,
                )

                if field_name != self.embed_field.name:
                    embed_field_update.name = field_name

                if field_value != self.embed_field.value:
                    embed_field_update.value = field_value

                if field_inline != self.embed_field.inline:
                    embed_field_update.inline = field_inline

                await self.bot.db_embeds.update_embed_fields(embed_field_update)

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
            logger.error(f"Error editing embed field", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while trying to edit the embed field. Please contact an administrator.",
                ephemeral=True,
            )
