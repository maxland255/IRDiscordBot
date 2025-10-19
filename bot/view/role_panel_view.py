from typing import TYPE_CHECKING

from discord import Interaction, Member
from discord.ui import Select, View

from bot.database.schemas import RolePanelSchema
from bot.utils.get_role import get_role

if TYPE_CHECKING:
    from bot.main import IRBot


class RolePanelSelect(Select):
    def __init__(self, panel: RolePanelSchema, bot: "IRBot", preview: bool = False):
        super().__init__(
            placeholder="Choose your role...",
            min_values=0,
            max_values=len(panel.options) if panel.multiple_choose else 1,
            custom_id=f"role_panel:{panel.id}",
        )
        self.bot = bot
        self.preview = preview

        for option in panel.options:
            self.add_option(
                label=option.label,
                description=option.description,
                emoji=option.emoji,
                value=f"role_option:{option.id}:{option.role_id}",
            )

    async def callback(self, interaction: Interaction):
        panel_id = int(self.custom_id.split(":")[1])

        panel = await self.bot.db_role_panels.get_roles_panel_by_id(panel_id)

        if panel is None:
            await interaction.response.send_message("An error occurred. Panel not found.", ephemeral=True)
            return

        if panel.deleted_at is not None:
            await interaction.response.send_message("This panel has been deleted. Please contact an administrator.",
                                                    ephemeral=True)
            return

        if self.preview:
            await interaction.response.send_message("This is a preview panel. No changes have been made.",
                                                    ephemeral=True)
            return

        member: Member = interaction.user

        managed_roles_ids = [option.role_id for option in panel.options]
        current_roles_ids = [role.id for role in member.roles]
        selected_roles_ids = [int(value.split(":")[2]) for value in self.values]

        await interaction.response.send_message("Updating your roles...", ephemeral=True)

        remove_roles_ids = [role_id for role_id in managed_roles_ids if
                            role_id in current_roles_ids and role_id not in selected_roles_ids]
        add_roles_ids = [role_id for role_id in selected_roles_ids if role_id not in current_roles_ids]

        for role_id in remove_roles_ids:
            role = await get_role(interaction.guild, role_id)
            if role is not None:
                await member.remove_roles(role, reason="Role Panel Selection")

        for role_id in add_roles_ids:
            role = await get_role(interaction.guild, role_id)
            if role is not None:
                await member.add_roles(role, reason="Role Panel Selection")

        response_message = "Your roles have been updated."
        if add_roles_ids:
            response_message += f"\nAdded roles: {', '.join([f"<@&{rid}>" for rid in add_roles_ids])}."

        if remove_roles_ids:
            response_message += f"\nRemoved roles: {', '.join([f"<@&{rid}>" for rid in remove_roles_ids])}."

        await interaction.followup.send(response_message, ephemeral=True)


class RolePanelView(View):
    def __init__(self, panel: RolePanelSchema, bot: "IRBot", preview: bool = False):
        super().__init__(
            timeout=180 if preview else None,
        )
        self.panel = panel
        self.bot = bot
        self.add_item(
            RolePanelSelect(panel=self.panel, bot=self.bot, preview=preview)
        )
