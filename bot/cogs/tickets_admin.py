import io
import jinja2
import logging

from typing import TYPE_CHECKING
from pathlib import Path

from discord import Cog, SlashCommandGroup, Permissions, InteractionContextType, ApplicationContext, Member, Option, \
    EmbedField, Color, User, File

from .cogs_base import CogsBase

from bot.utils.pagination_view import PaginationView

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)

template_loader = jinja2.FileSystemLoader(searchpath=Path(__file__).parent.parent / "templates")
jinja_env = jinja2.Environment(loader=template_loader, autoescape=True)


class TicketsAdmin(Cog, CogsBase):
    def __init__(self, bot: "IRBot"):
        self.bot = bot

    tickets_admin = SlashCommandGroup(
        name="tickets_admin",
        description="Administrative commands for ticket management and rescue operations",
        contexts={InteractionContextType.guild},
        default_member_permissions=Permissions(administrator=True),
    )

    # Ticket management command

    tickets_management = tickets_admin.create_subgroup(
        name="management",
        description="Administrative commands for ticket management",
    )

    @tickets_management.command(
        name="user_history",
        description="User history ticket information",
    )
    async def tickets_management_user_history(
            self,
            ctx: ApplicationContext,
            member: Member = Option(
                Member,
                description="Member to get user history ticket information",
                required=True,
            )
    ):
        try:
            await ctx.defer(ephemeral=True)

            all_member_tickets = await self.bot.db_tickets.get_all_tickets_by_member_id(member.id)

            if not all_member_tickets:
                await ctx.respond(
                    f"No tickets found for user {member.mention}.",
                    ephemeral=True,
                )
                return

            pagination_view = PaginationView(
                data=all_member_tickets,
                title=f"Ticket History for {member.display_name}",
                format_item_func=lambda item: EmbedField(
                    name=f"ID: {item.id}",
                    value=f"**Type:** {item.ticket_type.name}\n**Status:** {item.status.value}\n**Created At:** {item.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
                    inline=False,
                ),
                embed_color=Color.dark_gold(),
            )

            await ctx.respond(
                embed=pagination_view.create_page_embed(),
                view=pagination_view,
                ephemeral=True,
            )
        except Exception as e:
            logger.error(
                f"Error executing tickets_management_user_history command: {e}",
                exc_info=e
            )
            await ctx.respond(
                "An error occurred while processing your request.",
                ephemeral=True,
            )

    @tickets_management.command(
        name="list_open",
        description="List open tickets",
    )
    async def tickets_management_list_open(self, ctx: ApplicationContext):
        try:
            await ctx.defer(ephemeral=True)

            open_tickets = await self.bot.db_tickets.get_all_open_tickets()

            if not open_tickets:
                await ctx.respond(
                    "There are no open tickets at the moment.",
                    ephemeral=True,
                )
                return

            pagination_view = PaginationView(
                data=open_tickets,
                title=f"All Open Tickets",
                format_item_func=lambda item: EmbedField(
                    name=f"ID: {item.id}",
                    value=f"**Type:** {item.ticket_type.name}\n**Member:** <@{item.member_id}>\n**Status:** {item.status.value}\n**Created At:** {item.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
                    inline=False,
                ),
                embed_color=Color.dark_gold(),
            )

            await ctx.respond(
                embed=pagination_view.create_page_embed(),
                view=pagination_view,
                ephemeral=True,
            )
        except Exception as e:
            logger.error(
                f"Error executing tickets_management_list_open command: {e}",
                exc_info=e
            )
            await ctx.respond(
                "An error occurred while processing your request.",
                ephemeral=True,
            )

    @tickets_management.command(
        name="get_transcript",
        description="Get ticket transcript by ticket ID",
    )
    async def tickets_management_get_transcript(
            self,
            ctx: ApplicationContext,
            ticket_id: int = Option(
                int,
                description="Ticket ID to get the transcript",
                required=True,
            )
    ):
        try:
            await ctx.defer(ephemeral=True)

            ticket = await self.bot.db_tickets.get_ticket_by_id(ticket_id)

            if ticket is None:
                await ctx.respond(
                    f"Ticket ID {ticket_id} does not exist.",
                    ephemeral=True,
                )
                return

            all_ticket_message = await self.bot.db_ticket_messages.get_all_ticket_messages(ticket.id,
                                                                                           include_deleted=True)

            if not all_ticket_message:
                await ctx.respond(
                    f"No messages found for ticket ID {ticket_id}.",
                    ephemeral=True,
                )
                return

            processed_messages: list[dict[str, str]] = []
            for msg in all_ticket_message:
                user = await self.bot.get_or_fetch(User, msg.author_id)
                author_name = user.name if user else f"Utilisateur ({msg.author_id})"
                author_avatar = user.display_avatar.url if user and user.display_avatar else "URL_AVATAR_DEFAUT_DISCORD"

                attachments = []
                if msg.attachments_json:
                    for att in msg.attachments_json:
                        attachments.append({
                            "url": att.get('url'),
                            "filename": att.get('filename'),
                            "size": att.get('size'),
                            "is_image": "image" in att.get('content_type', '')
                        })

                processed_messages.append({
                    "id": msg.message_id,
                    "author_name": author_name,
                    "author_avatar": author_avatar,
                    "timestamp": msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "content": msg.content,
                    "attachments": attachments,
                    "stickers": msg.stickers_json,
                    "poll": msg.poll_json,
                    "embeds": msg.embeds_json,
                    "reference": msg.reference_json,
                    "is_deleted": msg.deleted_at is not None,
                })

            creator = await self.bot.get_or_fetch(User, ticket.member_id)
            handler = await self.bot.get_or_fetch(User, ticket.handler_id) if ticket.handler_id else None

            template = jinja_env.get_template("transcript.html")
            html_content = template.render(
                ticket=ticket,
                messages=processed_messages,
                creator_name=creator.name if creator else f"Utilisateur ({ticket.member_id})",
                handler_name=handler.name if handler else "Non assigné"
            )

            file_data = io.BytesIO(html_content.encode('utf-8'))
            transcript_file = File(file_data, filename=f"transcript-ticket-{ticket.id}.html")

            await ctx.respond(
                content=f"Transcript for ticket ID {ticket.id}:",
                file=transcript_file,
                ephemeral=True,
            )
        except Exception as e:
            logger.error(
                f"Error executing tickets_management get_transcript command: {e}",
                exc_info=e
            )
            await ctx.respond(
                "An error occurred while processing your request.",
                ephemeral=True,
            )

    # Ticket rescue command

    # /ticket_admin rescue (Réparation)

    # /ticket_admin rescue force_close <ticket_id_or_channel_id>

    # /ticket_admin rescue set_status <ticket_id> <status>

    # /ticket_admin rescue orphan_check
