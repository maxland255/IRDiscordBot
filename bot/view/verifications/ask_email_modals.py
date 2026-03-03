import bcrypt
import secrets
import logging

from typing import TYPE_CHECKING
from datetime import datetime, UTC, timedelta

from discord import Interaction, Member
from discord.ui import DesignerModal, InputText, Label

from bot.database.schemas import VerificationsSchema, VerificationsUpdate

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class AskEmailModals(DesignerModal):
    def __init__(self, bot: "IRBot", verification: VerificationsSchema):
        super().__init__(
            title="Email Verification",
            timeout=300,
        )
        self.bot = bot
        self.verification = verification

        self.email_input = InputText(
            required=True,
            placeholder="Email Address",
        )

        self.email_label = Label(
            label="Email",
            item=self.email_input,
        )

        self.name_input = InputText(
            required=False,
            placeholder="Prénom + Nom (Ex: Ada Lovelace)",
            max_length=32,
        )

        self.name_label = Label(
            label="Full Name",
            item=self.name_input,
        )

        self.add_item(self.email_label)
        self.add_item(self.name_label)

    async def callback(self, interaction: Interaction):
        try:
            await interaction.response.defer(ephemeral=True, invisible=False)

            guild_config = await self.bot.db_guilds.get_guild_by_id(interaction.guild_id)

            if guild_config is None or guild_config.deleted_at is not None:
                logger.warning(
                    f"Guild config not found for guild ID {interaction.guild_id} in email verification modal.")
                await interaction.followup.send(
                    "An error occurred while trying to start the email verification process. Please contact an administrator.",
                )
                return

            if self.name_input.value is not None:
                try:
                    member = interaction.user

                    if isinstance(member, Member):
                        await member.edit(nick=self.name_input.value)
                except Exception as e:
                    logger.error(
                        f"Failed to update nickname for user {interaction.user.id} in guild {interaction.guild_id}, Value: {self.name_input.value}",
                        exc_info=e,
                    )

            secret_code = secrets.token_hex(3).upper()

            hashed_code = bcrypt.hashpw(secret_code.encode('utf-8'), bcrypt.gensalt())

            email = self.email_input.value

            email_domain = email.split('@')[-1].lower()

            if email_domain not in guild_config.allowed_email_domains:
                await interaction.followup.send(
                    "The email domain you provided is not allowed for verification. Please use an appropriate email address.",
                )
                return

            update_verification = VerificationsUpdate(
                id=self.verification.id,
                hashed_code=hashed_code,
                code_expires_at=datetime.now(UTC) + timedelta(minutes=15),
                user_email=email,
            )

            # Send the email with the verification code
            result = await self.bot.verification_mail_service.send_verification_code_email(interaction.guild.name,
                                                                                           email, secret_code)

            if not result:
                await interaction.followup.send(
                    "Failed to send verification email. Please try again later.",
                )
                return

            await self.bot.db_verifications.update_verification(update_verification)

            await interaction.followup.send(
                f"A verification code has been sent to {email}. Please check your email and click the button 'Enter Verification Code' to continue the verification process.",
            )
        except Exception as e:
            logger.error(f"Error in email verification modal callback", exc_info=e)
            await interaction.followup.send(
                "An error occurred while processing your email. Please try again later.",
            )
            return
