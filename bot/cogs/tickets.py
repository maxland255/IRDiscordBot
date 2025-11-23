import logging

from typing import TYPE_CHECKING, Any, Callable
from datetime import datetime, UTC

from discord import Cog, SlashCommandGroup, InteractionContextType, Message, StickerItem, RawMessageDeleteEvent, \
    RawMessageUpdateEvent, RawBulkMessageDeleteEvent, ApplicationContext, Member, Option, Role, Interaction, \
    TextChannel, CategoryChannel, Guild, Embed
from discord.utils import get_or_fetch
from discord.ui import DesignerView

from .cogs_base import CogsBase

from bot.exception import NonCriticalCogInitializationError
from bot.database.schemas import TicketMessageCreate, TicketMessageUpdate, TicketStatus, TicketsSchema, TicketsUpdate, \
    TicketTypeSchema, TicketsCreate
from bot.utils.get_role import get_role
from bot.utils.ticket_permissions import get_externe_member_permissions, get_moderator_permissions, \
    get_member_permissions, get_default_role_permissions
from bot.view.tickets.ticket_manage_panel_view import TicketManagePanelView

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class Tickets(Cog, CogsBase):
    def __init__(self, bot: "IRBot"):
        self.bot = bot

        self._all_channel_tickets: set[int] = set()

    tickets = SlashCommandGroup(
        name="tickets",
        description="Tickets command",
        contexts={InteractionContextType.guild},
    )

    async def initialize(self) -> None:
        try:
            logger.info(f"Initializing Tickets")

            tickets = await self.bot.db_tickets.get_all_open_tickets()

            for ticket in tickets:
                if ticket.channel_id is not None:
                    self._all_channel_tickets.add(ticket.channel_id)
                else:
                    logger.warning(f"Ticket {ticket.id} has no channel_id")

            logger.info(f"{len(self._all_channel_tickets)} tickets opened")
            logger.info("Tickets initialization complete")
        except Exception as e:
            logger.exception("Failed to initialize Tickets", exc_info=e)
            raise NonCriticalCogInitializationError(e)

    @property
    def all_channel_tickets(self) -> set[int]:
        return self._all_channel_tickets

    def add_ticket_channel_id(self, channel_id: int) -> None:
        self._all_channel_tickets.add(channel_id)

    def remove_ticket_channel_id(self, channel_id: int) -> None:
        self._all_channel_tickets.remove(channel_id)

    # Manage ticket method

    async def create_ticket_from_interaction(self, interaction: Interaction, ticket_type: TicketTypeSchema,
                                             reason: str | None = None) -> TextChannel | None:
        result = await self.create_new_ticket(
            ticket_type=ticket_type,
            member=interaction.user,
            guild=interaction.guild,
            ticket_management_view=TicketManagePanelView,
            ticket_management_embed=TicketManagePanelView.create_panel_embed(ticket_type, author=interaction.user,
                                                                             reason=reason),
        )

        return result[0]

    async def create_new_ticket(self, ticket_type: TicketTypeSchema | int, member: Member, guild: Guild,
                                ticket_management_view: Callable[["IRBot"], DesignerView],
                                ticket_management_embed: Embed) -> tuple[
        TextChannel, TicketsSchema]:

        ticket_type = await self.bot.db_ticket_type.get_ticket_type_by_id(
            ticket_type.id if isinstance(ticket_type, TicketTypeSchema) else ticket_type)

        if ticket_type is None or ticket_type.deleted_at is not None:
            raise ValueError("Ticket type does not exist or is inactive.")

        existing_ticket = await self.bot.db_tickets.find_open_ticket_by_member_id_guild_id_and_type_id(guild.id,
                                                                                                       member.id,
                                                                                                       ticket_type.id)

        if existing_ticket:
            raise RuntimeError(
                "You already have an open ticket of this type. Please close your existing ticket before opening a new one.",
            )

        new_ticket = TicketsCreate(
            ticket_type_id=ticket_type.id,
            member_id=member.id,
        )

        try:
            ticket = await self.bot.db_tickets.create_ticket(new_ticket)
        except Exception as e:
            logger.exception("Failed to create ticket", exc_info=e)
            raise RuntimeError("An error occurred while creating the ticket.") from e

        ticket_category = await get_or_fetch(guild, CategoryChannel, ticket_type.ticket_channel_category_id)

        if ticket_category is None:
            raise ValueError("Ticket category channel not found.")

        moderator_role = await get_role(guild, ticket_type.moderator_role_id)

        if moderator_role is None:
            raise ValueError("Moderator role not found.")

        ticket_channel = await ticket_category.create_text_channel(
            name=f"{ticket_type.name} - {ticket.id}",
            overwrites={
                guild.default_role: get_default_role_permissions(),
                member: get_member_permissions(),
                moderator_role: get_moderator_permissions(),
            },
            reason=f"Creating ticket channel for ticket ID {ticket.id} ({member.display_name})",
        )

        # Add the ticket channel ID to the in-memory set
        self.add_ticket_channel_id(ticket_channel.id)

        ticket_management_panel_message = await ticket_channel.send(
            embed=ticket_management_embed,
            view=ticket_management_view(self.bot),
        )

        try:
            await ticket_management_panel_message.pin()
        except Exception as e:
            logger.warning(f"Failed to pin ticket panel message in channel {ticket_channel.id}: {e}", exc_info=e)

        update_ticket = TicketsUpdate(
            id=ticket.id,
            channel_id=ticket_channel.id,
            panel_message_id=ticket_management_panel_message.id,
        )

        tickets = await self.bot.db_tickets.update_ticket(update_ticket)

        return ticket_channel, tickets

    async def close_ticket_channel(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        ticket = await self.bot.db_tickets.get_ticket_by_channel_id(interaction.channel_id)

        if ticket is None:
            await interaction.response.send_message(
                "Unable to close ticket: Ticket not found.",
                ephemeral=True,
            )
            return

        ticket_type = ticket.ticket_type

        moderator_role = await get_role(interaction.guild, ticket_type.moderator_role_id)

        if moderator_role is None:
            await interaction.response.send_message(
                "Unable to close ticket: Moderator role not found.",
                ephemeral=True,
            )
            return

        if ticket.member_id != interaction.user.id and moderator_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You do not have permission to close this ticket.",
                ephemeral=True,
            )
            return

        await self.close_ticket(interaction.guild, ticket)

    async def close_ticket(self, guild: Guild, ticket: TicketsSchema, channel: TextChannel | None = None):
        if channel is None:
            channel_id = ticket.channel_id

            if channel_id is None:
                raise ValueError("Channel id is None.")

            channel: TextChannel | None = await guild.get_or_fetch(TextChannel, channel_id)

            if channel is None:
                raise ValueError("Channel not found.")

        if ticket.channel_id != channel.id:
            raise ValueError("Ticket channel ID does not match the provided channel ID.")

        # Remove the ticket channel from the opened tickets set
        self.remove_ticket_channel_id(channel.id)

        update_ticket = TicketsUpdate(
            id=ticket.id,
            status=TicketStatus.CLOSED,
            channel_id=None,
            panel_message_id=None,
        )

        await self.bot.db_tickets.update_ticket(update_ticket)

        await channel.delete(
            reason=f"Ticket ID {ticket.id} closed by the internal system ({self.bot.user.display_name})",
        )

    # Event listeners

    @Cog.listener(name="on_message")
    async def _on_message(self, message: Message):
        try:
            channel = message.channel

            if channel.id in self._all_channel_tickets:
                ticket = await self.bot.db_tickets.get_ticket_by_channel_id(channel.id)

                if ticket is None:
                    logger.error(f"Ticket not found for channel id {channel.id}")
                    return

                create_ticket_message = TicketMessageCreate(
                    ticket_id=ticket.id,
                    message_id=message.id,
                    author_id=message.author.id,
                    content=message.content,
                    attachments_json=[attachment.to_dict() for attachment in
                                      message.attachments] if message.attachments else None,
                    stickers_json=[self._sticker_to_dict(sticker) for sticker in
                                   message.stickers] if message.stickers else None,
                    poll_json=message.poll.to_dict() if message.poll else None,
                    reference_json=message.reference.to_dict() if message.reference else None,
                    embeds_json=[embed.to_dict() for embed in message.embeds] if message.embeds else None,
                )

                await self.bot.db_ticket_messages.create_ticket_message(create_ticket_message)
        except Exception as e:
            logger.exception(f"Error processing message in ticket channel: {message.id}", exc_info=e)

    @Cog.listener("on_raw_message_delete")
    async def _on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        try:
            channel_id = payload.channel_id

            if channel_id in self._all_channel_tickets:
                await self.bot.db_ticket_messages.delete_ticket_message_by_message_id(payload.message_id)
        except Exception as e:
            logger.exception(f"Error processing message delete in ticket channel: {payload.message_id}", exc_info=e)

    @Cog.listener("on_raw_bulk_message_delete")
    async def _on_raw_bulk_message_delete(self, payload: RawBulkMessageDeleteEvent):
        try:
            if payload.channel_id in self._all_channel_tickets:
                await self.bot.db_ticket_messages.delete_multiple_ticket_messages(payload.message_ids)
        except Exception as e:
            logger.exception(f"Error processing bulk message delete in ticket channel: {payload.message_ids}",
                             exc_info=e)

    @Cog.listener("on_raw_message_edit")
    async def _on_raw_message_edit(self, payload: RawMessageUpdateEvent):
        try:
            if payload.channel_id in self._all_channel_tickets:
                ticket_message = await self.bot.db_ticket_messages.get_ticket_message_by_message_id(payload.message_id)

                if ticket_message is None:
                    logger.warning(f"Ticket not found for channel id {payload.channel_id}")
                    return

                message = payload.new_message

                update_ticket_message = TicketMessageUpdate(
                    id=ticket_message.id,
                    content=message.content,
                    attachments_json=[attachment.to_dict() for attachment in
                                      message.attachments] if message.attachments else None,
                    stickers_json=[self._sticker_to_dict(sticker) for sticker in
                                   message.stickers] if message.stickers else None,
                    poll_json=message.poll.to_dict() if message.poll else None,
                    reference_json=message.reference.to_dict() if message.reference else None,
                    embeds_json=[embed.to_dict() for embed in message.embeds] if message.embeds else None,
                    edited_at=datetime.now(UTC),
                )

                await self.bot.db_ticket_messages.update_ticket_message(update_ticket_message)
        except Exception as e:
            logger.exception(f"Error processing message edit in ticket channel: {payload.message_id}", exc_info=e)

    @staticmethod
    def _sticker_to_dict(sticker: StickerItem) -> dict[str, Any]:
        return {
            "id": sticker.id,
            "name": sticker.name,
            "format_type": sticker.format.value,
            "url": sticker.url,
        }

    # Tickets commands

    @tickets.command(
        name="add_user",
        description="Add a user to the ticket channel",
    )
    async def tickets_add_user(
            self,
            ctx: ApplicationContext,
            member: Member = Option(
                Member,
                description="The user to add to the ticket channel",
                required=True,
            )
    ):
        try:
            await ctx.defer(ephemeral=True)

            channel = ctx.channel

            if channel.id not in self._all_channel_tickets:
                await ctx.respond(
                    "This command can only be used in ticket channels.",
                    ephemeral=True,
                )
                return

            ticket = await self.bot.db_tickets.get_ticket_by_channel_id(channel.id)

            if ticket is None or ticket.status == TicketStatus.CLOSED or ticket.deleted_at is not None:
                await ctx.respond(
                    "This ticket is closed or does not exist.",
                    ephemeral=True,
                )
                return

            result = await self.check_member_permissions(ctx, ticket)

            if not result[0]:
                return

            # Check if the member is not the ticket creator
            if member.id == ticket.member_id:
                await ctx.respond(
                    f"{member.mention} is the ticket creator and is already in the ticket channel.",
                    ephemeral=True,
                )
                return

            # Check if the member is already in the channel
            if member in channel.members:
                await ctx.respond(
                    f"{member.mention} is already in this ticket channel.",
                    ephemeral=True,
                )
                return

            await channel.set_permissions(
                member,
                overwrite=get_externe_member_permissions(),
                reason=f"Added {member.mention} to this ticket channel.",
            )

            await ctx.respond(
                f"{member.mention} has been added to this ticket channel.",
                ephemeral=True,
            )
        except Exception as e:
            logger.exception(
                f"An error occurred while processing the command tickets add user.",
                exc_info=e,
            )
            await ctx.respond(
                "An error occurred while processing the command. Please try again later.",
                ephemeral=True,
            )

    @tickets.command(
        name="remove_user",
        description="Remove a user from the ticket channel",
    )
    async def tickets_remove_user(
            self,
            ctx: ApplicationContext,
            member: Member = Option(
                Member,
                description="The user to remove from the ticket channel",
                required=True,
            )
    ):
        try:
            await ctx.defer(ephemeral=True)

            channel = ctx.channel

            if channel.id not in self._all_channel_tickets:
                await ctx.respond(
                    "This command can only be used in ticket channels.",
                    ephemeral=True,
                )
                return

            ticket = await self.bot.db_tickets.get_ticket_by_channel_id(channel.id)

            if ticket is None or ticket.status == TicketStatus.CLOSED or ticket.deleted_at is not None:
                await ctx.respond(
                    "This ticket is closed or does not exist.",
                    ephemeral=True,
                )
                return

            result = await self.check_member_permissions(ctx, ticket)

            if not result[0]:
                return

            # Check if the member is not the ticket creator
            if member.id == ticket.member_id:
                await ctx.respond(
                    f"{member.mention} is the ticket creator and cannot be removed from the ticket channel.",
                    ephemeral=True,
                )
                return

            # Check if the member is already in the channel
            if member not in channel.members:
                await ctx.respond(
                    f"{member.mention} is not in this ticket channel.",
                    ephemeral=True,
                )
                return

            await channel.set_permissions(
                member,
                overwrite=None,
                reason=f"Removed {member.mention} from this ticket channel.",
            )

            await ctx.respond(
                f"{member.mention} has been removed to this ticket channel.",
                ephemeral=True,
            )
        except Exception as e:
            logger.exception(
                f"An error occurred while processing the command tickets remove user.",
                exc_info=e,
            )
            await ctx.respond(
                "An error occurred while processing the command. Please try again later.",
                ephemeral=True,
            )

    @tickets.command(
        name="lock",
        description="Lock the ticket channel",
    )
    async def tickets_lock(
            self,
            ctx: ApplicationContext,
    ):
        try:
            await ctx.defer(ephemeral=True)

            channel = ctx.channel

            if channel.id not in self._all_channel_tickets:
                await ctx.respond(
                    "This command can only be used in ticket channels.",
                    ephemeral=True,
                )
                return

            ticket = await self.bot.db_tickets.get_ticket_by_channel_id(channel.id)

            if ticket is None or ticket.status == TicketStatus.CLOSED or ticket.deleted_at is not None:
                await ctx.respond(
                    "This ticket is closed or does not exist.",
                    ephemeral=True,
                )
                return

            if ticket.is_locked:
                await ctx.respond(
                    "This ticket is already locked.",
                    ephemeral=True,
                )
                return

            result = await self.check_member_permissions(ctx, ticket)

            if not result[0]:
                return

            moderator_role = result[1]

            update_ticket = TicketsUpdate(
                id=ticket.id,
                is_locked=True,
            )

            await self.bot.db_tickets.update_ticket(update_ticket)

            await channel.set_permissions(
                ctx.user,
                overwrite=get_moderator_permissions(),
                reason=f"Locked the ticket channel. Granted moderator permissions to {ctx.user.mention}.",
            )

            await channel.set_permissions(
                moderator_role,
                overwrite=None,
                reason=f"Locked the ticket channel. Removed specific permissions from {moderator_role.mention}.",
            )

            await ctx.respond(
                "The ticket channel has been locked.",
                ephemeral=True,
            )
        except Exception as e:
            logger.exception(
                f"An error occurred while processing the command tickets lock.",
                exc_info=e,
            )
            await ctx.respond(
                "An error occurred while processing the command. Please try again later.",
                ephemeral=True,
            )

    @tickets.command(
        name="unlock",
        description="Unlock the ticket channel",
    )
    async def tickets_unlock(
            self,
            ctx: ApplicationContext,
    ):
        try:
            await ctx.defer(ephemeral=True)

            channel = ctx.channel

            if channel.id not in self._all_channel_tickets:
                await ctx.respond(
                    "This command can only be used in ticket channels.",
                    ephemeral=True,
                )
                return

            ticket = await self.bot.db_tickets.get_ticket_by_channel_id(channel.id)

            if ticket is None or ticket.status == TicketStatus.CLOSED or ticket.deleted_at is not None:
                await ctx.respond(
                    "This ticket is closed or does not exist.",
                    ephemeral=True,
                )
                return

            if not ticket.is_locked:
                await ctx.respond(
                    "This ticket is not locked.",
                    ephemeral=True,
                )
                return

            result = await self.check_member_permissions(ctx, ticket)

            if not result[0]:
                return

            moderator_role = result[1]

            update_ticket = TicketsUpdate(
                id=ticket.id,
                is_locked=False,
            )

            await self.bot.db_tickets.update_ticket(update_ticket)

            await channel.set_permissions(
                moderator_role,
                overwrite=get_moderator_permissions(),
                reason=f"Locked the ticket channel. Granted moderator permissions to {moderator_role.mention}.",
            )

            await channel.set_permissions(
                ctx.user,
                overwrite=None,
                reason=f"Locked the ticket channel. Removed moderator permissions from {ctx.user.mention}.",
            )

            await ctx.respond(
                "The ticket channel has been unlocked.",
                ephemeral=True,
            )
        except Exception as e:
            logger.exception(
                f"An error occurred while processing the command tickets lock.",
                exc_info=e,
            )
            await ctx.respond(
                "An error occurred while processing the command. Please try again later.",
                ephemeral=True,
            )

    @staticmethod
    async def check_member_permissions(ctx: ApplicationContext, ticket: TicketsSchema) -> tuple[bool, Role | None]:
        moderator_role = await get_role(ctx.guild, ticket.ticket_type.moderator_role_id)

        if moderator_role is None and not ctx.user.guild_permissions.administrator:
            await ctx.respond(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return False, None

        if moderator_role not in ctx.user.roles and not ctx.user.guild_permissions.administrator:
            await ctx.respond(
                "You do not have permission to use this command.",
                ephemeral=True,
            )
            return False, None
        return True, moderator_role
