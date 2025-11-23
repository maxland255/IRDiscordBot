import logging

from typing import TYPE_CHECKING

from discord import Interaction
from discord.ui import DesignerModal, Label, InputText

from bot.database.schemas import GuildSchema, GuildUpdate

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.verifications import Verifications

logger = logging.getLogger(__name__)


class EditVerificationDelaysModal(DesignerModal):
    def __init__(self, bot: "IRBot", guild_config: GuildSchema):
        super().__init__(
            title="Edit Verification Delays",
        )
        self.bot = bot
        self.guild_config = guild_config

        self.expulsion_delay_input = InputText(
            placeholder="Expulsion Delay in hours",
            min_length=1,
            max_length=2,
            required=True,
            value=str(self.guild_config.new_member_verification_time_limit),
        )
        self.expulsion_delay_label = Label(
            label="Expulsion Delay",
            item=self.expulsion_delay_input,
        )
        self.add_item(self.expulsion_delay_label)

        self.grace_period_input = InputText(
            placeholder="Grace Period in days",
            min_length=1,
            max_length=2,
            required=True,
            value=str(self.guild_config.grace_period_days),
        )
        self.grace_period_label = Label(
            label="Grace Period",
            item=self.grace_period_input,
        )
        self.add_item(self.grace_period_label)

    async def callback(self, interaction: Interaction):
        try:
            guild_update = GuildUpdate(
                id=self.guild_config.id,
                name=interaction.guild.name,
            )

            try:
                new_member_verification_time_limit = int(self.expulsion_delay_input.value)
                grace_period_days = int(self.grace_period_input.value)
            except ValueError:
                await interaction.response.send_message(
                    "Please enter valid integer values for delays.",
                    ephemeral=True,
                )
                return

            if new_member_verification_time_limit <= 0 or grace_period_days < 0:
                await interaction.response.send_message(
                    "Please enter positive values for delays.",
                    ephemeral=True,
                )
                return

            if new_member_verification_time_limit != self.guild_config.new_member_verification_time_limit:
                guild_update.new_member_verification_time_limit = new_member_verification_time_limit

            if grace_period_days != self.guild_config.grace_period_days:
                guild_update.grace_period_days = grace_period_days

            await self.bot.db_guilds.update_guild(guild_update)

            verification_cog: "Verifications | None" = self.bot.get_cog("Verifications")

            if verification_cog is None:
                await interaction.response.send_message(
                    "✅ Verification delays updated successfully.",
                    ephemeral=True,
                )
            else:
                await interaction.response.edit_message(
                    embed=await verification_cog.create_embed_config_view(self.bot, interaction.guild),
                )
        except Exception as e:
            logger.exception(f"Error in EditVerificationDelaysModal callback", exc_info=e)
            await interaction.response.send_message(
                "An unexpected error occurred while trying to update verification delays. Please contact an administrator.",
                ephemeral=True,
            )
