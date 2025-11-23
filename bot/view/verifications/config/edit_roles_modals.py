import logging

from typing import TYPE_CHECKING

from discord import ComponentType, Interaction
from discord.ui import DesignerModal, Label, Select

from bot.database.schemas import GuildSchema, GuildUpdate

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.verifications import Verifications

logger = logging.getLogger(__name__)


class EditVerificationRolesModal(DesignerModal):
    def __init__(self, bot: "IRBot", guild_config: GuildSchema):
        super().__init__(
            title="Edit Verification Roles",
        )
        self.bot = bot
        self.guild_config = guild_config

        # Verified Role Select
        self.verified_role_select = Select(
            placeholder="Select the Verified Role",
            min_values=0,
            max_values=1,
            select_type=ComponentType.role_select,
            required=False,
        )
        if self.guild_config.verified_role_id is not None:
            self.verified_role_select.add_default_value(id=self.guild_config.verified_role_id)

        self.verified_role_label = Label(
            label="Verified Role",
            item=self.verified_role_select,
        )
        self.add_item(self.verified_role_label)

        # Student Role Select
        self.student_role_select = Select(
            placeholder="Select the Verified Student Role",
            min_values=1,
            max_values=1,
            select_type=ComponentType.role_select,
            required=True,
        )
        if self.guild_config.student_role_id is not None:
            self.student_role_select.add_default_value(id=self.guild_config.student_role_id)

        self.student_role_label = Label(
            label="Student verified Role",
            item=self.student_role_select,
        )
        self.add_item(self.student_role_label)

        # Alumni Role Select
        self.alumni_role_select = Select(
            placeholder="Select the Verified Alumni Role",
            min_values=1,
            max_values=1,
            select_type=ComponentType.role_select,
            required=True,
        )
        if self.guild_config.alumni_role_id is not None:
            self.alumni_role_select.add_default_value(id=self.guild_config.alumni_role_id)

        self.alumni_role_label = Label(
            label="Alumni verified Role",
            item=self.alumni_role_select,
        )
        self.add_item(self.alumni_role_label)

        # External Role Select
        self.external_role_select = Select(
            placeholder="Select the Verified External Role",
            min_values=1,
            max_values=1,
            select_type=ComponentType.role_select,
            required=True,
        )
        if self.guild_config.external_role_id is not None:
            self.external_role_select.add_default_value(id=self.guild_config.external_role_id)

        self.external_role_label = Label(
            label="External verified Role",
            item=self.external_role_select,
        )
        self.add_item(self.external_role_label)

        # Teacher Role Select
        self.teacher_role_select = Select(
            placeholder="Select the Verified Teacher Role",
            min_values=1,
            max_values=1,
            select_type=ComponentType.role_select,
            required=True,
        )
        if self.guild_config.teacher_role_id is not None:
            self.teacher_role_select.add_default_value(id=self.guild_config.teacher_role_id)

        self.teacher_role_label = Label(
            label="Teacher verified Role",
            item=self.teacher_role_select,
        )
        self.add_item(self.teacher_role_label)

    async def callback(self, interaction: Interaction):
        try:
            guild_update = GuildUpdate(
                id=self.guild_config.id,
                name=interaction.guild.name,
            )

            verified_role_select = self.verified_role_select.values[0].id if self.verified_role_select.values else None
            student_role_select = self.student_role_select.values[0].id
            alumni_role_select = self.alumni_role_select.values[0].id
            external_role_select = self.external_role_select.values[0].id
            teacher_role_select = self.teacher_role_select.values[0].id

            if verified_role_select != self.guild_config.verified_role_id:
                guild_update.verified_role_id = verified_role_select

            if student_role_select != self.guild_config.student_role_id:
                guild_update.student_role_id = student_role_select

            if alumni_role_select != self.guild_config.alumni_role_id:
                guild_update.alumni_role_id = alumni_role_select

            if external_role_select != self.guild_config.external_role_id:
                guild_update.external_role_id = external_role_select

            if teacher_role_select != self.guild_config.teacher_role_id:
                guild_update.teacher_role_id = teacher_role_select

            await self.bot.db_guilds.update_guild(guild_update)

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
            logger.exception(f"Error in EditVerificationRolesModal callback", exc_info=e)
            await interaction.response.send_message(
                "An unexpected error occurred while updating verification roles. Please contact an administrator.",
                ephemeral=True,
            )
