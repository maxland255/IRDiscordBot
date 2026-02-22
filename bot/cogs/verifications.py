import logging
import discord

from typing import TYPE_CHECKING
from datetime import datetime, UTC, timedelta

from discord import Cog, Member, Guild, RawMemberRemoveEvent, SlashCommandGroup, Permissions, InteractionContextType, \
    ApplicationContext, Role, Embed, Color, CategoryChannel, User, Option, OptionChoice
from discord.ext import tasks

from bot.database.schemas import VerificationStatus, VerificationsCreate, VerificationsUpdate, VerificationsSchema, \
    GuildSchema
from bot.view.verifications.verification_choose_view import VerificationChooseView
from bot.view.verifications.config.config_view import ConfigView
from bot.view.verifications.ask_email_modals import AskEmailModals
from bot.view.verifications.enter_code_modals import EnterCodeModals
from bot.view.verifications.confirm_alumni_modals import ConfirmAlumniModals

from .cogs_base import CogsBase

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.tickets import Tickets

logger = logging.getLogger(__name__)


class Verifications(Cog, CogsBase):
    def __init__(self, bot: "IRBot"):
        self.bot = bot

    async def initialize(self) -> None:
        await self.bot.wait_until_ready()

        # Start looping tasks
        self._kick_unverified_members_loop.start()
        self._manage_verification_lifecycle_loop.start()

    # Looping tasks

    @tasks.loop(minutes=10)
    async def _kick_unverified_members_loop(self):
        try:
            guilds_config = await self.bot.db_guilds.get_all_guilds()

            for guild_config in guilds_config:
                if guild_config.new_member_verification_time_limit == 0:
                    continue

                guild = await self.bot.get_or_fetch(Guild, guild_config.id)

                if guild is None:
                    continue

                kick_before_date = datetime.now(UTC) - timedelta(hours=guild_config.new_member_verification_time_limit)

                member_to_kick = await self.bot.db_verifications.get_unverified_members_past_date(guild.id,
                                                                                                  kick_before_date)

                for entry in member_to_kick:
                    if entry.joined_at > kick_before_date:
                        # Verification if an error is occurred with the SQL condition
                        continue

                    member = await guild.get_or_fetch(Member, entry.user_id)

                    if member is None:
                        await self.bot.db_verifications.update_verification(
                            VerificationsUpdate(
                                id=entry.id,
                                status=VerificationStatus.kicked,
                            )
                        )
                        continue

                    try:
                        invite = await guild.text_channels[0].create_invite(
                            max_age=604800,  # 7 days
                            max_uses=1,
                            unique=True,
                            reason="Re-invite after verification kick",
                        )
                        await member.send(
                            f"Vous avez été expulsé du serveur '{guild.name}' car vous n'avez pas "
                            f"complété la vérification dans le délai de {guild_config.new_member_verification_time_limit} heures.\n\n"
                            f"Vous pouvez rejoindre à nouveau ici si vous êtes prêt à vous vérifier : {invite.url}"
                        )

                        await member.kick(reason="Failed to complete verification in time.")

                        await self.bot.logger.verification.kick_unverified_new_member(
                            guild,
                            member,
                            entry,
                            "Failed to complete verification in time.",
                        )
                    except (discord.Forbidden, discord.HTTPException):
                        pass

                    await self.bot.db_verifications.update_verification(
                        VerificationsUpdate(
                            id=entry.id,
                            status=VerificationStatus.kicked,
                        )
                    )
        except Exception as e:
            logger.error("Error in kick_unverified_members_loop", exc_info=e)

    @tasks.loop(hours=24)
    async def _manage_verification_lifecycle_loop(self):
        await self._manage_expired_member_status()

        await self._manage_expired_member_status_reminder()

        await self._manage_expired_member_grace_periods()

    async def _manage_expired_member_status(self):
        try:
            now = datetime.now(UTC)

            expired_student = await self.bot.db_verifications.get_expired_students(now)

            for entry in expired_student:
                guild = await self.bot.get_or_fetch(Guild, entry.guild_id)
                if guild is None: continue

                member = await guild.get_or_fetch(Member, entry.user_id)
                if member is None: continue

                guild_config = await self.bot.db_guilds.get_guild_by_id(guild.id)
                if guild_config is None: continue

                grace_period_end_at = now + timedelta(days=guild_config.grace_period_days)

                await self.bot.db_verifications.start_reverification(entry.id, grace_period_end_at)

                try:
                    await member.send(
                        embed=self._create_embed_reverification_notice(guild, guild_config)
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
        except Exception as e:
            logger.error("Error in manage_expired_member_status", exc_info=e)

    async def _manage_expired_member_status_reminder(self):
        try:
            now = datetime.now(UTC)

            reminder_date = now + timedelta(days=3)

            members_to_remind = await self.bot.db_verifications.get_reverification_reminders(reminder_date)

            for entry in members_to_remind:
                guild = await self.bot.get_or_fetch(Guild, entry.guild_id)
                if guild is None: continue

                member = await self.bot.get_or_fetch(User, entry.user_id)
                if member is not None:
                    await member.send(
                        embed=self._create_embed_reverification_notice(guild, guild_config=None, reminder=True)
                    )

                await self.bot.db_verifications.mark_reminder_sent(entry.id, sent_at=now)
        except Exception as e:
            logger.error("Error in manage_expired_member_status_reminder", exc_info=e)

    async def _manage_expired_member_grace_periods(self):
        try:
            now = datetime.now(UTC)

            expired_grace_periods = await self.bot.db_verifications.get_expired_grace_periods(now)

            for entry in expired_grace_periods:
                guild = await self.bot.get_or_fetch(Guild, entry.guild_id)
                if guild is None: continue

                member = await guild.get_or_fetch(Member, entry.user_id)
                if member is None: continue

                guild_config = await self.bot.db_guilds.get_guild_by_id(guild.id)
                if guild_config is None: continue

                try:
                    await member.remove_roles(*member.roles[1:], atomic=True,
                                              reason="Grace period expired, removing all roles.")
                except (discord.Forbidden, discord.HTTPException):
                    pass

                await self.bot.db_verifications.update_verification(
                    VerificationsUpdate(
                        id=entry.id,
                        status=VerificationStatus.expired,
                    )
                )
        except Exception as e:
            logger.error("Error in manage_expired_member_grace_periods", exc_info=e)

    # Event listeners

    @Cog.listener("on_member_join")
    async def _on_member_join(self, member: Member):
        if member.bot:
            return

        verification = await self.bot.db_verifications.get_verification_by_user_id(member.guild.id, member.id)

        if verification is not None:
            match verification.status:
                case VerificationStatus.verified_student \
                     | VerificationStatus.verified_alumni \
                     | VerificationStatus.verified_external \
                     | VerificationStatus.verified_teacher:
                    # User is already verified, add the role if missing
                    await self._handle_existing_member_verification(member, verification)
                case _:
                    # User is in the process of verification, reset the process
                    await self._handle_new_member(member, verification)
        else:
            await self._handle_new_member(member)

    @Cog.listener("on_raw_member_remove")
    async def _on_raw_member_remove(self, payload: RawMemberRemoveEvent):
        try:
            verification = await self.bot.db_verifications.get_verification_by_user_id(payload.guild_id,
                                                                                       payload.user.id)

            if verification is not None and verification.ticket_id is not None:
                ticket_cogs: "Tickets | None" = self.bot.get_cog("Tickets")

                if ticket_cogs is not None:
                    guild = await self.bot.get_or_fetch(Guild, payload.guild_id)
                    ticket = await self.bot.db_tickets.get_ticket_by_id(verification.ticket_id)

                    if guild is not None and ticket is not None:
                        await ticket_cogs.close_ticket(guild, ticket)

                        update_verification = VerificationsUpdate(
                            id=verification.id,
                            ticket_id=None,
                        )

                        await self.bot.db_verifications.update_verification(update_verification)
                    else:
                        logger.warning(
                            f"Guild or Ticket not found when trying to close ticket ID {verification.ticket_id} for user ID {payload.user.id} in guild ID {payload.guild_id}")
                else:
                    logger.warning("Unable to find Tickets in the IRBot cogs")
        except Exception as e:
            logger.error(f"Error handling member remove for user ID {payload.user.id} in guild ID {payload.guild_id}",
                         exc_info=e)

    async def _handle_existing_member_verification(self, member: Member, verification: VerificationsSchema):
        if verification.status == VerificationStatus.verified_student:
            # Check if the verification has expired
            now = datetime.now(UTC)

            if verification.verification_expires_at is not None and verification.verification_expires_at < now:
                # Verification has expired, update status to reset the verification
                await self._handle_new_member(member, verification)
            else:
                # Verification is still valid, reapply roles if necessary
                await self.set_member_status(self.bot, member.guild, member, verification, verification.status)
        else:
            await self.set_member_status(self.bot, member.guild, member, verification, verification.status)

    async def _handle_new_member(self, member: Member, existing_verification: VerificationsSchema | None = None):
        try:
            if existing_verification is not None:
                update_verification = VerificationsUpdate(
                    id=existing_verification.id,
                    joined_at=datetime.now(UTC),
                    status=VerificationStatus.pending_email,
                    hashed_code=None,
                    code_expires_at=None,
                    verification_expires_at=None,
                    grace_period_ends_at=None,
                    ticket_id=None,
                )

                await self.bot.db_verifications.update_verification(update_verification)
            else:
                new_verification = VerificationsCreate(
                    guild_id=member.guild.id,
                    user_id=member.id,
                )

                await self.bot.db_verifications.create_verification(new_verification)
        except Exception as e:
            logger.error(f"Error creating new verification for member {member.id} in guild {member.guild.id}",
                         exc_info=e)

    # Commands

    # Users commands

    verification_user = SlashCommandGroup(
        name="verify",
        description="Manage user verifications",
    )

    @verification_user.command(
        name="reverify",
        description="Start the re-verification process",
    )
    async def verification_user_reverify(
            self,
            ctx: ApplicationContext,
            status: int = Option(
                int,
                description="",
                choices=[
                    OptionChoice(
                        name="Student",
                        value=1,
                    ),
                    OptionChoice(
                        name="Alumni",
                        value=2,
                    ),
                ]
            ),
    ):
        try:
            if status == 1:
                # Student
                verification = await self.bot.db_verifications.get_verification_by_user_id(ctx.guild_id, ctx.author.id)
                if verification is None:
                    await ctx.respond(
                        "❌ You do not have a verification entry. Please contact an administrator.",
                        ephemeral=True,
                    )
                    return

                if verification.status not in [
                    VerificationStatus.verified_student,
                    VerificationStatus.pending_reverification,
                ]:
                    await ctx.respond(
                        "❌ You are not eligible to reverify as a Student. Only verified students can reverify as Students.",
                        ephemeral=True,
                    )
                    return

                await ctx.response.send_modal(
                    AskEmailModals(self.bot, verification)
                )
            elif status == 2:
                # Alumni
                verification = await self.bot.db_verifications.get_verification_by_user_id(ctx.guild_id, ctx.author.id)
                if verification is None:
                    await ctx.respond(
                        "❌ You do not have a verification entry. Please contact an administrator.",
                        ephemeral=True,
                    )
                    return

                if verification.status not in [
                    VerificationStatus.verified_student,
                    VerificationStatus.pending_reverification,
                ]:
                    await ctx.respond(
                        "❌ You are not eligible to reverify as an Alumni. Only verified students can reverify as Alumni.",
                        ephemeral=True,
                    )
                    return

                await ctx.response.send_modal(
                    ConfirmAlumniModals(self.bot, verification)
                )
            else:
                await ctx.respond(
                    "❌ Invalid status selected. Please choose either 'Student' or 'Alumni'.",
                    ephemeral=True,
                )
        except Exception as e:
            logger.error(f"Error in reverify command for user {ctx.author.id} in guild {ctx.guild_id}", exc_info=e)
            await ctx.respond(
                "An error occurred while trying to process your re-verification. Please contact an administrator.",
                ephemeral=True,
            )

    @verification_user.command(
        name="code",
        description="Enter your verification code",
    )
    async def verification_user_code(self, ctx: ApplicationContext):
        try:
            verification = await self.bot.db_verifications.get_verification_by_user_id(ctx.guild_id, ctx.author.id)
            if verification is None:
                await ctx.respond(
                    "❌ You do not have a verification entry. Please contact an administrator.",
                    ephemeral=True,
                )
                return

            if verification.status not in [
                VerificationStatus.pending_email,
                VerificationStatus.pending_reverification,
            ]:
                await ctx.respond(
                    "❌ You are not currently in a state that requires entering a verification code.",
                    ephemeral=True,
                )
                return

            await ctx.response.send_modal(
                EnterCodeModals(self.bot)
            )
        except Exception as e:
            logger.error(f"Error in code command for user {ctx.author.id} in guild {ctx.guild_id}", exc_info=e)
            await ctx.respond(
                "An error occurred while trying to process your verification code. Please contact an administrator.",
                ephemeral=True,
            )

    # Administrator commands

    verification = SlashCommandGroup(
        name="verification",
        description="Commands related to user verifications",
        default_member_permissions=Permissions(administrator=True),
        contexts={InteractionContextType.guild},
    )

    verification_config = verification.create_subgroup(
        name="config",
        description="Commands related to user verifications configuration",
    )

    verification_admin = verification.create_subgroup(
        name="admin",
        description="Manage user verifications manually",
    )

    @verification_config.command(
        name="publish",
        description="Publish verification panel in the current channel",
    )
    async def verification_publish(self, ctx: ApplicationContext):
        try:
            await ctx.defer(ephemeral=True)

            verification_view = VerificationChooseView(self.bot)

            await ctx.channel.send(
                embed=await verification_view.create_panel_embed(ctx.guild),
                view=verification_view,
            )

            await ctx.respond(
                "✅ Verification panel has been published in this channel.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error publishing verification panel", exc_info=e)
            await ctx.respond(
                "An error occurred while trying to publish the verification panel. Please contact an administrator.",
                ephemeral=True,
            )

    @verification_config.command(
        name="configure",
        description="Configure verification settings for the server",
    )
    async def verification_configure(self, ctx: ApplicationContext):
        try:
            await ctx.defer(ephemeral=True)

            config_view = ConfigView(self.bot)

            verification_embed = await self.create_embed_config_view(self.bot, ctx.guild)

            await ctx.respond(
                embed=verification_embed,
                view=config_view,
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error creating verification config view", exc_info=e)
            await ctx.respond(
                "An error occurred while trying to create the verification configuration view. Please contact an administrator.",
                ephemeral=True,
            )

    @verification_config.command(
        name="config_view",
        description="View the current verification configuration for the server",
    )
    async def verification_config_view(self, ctx: ApplicationContext):
        try:
            await ctx.defer(ephemeral=True)

            verification_embed = await self.create_embed_config_view(self.bot, ctx.guild)

            await ctx.respond(embed=verification_embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error creating verification config view", exc_info=e)
            await ctx.respond(
                "An error occurred while trying to create the verification configuration view. Please contact an administrator.",
                ephemeral=True,
            )

    # Admin commands

    @verification_admin.command(
        name="set_status",
        description="Manually set a member's verification status",
    )
    async def verification_admin_set_status(
            self,
            ctx: ApplicationContext,
            member: Member = Option(
                Member,
                description="The member to set the verification status for",
                required=True,
            ),
            status: VerificationStatus = Option(
                VerificationStatus,
                description="The verification status to set",
                required=True,
            ),
            close_ticket: bool = Option(
                bool,
                description="Whether or not to close the verification ticket if one exists",
                required=False,
                default=False,
            ),
    ):
        try:
            verification = await self.bot.db_verifications.get_verification_by_user_id(ctx.guild_id, member.id)

            if verification is None:
                await ctx.respond(
                    f"{member.mention} does not have a verification entry. Please create one first.",
                    ephemeral=True,
                )
                return

            if close_ticket and verification.ticket_id is None:
                await ctx.respond(
                    f"{member.mention} does not have an associated verification ticket to close.",
                    ephemeral=True,
                )
                return

            if close_ticket:
                ticket_cog: "Tickets | None" = self.bot.get_cog("Tickets")

                if ticket_cog is None:
                    await ctx.respond(
                        "Tickets cog is not available. Cannot close the verification ticket.",
                        ephemeral=True,
                    )
                    return

                ticket = await self.bot.db_tickets.get_ticket_by_id(verification.ticket_id)

                await ticket_cog.close_ticket(ctx.guild, ticket)

            await self.set_member_status(self.bot, ctx.guild, member, verification, status)

            await self.bot.logger.verification.success_manual_verification(
                ctx.guild,
                member,
                ctx.author,
                verification,
                status,
                reason="Manual status change via admin command",
            )

            await ctx.respond(
                f"✅ Successfully set {member.mention}'s verification status to {status.name}.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error setting verification status for member {member.id} in guild {ctx.guild_id}",
                         exc_info=e)
            await ctx.respond(
                f"An error occurred while trying to set the verification status for {member.mention}. Please contact an administrator.",
                ephemeral=True,
            )

    @verification_admin.command(
        name="create_verification",
        description="Create a verification entry for a member if one does not exist",
    )
    async def verification_admin_create_verification(
            self,
            ctx: ApplicationContext,
            member: Member = Option(
                Member,
                description="The member to set the verification status for",
                required=True,
            ),
    ):
        try:
            await self._on_member_join(member)

            await ctx.respond(
                f"✅ Successfully created a verification entry for {member.mention} if one did not already exist.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error creating verification for member {member.id} in guild {member.guild.id}",
                         exc_info=e)
            await ctx.respond(
                f"An error occurred while trying to create a verification for {member.mention}. Please contact an administrator.",
                ephemeral=True,
            )
            return

    # Static methods
    @staticmethod
    async def set_member_status(bot: "IRBot", guild: Guild, member: Member, verification: VerificationsSchema,
                                status: VerificationStatus) -> None:
        guild_config = await bot.db_guilds.get_guild_by_id(guild.id)

        if guild_config is None:
            logger.warning(f"Guild config not found for guild ID {guild.id} in set_member_status.")
            raise ValueError("Guild configuration not found.")

        for role in member.roles[1:]:
            if role.id in [
                guild_config.verified_role_id,
                guild_config.student_role_id,
                guild_config.alumni_role_id,
                guild_config.external_role_id,
                guild_config.teacher_role_id,
            ]:
                try:
                    await member.remove_roles(role, reason="Updating verification status")
                except (discord.Forbidden, discord.HTTPException):
                    pass

        update_verification = VerificationsUpdate(
            id=verification.id,
            hashed_code=None,
            code_expires_at=None,
            status=status,
            verification_expires_at=None,
            grace_period_ends_at=None,
            last_reminder_sent_at=None,
        )

        if status == VerificationStatus.verified_student:
            verification_expires_at = datetime.now(UTC) + timedelta(days=365)

            update_verification.verification_expires_at = verification_expires_at
            update_verification.grace_period_ends_at = verification_expires_at + timedelta(
                days=guild_config.grace_period_days)

        if guild_config.verified_role_id is not None:
            verified_role = await guild.get_or_fetch(Role, guild_config.verified_role_id)

            if verified_role is not None:
                await member.add_roles(verified_role, reason="Verified role")

        if status == VerificationStatus.verified_student:
            verified_student_role = await guild.get_or_fetch(Role, guild_config.student_role_id)

            if verified_student_role is None:
                logger.warning(f"Student role not found in guild ID {guild.id} during set_member_status.")
                raise ValueError("Student role not configured in guild.")

            await member.add_roles(verified_student_role, reason="Verified student role")
        elif status == VerificationStatus.verified_alumni:
            verified_alumni_role = await guild.get_or_fetch(Role, guild_config.alumni_role_id)

            if verified_alumni_role is None:
                logger.warning(f"Alumni role not found in guild ID {guild.id} during set_member_status.")
                raise ValueError("Alumni role not configured in guild.")

            await member.add_roles(verified_alumni_role, reason="Verified alumni role")
        elif status == VerificationStatus.verified_external:
            verified_external_role = await guild.get_or_fetch(Role, guild_config.external_role_id)

            if verified_external_role is None:
                logger.warning(f"External role not found in guild ID {guild.id} during set_member_status.")
                raise ValueError("External role not configured in guild.")

            await member.add_roles(verified_external_role, reason="Verified external role")
        elif status == VerificationStatus.verified_teacher:
            verified_teacher_role = await guild.get_or_fetch(Role, guild_config.teacher_role_id)

            if verified_teacher_role is None:
                logger.warning(f"Teacher role not found in guild ID {guild.id} during set_member_status.")
                raise ValueError("Teacher role not configured in guild.")

            await member.add_roles(verified_teacher_role, reason="Verified teacher role")
        else:
            logger.warning(f"Invalid status {status} provided in set_member_status.")
            raise ValueError("Invalid verification status provided.")

        await bot.db_verifications.update_verification(update_verification)

    @staticmethod
    async def check_verification_status(bot: "IRBot", guild: Guild) -> None:
        """
        Check if the verification system is properly configured in the guild to operate.
        If not, raise appropriate warnings or errors.
        :param bot:
        :param guild:
        :return:
        """
        guild_config = await bot.db_guilds.get_guild_by_id(guild.id)

        if guild_config is None:
            raise ValueError("Guild configuration not found.")

        if guild_config.student_role_id is None:
            raise ValueError("Student role is not configured.")

        if guild_config.alumni_role_id is None:
            raise ValueError("Alumni role is not configured.")

        if guild_config.external_role_id is None:
            raise ValueError("External role is not configured.")

        if guild_config.teacher_role_id is None:
            raise ValueError("Teacher role is not configured.")

        if len(guild_config.allowed_email_domains) == 0:
            raise ValueError("No allowed email domains are configured.")

        if guild_config.verification_ticket_type_id is None:
            raise ValueError("The manual verification ticket type is not configured.")

        ticket_type = await bot.db_ticket_type.get_ticket_type_by_id(guild_config.verification_ticket_type_id)

        if ticket_type is None:
            raise ValueError("The manual verification ticket type configured does not exist.")

    @staticmethod
    async def create_embed_config_view(bot: "IRBot", guild: Guild) -> Embed:
        """
        Create an embed representing the current verification configuration of the guild.
        :param bot:
        :param guild:
        :return:
        """
        warning = False

        try:
            await Verifications.check_verification_status(bot, guild)
        except ValueError:
            warning = True

        verification_ticket_type_id: int | None = None
        verified_role: Role | None = None
        student_role: Role | None = None
        alumni_role: Role | None = None
        external_role: Role | None = None
        teacher_role: Role | None = None
        grace_period_days: int | None = None
        new_member_verification_time_limit: int | None = None
        allowed_email_domains: list[str] = []

        ticket_type_moderator_role: Role | None = None
        ticket_type_category: CategoryChannel | None = None

        guild_config = await bot.db_guilds.get_guild_by_id(guild.id)

        if guild_config is not None:
            verification_ticket_type_id = guild_config.verification_ticket_type_id
            verified_role = await guild.get_or_fetch(Role,
                                                     guild_config.verified_role_id) if guild_config.verified_role_id else None
            student_role = await guild.get_or_fetch(Role,
                                                    guild_config.student_role_id) if guild_config.student_role_id else None
            alumni_role = await guild.get_or_fetch(Role,
                                                   guild_config.alumni_role_id) if guild_config.alumni_role_id else None
            external_role = await guild.get_or_fetch(Role,
                                                     guild_config.external_role_id) if guild_config.external_role_id else None
            teacher_role = await guild.get_or_fetch(Role,
                                                    guild_config.teacher_role_id) if guild_config.teacher_role_id else None
            grace_period_days = guild_config.grace_period_days
            new_member_verification_time_limit = guild_config.new_member_verification_time_limit
            allowed_email_domains = guild_config.allowed_email_domains

            if verification_ticket_type_id is not None:
                ticket_type = await bot.db_ticket_type.get_ticket_type_by_id(verification_ticket_type_id)

                if ticket_type is not None:
                    ticket_type_moderator_role = await guild.get_or_fetch(Role,
                                                                          ticket_type.moderator_role_id) if ticket_type.moderator_role_id else None
                    ticket_type_category = await guild.get_or_fetch(CategoryChannel,
                                                                    ticket_type.ticket_channel_category_id) if ticket_type.ticket_channel_category_id else None

        verification_embed = Embed(
            title="Verifications",
            description="⚠️ Warning: The verification system is not properly configured. Please review the settings below." if warning else "✅ The verification system is properly configured.",
            color=Color.orange() if warning else Color.green(),
            timestamp=datetime.now(UTC),
        )

        verification_embed.add_field(
            name="Verified Role",
            value=verified_role.mention if verified_role else "Not configured",
            inline=False,
        )

        verification_embed.add_field(
            name="Student Role",
            value=student_role.mention if student_role else "Not configured",
            inline=False,
        )

        verification_embed.add_field(
            name="Alumni Role",
            value=alumni_role.mention if alumni_role else "Not configured",
            inline=False,
        )

        verification_embed.add_field(
            name="External Role",
            value=external_role.mention if external_role else "Not configured",
            inline=False,
        )

        verification_embed.add_field(
            name="Teacher Role",
            value=teacher_role.mention if teacher_role else "Not configured",
            inline=False,
        )

        verification_embed.add_field(
            name="Grace Period (days)",
            value=str(grace_period_days) if grace_period_days is not None else "Not configured",
            inline=False,
        )

        verification_embed.add_field(
            name="New Member Verification Time Limit (hours)",
            value=str(
                new_member_verification_time_limit) if new_member_verification_time_limit is not None else "Not configured",
            inline=False,
        )

        verification_embed.add_field(
            name="Allowed Email Domains",
            value=", ".join(allowed_email_domains) if allowed_email_domains else "Not configured",
            inline=False,
        )

        verification_embed.add_field(
            name="Verification Ticket Type",
            value=f"ID: {verification_ticket_type_id}\n"
                  f"Moderator Role: {ticket_type_moderator_role.mention if ticket_type_moderator_role else 'Not configured'}\n"
                  f"Category: {ticket_type_category.mention if ticket_type_category else 'Not configured'}"
            if verification_ticket_type_id is not None else "Not configured",
            inline=False,
        )

        return verification_embed

    @staticmethod
    def _create_embed_reverification_notice(guild: Guild, guild_config: GuildSchema | None = None,
                                            reminder: bool = False) -> Embed:
        assert guild_config is not None or reminder, "guild_config must be provided if reminder is False"

        if reminder:
            description = (
                f"Ceci est un rappel que votre statut de 'Étudiant vérifié' sur le serveur '{guild.name}' a expiré. "
                f"Il ne vous reste que quelques jours pour vous reverifier avant de devoir recommencer le processus de vérification depuis le début !"
                f"\n\nVeuillez exécuter la commande `/verify` pour commencer le processus de reverification.")
        else:
            description = (f"Votre statut de 'Étudiant vérifié' sur le serveur '{guild.name}' a expiré. "
                           f"Vous avez une période de grâce de {guild_config.grace_period_days} jours pour vous reverifier. "
                           f"Après cette période, vous devrez recommencer le processus de vérification depuis le début !"
                           f"\n\nVeuillez exécuter la commande `/verify` pour commencer le processus de reverification."
                           f"\nSi vous n'êtes plus étudiant, vous pouvez choisir le statut 'Alumni' lors de la vérification."
                           f"**Par contre, cela vous retirera l'accès aux canaux réservés aux étudiants.**")

        reverification_embed = Embed(
            title="Re-verification Required",
            description=description,
            color=Color.red() if reminder else Color.orange(),
            timestamp=datetime.now(UTC),
        )

        reverification_embed.set_footer(
            text=guild.name,
            icon_url=guild.icon.url if guild.icon else None,
        )

        return reverification_embed
