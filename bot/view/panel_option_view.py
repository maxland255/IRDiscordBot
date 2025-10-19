import logging

from typing import TYPE_CHECKING
from datetime import datetime, UTC

from discord import Role, Interaction, ComponentType, Color, Embed
from discord.ui import Modal, InputText, Select

from bot.database.schemas import RoleOptionsCreate, RoleOptionsSchema, RoleOptionsUpdate

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class PanelOptionView(Modal):
    def __init__(self, panel_id: int, bot: "IRBot", option: RoleOptionsSchema | None = None):
        super().__init__(title="Panel Option Configuration")
        self.panel_id = panel_id
        self.bot = bot
        self.option = option

        self.role_select = Select(
            select_type=ComponentType.role_select,
            label="Select a Role",
            placeholder="Choose a role for this option",
            required=self.option is None,
        )
        self.label_input = InputText(
            label="Label",
            placeholder="Enter the label for the option",
            max_length=100,
            value=self.option.label if self.option is not None else None,
        )
        self.description_input = InputText(
            label="Description",
            placeholder="Enter the description for the option",
            required=False,
            max_length=100,
            value=self.option.description if self.option is not None and self.option.description else "",
        )
        self.emoji_input = InputText(
            label="Emoji",
            placeholder="Enter the emoji for the option",
            required=False,
            max_length=2,
            value=self.option.emoji if self.option is not None and self.option.emoji else "",
        )

        if self.option is None:
            self.add_item(self.role_select)
        self.add_item(self.label_input)
        self.add_item(self.description_input)
        self.add_item(self.emoji_input)

    async def callback(self, interaction: Interaction):
        try:
            role_selected: list[Role] = self.role_select.values
            label = self.label_input.value
            description = self.description_input.value
            emoji = self.emoji_input.value

            if self.option is not None:
                try:
                    role_option = await self.update_role_option(label=label, description=description, emoji=emoji)
                except Exception as e:
                    logger.error(f"Error updating role option: {e}")
                    await interaction.respond("An error occurred while updating the role option.", ephemeral=True)
                    return
            else:
                if not role_selected:
                    await interaction.respond("You must select a role for this option.", ephemeral=True)
                    return

                role = role_selected[0]

                role_option = await self.create_role_option(
                    role=role,
                    label=label,
                    description=description,
                    emoji=emoji,
                )

            role_options_embed = self.print_role_options(role_option)

            await interaction.respond(embed=role_options_embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in PanelOptionView callback: {e}")
            await interaction.respond("An error occurred while processing your request.", ephemeral=True)

    async def create_role_option(self, role: Role, label: str, description: str | None,
                                 emoji: str | None) -> RoleOptionsSchema:
        new_role_panel_option = RoleOptionsCreate(
            panel_id=self.panel_id,
            role_id=role.id,
            label=label,
            description=description if description else None,
            emoji=emoji if emoji else None,
        )

        role_option = await self.bot.db_role_options.create_role_options(new_role_panel_option)

        return role_option

    async def update_role_option(self, label: str | None, description: str | None,
                                 emoji: str | None) -> RoleOptionsSchema:
        role_option_update = RoleOptionsUpdate(
            id=self.option.id,
        )

        if label is not None and label != "":
            role_option_update.label = label

        if description is not None and description != "":
            role_option_update.description = description

        if emoji is not None and emoji != "":
            role_option_update.emoji = emoji

        updated_role_option = await self.bot.db_role_options.update_role_options(role_option_update)

        return updated_role_option

    def print_role_options(self, option: RoleOptionsSchema) -> Embed:
        options_embed = Embed(
            title="Role Options",
            colour=Color.green(),
            timestamp=datetime.now(UTC),
        )

        options_embed.add_field(
            name=option.label,
            value=f"Role: <@&{option.role_id}>\n"
                  f"Description: {option.description if option.description else 'No description'}\n"
                  f"Emoji: {option.emoji if option.emoji else 'No emoji'}",
            inline=False,
        )

        return options_embed
