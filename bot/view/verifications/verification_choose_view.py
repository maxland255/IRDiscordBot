import logging

from typing import TYPE_CHECKING
from datetime import datetime, timedelta, UTC

from discord import ButtonStyle, Interaction, Embed, Guild, Member
from discord.ui import DesignerView, ActionRow

from bot.view.components import ActionButton
from bot.database.schemas import VerificationStatus, VerificationsUpdate
from bot.exception import VerificationRateLimitError, VerificationNotFound

from .ask_email_modals import AskEmailModals
from .enter_code_modals import EnterCodeModals
from .ticket_verif_result_panel_view import TicketVerifResultPanelView

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.tickets import Tickets
    from bot.cogs.verifications import Verifications

logger = logging.getLogger(__name__)


class VerificationChooseView(DesignerView):
    def __init__(self, bot: "IRBot"):
        super().__init__(timeout=None)

        self.bot = bot

        self.email_verification_button = ActionButton(
            style=ButtonStyle.primary,
            label="Verify via Email",
            custom_id="verification:choose:email",
            on_click=self._verification_by_email,
        )

        self.manual_verification_button = ActionButton(
            label="Request Manual Verification",
            custom_id="verification:choose:manual_verification",
            on_click=self._verification_manual,
        )

        self.enter_verification_code_button = ActionButton(
            label="Enter Verification Code",
            custom_id="verification:choose:enter_code",
            style=ButtonStyle.green,
            on_click=self._verification_enter_code,
        )

        self.action_row = ActionRow(
            self.email_verification_button,
            self.manual_verification_button,
            self.enter_verification_code_button,
        )

        self.add_item(self.action_row)

    async def _verification_by_email(self, interaction: Interaction):
        try:
            # await interaction.response.defer(ephemeral=True, invisible=False)

            try:
                await self.bot.db_verifications.check_email_rate_limit(interaction.guild_id, interaction.user.id)
            except VerificationRateLimitError as e:
                if isinstance(e, VerificationRateLimitError):
                    msg = f"⏳ {e}"
                    if e.retry_after:
                        date = datetime.now(UTC) + timedelta(seconds=e.retry_after)
                        msg += f" Please wait <t:{round(date.timestamp())}:F> seconds before trying again."

                    await interaction.response.send_message(
                        msg,
                        ephemeral=True,
                    )
                    return
            except VerificationNotFound as e:
                logger.error(
                    f"Verification entry not found for user {interaction.user.id} in guild {interaction.guild_id}, Creating a new one.",
                    exc_info=e,
                )
                verification_cog: "Verifications | None" = self.bot.get_cog("Verifications")

                if verification_cog is None:
                    logger.critical(
                        f"Verification cog not found while trying to create a new verification entry for user {interaction.user.id} in guild {interaction.guild_id}.",
                    )
                    await interaction.response.send_message(
                        "An error occurred while trying to start the email verification process. Please contact an administrator.",
                        ephemeral=True,
                    )
                    return

                if not isinstance(interaction.user, Member):
                    logger.critical(
                        f"Interaction user is not a Member while trying to create a new verification entry for user {interaction.user.id} in guild {interaction.guild_id}.",
                    )
                    await interaction.response.send_message(
                        "An error occurred while trying to start the email verification process. Please contact an administrator.",
                        ephemeral=True,
                    )

                await verification_cog.handle_new_member(interaction.user, None)

            verification = await self.bot.db_verifications.get_verification_by_user_id(interaction.guild_id,
                                                                                       interaction.user.id)

            if verification is None or verification.deleted_at is not None:
                await interaction.response.send_message(
                    "An error occurred while trying to start the email verification process. Please contact an administrator.",
                    ephemeral=True,
                )
                return

            if verification.status in [
                VerificationStatus.verified_student,
                VerificationStatus.verified_alumni,
                VerificationStatus.verified_external,
                VerificationStatus.verified_teacher,
            ]:
                await interaction.response.send_message(
                    "✅ Vous êtes déjà vérifié sur ce serveur.",
                    ephemeral=True,
                )
                return
            elif verification.status == VerificationStatus.pending_manual:
                await interaction.response.send_message(
                    "⏳ Votre demande d'accès manuel est déjà en cours de traitement par un administrateur.",
                    ephemeral=True,
                )
                return

            update_verification = VerificationsUpdate(
                id=verification.id,
                status=VerificationStatus.pending_email,
            )

            verification = await self.bot.db_verifications.update_verification(update_verification)

            await interaction.response.send_modal(AskEmailModals(self.bot, verification))
        except Exception as e:
            logger.error(
                f"Error starting email verification for user {interaction.user.id} in guild {interaction.guild_id}",
                exc_info=e,
            )
            if interaction.response.is_done():
                await interaction.followup.send(
                    "An error occurred while trying to start the email verification process. Please contact an administrator.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "An error occurred while trying to start the email verification process. Please contact an administrator.",
                    ephemeral=True,
                )

    async def _verification_manual(self, interaction: Interaction):
        try:
            await interaction.response.defer(ephemeral=True, invisible=False)

            guild_config = await self.bot.db_guilds.get_guild_by_id(interaction.guild_id)

            if guild_config is None or guild_config.deleted_at is not None:
                await interaction.followup.send(
                    "An error occurred while trying to start the manual verification process. Please contact an administrator.",
                    ephemeral=True,
                )
                return

            if guild_config.verification_ticket_type_id is None:
                await interaction.followup.send(
                    "Manual verification is not configured on this server. Please contact an administrator.",
                    ephemeral=True,
                )
                return

            verification = await self.bot.db_verifications.get_verification_by_user_id(interaction.guild_id,
                                                                                       interaction.user.id)

            if verification is None or verification.deleted_at is not None:
                await interaction.followup.send(
                    "An error occurred while trying to start the email verification process. Please contact an administrator.",
                    ephemeral=True,
                )
                return

            if verification.status in [
                VerificationStatus.verified_student,
                VerificationStatus.verified_alumni,
                VerificationStatus.verified_external
            ]:
                await interaction.followup.send(
                    "✅ Vous êtes déjà vérifié sur ce serveur.",
                    ephemeral=True,
                )
                return
            elif verification.status == VerificationStatus.pending_manual and verification.ticket_id is not None:
                await interaction.followup.send(
                    "⏳ Votre demande d'accès manuel est déjà en cours de traitement par un administrateur.",
                    ephemeral=True,
                )
                return

            tickets_cog: "Tickets | None" = self.bot.get_cog("Tickets")

            if tickets_cog is None:
                await interaction.followup.send(
                    "Ticketing system is currently unavailable. Please contact an administrator.",
                    ephemeral=True,
                )
                return

            ticket_channel, tickets = await tickets_cog.create_new_ticket(
                ticket_type=guild_config.verification_ticket_type_id,
                member=interaction.user,
                guild=interaction.guild,
                ticket_management_view=TicketVerifResultPanelView,
                ticket_management_embed=TicketVerifResultPanelView.create_ticket_verif_result_panel_embed(
                    interaction.user),
            )

            update_verification = VerificationsUpdate(
                id=verification.id,
                status=VerificationStatus.pending_manual,
                ticket_id=tickets.id,
            )

            await self.bot.db_verifications.update_verification(update_verification)

            await interaction.followup.send(
                f"✅ Your manual verification request has been submitted. Please describe your situation in the ticket created for you ({ticket_channel.mention}).",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(
                f"Error starting manual verification for user {interaction.user.id} in guild {interaction.guild_id}",
                exc_info=e,
            )
            if interaction.response.is_done():
                await interaction.followup.send(
                    "An error occurred while trying to start the manual verification process. Please contact an administrator.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "An error occurred while trying to start the manual verification process. Please contact an administrator.",
                    ephemeral=True,
                )

    async def _verification_enter_code(self, interaction: Interaction):
        try:
            verification = await self.bot.db_verifications.get_verification_by_user_id(interaction.guild_id,
                                                                                       interaction.user.id)
            if verification is None:
                await interaction.response.send_message(
                    "❌ You do not have a verification entry. Please contact an administrator.",
                    ephemeral=True,
                )
                return

            if verification.status not in [
                VerificationStatus.pending_email,
                VerificationStatus.pending_reverification,
            ]:
                await interaction.response.send_message(
                    "❌ You are not currently in a state that requires entering a verification code.",
                    ephemeral=True,
                )
                return

            await interaction.response.send_modal(EnterCodeModals(self.bot))
        except Exception as e:
            logger.error(
                f"Error entering verification code for user {interaction.user.id} in guild {interaction.guild_id}",
                exc_info=e,
            )
            await interaction.response.send_message(
                "An error occurred while trying to enter the verification code. Please contact an administrator.",
                ephemeral=True,
            )

    @staticmethod
    async def create_panel_embed(guild: Guild) -> Embed:
        panel_embed = Embed(
            title="Verification",
            description=f"Welcome to {guild.name}! Please choose one of the verification methods below to gain access to the server.",
            color=0x3498db,
        )

        return panel_embed
