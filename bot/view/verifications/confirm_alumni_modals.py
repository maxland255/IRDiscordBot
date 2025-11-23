import logging
from typing import TYPE_CHECKING

from discord.ui import DesignerModal, TextDisplay

from bot.database.schemas import VerificationsSchema, VerificationStatus

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.verifications import Verifications

logger = logging.getLogger(__name__)


class ConfirmAlumniModals(DesignerModal):
    def __init__(self, bot: "IRBot", verification: VerificationsSchema):
        super().__init__(
            title="Confirm Alumni Status",
            timeout=300,
        )
        self.bot = bot
        self.verification = verification

        self.add_item(
            TextDisplay(
                content="Si vous décidé de confirmer votre statut d'ancien élève, vous perdrez l'accès aux canaux réservés aux étudiants actuels et à certains avantages associés. Veuillez confirmer que vous comprenez cette action.",
            )
        )

    async def callback(self, interaction):
        try:
            verification_cog: "Verifications | None" = self.bot.get_cog("Verifications")
            if verification_cog is None:
                await interaction.response.send_message(
                    "❌ An error occurred while processing your request. Please try again later.",
                    ephemeral=True,
                )
                return

            await verification_cog.set_member_status(self.bot, interaction.guild, interaction.user, self.verification,
                                                     VerificationStatus.verified_alumni)

            await interaction.response.send_message(
                "✅ You have been successfully reverified as an Alumni.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error in ConfirmAlumniModals callback", exc_info=e)
            await interaction.response.send_message(
                "❌ An error occurred while processing your request. Please try again later.",
                ephemeral=True,
            )
