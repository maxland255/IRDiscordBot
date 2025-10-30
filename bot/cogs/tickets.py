import logging

from typing import TYPE_CHECKING, Any
from datetime import datetime, UTC

from discord import Cog, SlashCommandGroup, InteractionContextType, Message, StickerItem, RawMessageDeleteEvent, \
    RawMessageUpdateEvent, RawBulkMessageDeleteEvent, ApplicationContext, Member, Option, Role

from .cogs_base import CogsBase

from bot.exception import NonCriticalCogInitializationError
from bot.database.schemas import TicketMessageCreate, TicketMessageUpdate, TicketStatus, TicketsSchema, TicketsUpdate
from bot.utils.get_role import get_role
from bot.utils.ticket_permissions import get_externe_member_permissions, get_moderator_permissions

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
