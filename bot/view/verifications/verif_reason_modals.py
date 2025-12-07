import logging

from typing import TYPE_CHECKING, Literal

from discord import InputTextStyle, Interaction, Member, Role, SelectOption
from discord.ui import DesignerModal, Label, InputText, TextDisplay, Select

from bot.database.schemas import TicketsSchema, VerificationsUpdate, VerificationStatus
from bot.cogs.moderation import Moderation

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.tickets import Tickets
    from bot.cogs.verifications import Verifications

logger = logging.getLogger(__name__)


class VerifReasonModals(DesignerModal):
    def __init__(
            self,
            bot: "IRBot",
            ticket: TicketsSchema,
            action: Literal["verified_alumni", "verified_external", "kick_user", "other"],
    ):
        super().__init__(
            title="Verification Reason",
            timeout=300,
        )
        self.bot = bot
        self.ticket = ticket
        self.action = action

        if self.action != "other":
            self.action_text = TextDisplay(
                content=f"Selected action: {self.action}",
            )
            self.add_item(self.action_text)
        else:
            self.action_select = Select(
                placeholder="Select action",
                options=[
                    SelectOption(
                        label="Verify Student",
                        value=VerificationStatus.verified_student.value,
                    ),
                    SelectOption(
                        label="Verify Alumni",
                        value=VerificationStatus.verified_alumni.value,
                    ),
                    SelectOption(
                        label="Verify External",
                        value=VerificationStatus.verified_external.value,
                    ),
                    SelectOption(
                        label="Verify Teacher",
                        value=VerificationStatus.verified_teacher.value,
                    ),
                ]
            )
            self.action_label = Label(
                label="Action",
                item=self.action_select,
            )
            self.add_item(self.action_label)

        self.reason_input = InputText(
            placeholder="Please provide your reason for manual verification here.",
            required=True,
            style=InputTextStyle.long,
        )

        self.reason_label = Label(
            label="Reason",
            item=self.reason_input,
        )

        self.add_item(self.reason_label)

    async def callback(self, interaction: Interaction):
        try:
            moderator_role = await interaction.guild.get_or_fetch(Role, self.ticket.ticket_type.moderator_role_id)

            if moderator_role is None and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "You do not have permission to perform this action.",
                    ephemeral=True,
                )
                return

            if moderator_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "You do not have permission to perform this action.",
                    ephemeral=True,
                )
                return

            reason = self.reason_input.value
            member = await interaction.guild.get_or_fetch(Member, self.ticket.member_id)

            if member is None:
                await interaction.response.send_message(
                    "An error occurred while trying to process your request. Member not found in the guild.",
                    ephemeral=True,
                )
                return

            verification = await self.bot.db_verifications.get_verification_by_user_id(interaction.guild_id, member.id)

            if verification is None:
                await interaction.response.send_message(
                    "An error occurred while trying to process your request. Verification record not found.",
                    ephemeral=True,
                )
                return

            # TODO:
            if verification.status in (
                    VerificationStatus.verified_alumni,
                    VerificationStatus.verified_external,
                    VerificationStatus.verified_teacher,
                    VerificationStatus.verified_student,
                    VerificationStatus.kicked,
            ):
                await interaction.response.send_message(
                    "An error occurred while trying to precess your request. Verification is already closed",
                    ephemeral=True,
                )
                return

            guild_config = await self.bot.db_guilds.get_guild_by_id(interaction.guild_id)

            if guild_config is None:
                await interaction.response.send_message(
                    "An error occurred while trying to process your request. No guild configuration found.",
                    ephemeral=True,
                )
                return

            if self.action == "kick_user":
                result = await Moderation.check_member_permissions(self.bot, interaction.guild, interaction.user)

                if not result[0]:
                    await interaction.response.send_message(
                        result[1],
                        ephemeral=True,
                    )
                    return

                await member.kick(reason=reason)

                update_verification = VerificationsUpdate(
                    id=verification.id,
                    status=VerificationStatus.kicked,
                    verification_expires_at=None,
                    ticket_id=None,
                )

                await self.bot.db_verifications.update_verification(update_verification)

                await self.bot.logger.moderation.moderation_kick(interaction.guild, member, interaction.user, reason)
            else:
                action = self.action if self.action != "other" else self.action_select.values[0]

                verification_status = VerificationStatus.from_str(action)

                verification_cogs: "Verifications | None" = self.bot.get_cog("Verifications")

                if verification_cogs is None:
                    await interaction.response.send_message(
                        "An error occurred while trying to process your request. Verifications system is unavailable.",
                        ephemeral=True,
                    )
                    return

                await verification_cogs.set_member_status(self.bot, interaction.guild, member, verification,
                                                          verification_status)

                await self.bot.logger.verification.success_manual_verification(
                    guild=interaction.guild,
                    member=member,
                    moderator=interaction.user,
                    verification=verification,
                    new_status=verification_status,
                    reason=reason,
                )

            ticket_cog: "Tickets | None" = self.bot.get_cog("Tickets")

            if ticket_cog is None:
                await interaction.response.send_message(
                    "An error occurred while trying to process your request. Tickets system is unavailable.",
                    ephemeral=True,
                )
                return

            await ticket_cog.close_ticket(interaction.guild, self.ticket, interaction.channel)

            await interaction.response.defer()
        except Exception as e:
            logger.error(f"Error processing verification reason modal for ticket ID {self.ticket.id}", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while processing your request. Please contact an administrator.",
                ephemeral=True,
            )
