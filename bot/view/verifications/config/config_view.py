import logging

from typing import TYPE_CHECKING
from functools import partial

from discord import ButtonStyle, Interaction
from discord.ui import DesignerView, ActionRow

from bot.view.components import ActionButton
from bot.database.schemas import TicketTypeSchema

from .edit_roles_modals import EditVerificationRolesModal
from .edit_delays_modals import EditVerificationDelaysModal
from .edit_ticket_type_modals import EditVerificationTicketTypeModal
from .edit_domains_modals import EditVerificationDomainsModal

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class ConfigView(DesignerView):
    def __init__(self, bot: "IRBot"):
        super().__init__(timeout=300)
        self.bot = bot

        self.edit_role_button = ActionButton(
            label="Edit Roles",
            style=ButtonStyle.secondary,
            on_click=self.edit_verification_roles,
            custom_id="config:edit_roles",
        )

        self.edit_delays_button = ActionButton(
            label="Edit Delays",
            style=ButtonStyle.secondary,
            on_click=self.edit_verification_delays,
            custom_id="config:edit_delays",
        )

        self.edit_ticket_type_button = ActionButton(
            label="Edit Ticket Type",
            style=ButtonStyle.secondary,
            on_click=self.edit_verification_ticket_type,
            custom_id="config:edit_ticket_type",
        )

        self.add_domain_button = ActionButton(
            label="Add an email domain",
            style=ButtonStyle.secondary,
            on_click=partial(self.edit_email_domain, add=True),
            custom_id="config:add_email_domain",
        )

        self.remove_domain_button = ActionButton(
            label="Remove an email domain",
            style=ButtonStyle.secondary,
            on_click=partial(self.edit_email_domain, add=False),
            custom_id="config:remove_email_domain",
        )

        self.action_row = ActionRow(
            self.edit_role_button,
            self.edit_delays_button,
            self.edit_ticket_type_button,
            self.add_domain_button,
            self.remove_domain_button,
        )

        self.add_item(self.action_row)

    async def edit_verification_roles(self, interaction: Interaction):
        try:
            guild_config = await self.bot.db_guilds.get_guild_by_id(interaction.guild_id)

            if guild_config is None:
                await interaction.response.send_message(
                    "An error occurred while trying to edit verification roles. No guild configuration found.",
                    ephemeral=True,
                )
                return

            await interaction.response.send_modal(
                EditVerificationRolesModal(self.bot, guild_config)
            )
        except Exception as e:
            logger.exception(f"Error in edit_verification_roles", exc_info=e)
            await interaction.response.send_message(
                "An unexpected error occurred while trying to edit verification roles. Please contact an administrator.",
                ephemeral=True,
            )

    async def edit_verification_delays(self, interaction: Interaction):
        try:
            guild_config = await self.bot.db_guilds.get_guild_by_id(interaction.guild_id)

            if guild_config is None:
                await interaction.response.send_message(
                    "An error occurred while trying to edit verification roles. No guild configuration found.",
                    ephemeral=True,
                )
                return

            await interaction.response.send_modal(
                EditVerificationDelaysModal(self.bot, guild_config)
            )
        except Exception as e:
            logger.exception(f"Error in edit_verification_delays", exc_info=e)
            await interaction.response.send_message(
                "An unexpected error occurred while trying to edit verification delays. Please contact an administrator.",
                ephemeral=True,
            )

    async def edit_verification_ticket_type(self, interaction: Interaction):
        try:
            guild_config = await self.bot.db_guilds.get_guild_by_id(interaction.guild_id)

            if guild_config is None:
                await interaction.response.send_message(
                    "An error occurred while trying to edit verification roles. No guild configuration found.",
                    ephemeral=True,
                )
                return

            ticket_type: TicketTypeSchema | None = None

            if guild_config.verification_ticket_type_id is not None:
                ticket_type = await self.bot.db_ticket_type.get_ticket_type_by_id(
                    guild_config.verification_ticket_type_id)

            await interaction.response.send_modal(
                EditVerificationTicketTypeModal(self.bot, guild_config, ticket_type)
            )
        except Exception as e:
            logger.exception(f"Error in edit_verification_ticket_type", exc_info=e)
            await interaction.response.send_message(
                "An unexpected error occurred while trying to edit verification ticket type. Please contact an administrator.",
                ephemeral=True,
            )

    async def edit_email_domain(self, interaction: Interaction, add: bool):
        try:
            guild_config = await self.bot.db_guilds.get_guild_by_id(interaction.guild_id)

            if guild_config is None:
                await interaction.response.send_message(
                    "An error occurred while trying to edit verification roles. No guild configuration found.",
                    ephemeral=True,
                )
                return

            if add and len(guild_config.allowed_email_domains) >= 20:
                await interaction.response.send_message(
                    "You have reached the maximum number of allowed email domains (20). Please remove a domain before adding a new one.",
                    ephemeral=True,
                )
                return
            elif not add and len(guild_config.allowed_email_domains) == 0:
                await interaction.response.send_message(
                    "There are no email domains to remove.",
                    ephemeral=True,
                )
                return

            await interaction.response.send_modal(
                EditVerificationDomainsModal(self.bot, guild_config, add)
            )
        except Exception as e:
            logger.exception(f"Error in edit_email_domain", exc_info=e)
            await interaction.response.send_message(
                "An unexpected error occurred while trying to edit verification email domains. Please contact an administrator.",
                ephemeral=True,
            )
