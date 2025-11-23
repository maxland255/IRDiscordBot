import logging

from typing import TYPE_CHECKING

from discord import SelectOption, Interaction
from discord.ui import DesignerModal, Label, Select, InputText

from bot.database.schemas import GuildSchema, GuildUpdate

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.verifications import Verifications

logger = logging.getLogger(__name__)


class EditVerificationDomainsModal(DesignerModal):
    def __init__(self, bot: "IRBot", guild_config: GuildSchema, add_domain: bool = True):
        super().__init__(title="Edit Verification Domains")
        self.bot = bot
        self.guild_config = guild_config
        self.add_domain = add_domain

        if self.add_domain:
            self.domain_input = InputText(
                placeholder="Enter a domain to add (e.g., example.com)",
                required=True,
            )
            self.domain_label = Label(
                label="Add Domain",
                item=self.domain_input,
            )
            self.add_item(self.domain_label)
        else:
            self.domain_select = Select(
                placeholder="Select a domain to remove",
                required=True,
                min_values=1,
                options=[
                    SelectOption(
                        label=domain,
                        value=domain,
                    )
                    for domain in guild_config.allowed_email_domains
                ],
            )
            self.domain_label = Label(
                label="Remove Domain",
                item=self.domain_select,
            )
            self.add_item(self.domain_label)

    async def callback(self, interaction: Interaction):
        try:
            allowed_domains = set(self.guild_config.allowed_email_domains)

            if self.add_domain:
                allowed_domains.add(self.domain_input.value)
            else:
                for domain in self.domain_select.values:
                    allowed_domains.discard(domain)

            guild_update = GuildUpdate(
                id=self.guild_config.id,
                name=interaction.guild.name,
                allowed_email_domains=list(allowed_domains),
            )

            await self.bot.db_guilds.update_guild(guild_update)

            verification_cog: "Verifications | None" = self.bot.get_cog("Verifications")

            if verification_cog is None:
                await interaction.response.send_message(
                    "✅ Verification domains updated successfully.",
                    ephemeral=True,
                )
            else:
                await interaction.response.edit_message(
                    embed=await verification_cog.create_embed_config_view(self.bot, interaction.guild),
                )
        except Exception as e:
            logger.exception(f"Error in EditVerificationDomainsModal callback", exc_info=e)
            await interaction.response.send_message(
                "An unexpected error occurred while updating verification domains. Please contact an administrator.",
                ephemeral=True,
            )
