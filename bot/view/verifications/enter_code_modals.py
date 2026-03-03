import logging
import bcrypt

from typing import TYPE_CHECKING
from datetime import datetime, UTC

from discord import Interaction
from discord.ui import DesignerModal, Label, InputText, TextDisplay

from bot.database.schemas import VerificationStatus

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.verifications import Verifications

logger = logging.getLogger(__name__)


class EnterCodeModals(DesignerModal):
    def __init__(self, bot: "IRBot"):
        super().__init__(
            title="Enter Verification Code",
            timeout=1000,
        )
        self.bot = bot

        self.add_item(
            TextDisplay(
                content="A verification code has been sent to your email. Please enter it below to complete the verification process.",
            )
        )
        self.add_item(
            TextDisplay(
                content="If you did not receive the email, please check your spam folder or request a new code by canceling and starting the verification process again.",
            )
        )
        self.add_item(
            TextDisplay(
                content="If you close this modal, you can reopen it by clicking the 'Enter Verification Code' button again or use the command `/verify code`.",
            )
        )

        self.code_input = InputText(
            required=True,
            max_length=6,
            placeholder="123456",
        )
        self.code_label = Label(
            label="Verification Code",
            item=self.code_input,
        )
        self.add_item(self.code_label)

    async def callback(self, interaction: Interaction):
        try:
            await interaction.response.defer(ephemeral=True, invisible=False)

            verification = await self.bot.db_verifications.get_verification_by_user_id(interaction.guild_id,
                                                                                       interaction.user.id)

            if verification is None or verification.deleted_at is not None:
                await interaction.followup.send(
                    "An error occurred while processing your verification code. Please contact an administrator.",
                )
                return

            entered_code = self.code_input.value.upper()

            code_expires_at = verification.code_expires_at
            code_expires_at = code_expires_at.replace(tzinfo=UTC)

            if code_expires_at < datetime.now(UTC):
                await interaction.followup.send(
                    "Your verification code has expired. Please start the verification process again to receive a new code.",
                )
                return

            result = bcrypt.checkpw(entered_code.encode('utf-8'), verification.hashed_code.encode('utf-8'))

            if result:
                try:
                    verification_cogs: "Verifications | None" = self.bot.get_cog("Verifications")

                    if verification_cogs is None:
                        raise Exception("Verifications cog not found.")

                    await verification_cogs.set_member_status(self.bot, interaction.guild, interaction.user,
                                                              verification, VerificationStatus.verified_student)
                except ValueError as e:
                    logger.error(
                        f"ValueError in EnterCodeModals callback for user {interaction.user.id} in guild {interaction.guild_id}.",
                        exc_info=e)
                    await interaction.followup.send(
                        "An error occurred while updating your verification status. Please contact an administrator.",
                    )
                    return
            else:
                await interaction.followup.send(
                    "The verification code you entered is incorrect. Please try again.",
                )
                return

            await interaction.followup.send(
                "Your email has been successfully verified! You now have access to the server.",
            )
        except Exception as e:
            logger.error(
                f"Error in EnterCodeModals callback for user {interaction.user.id} in guild {interaction.guild_id}.",
                exc_info=e)
            await interaction.followup.send(
                "An error occurred while processing your verification code. Please try again later or contact an administrator.",
            )
