import logging

from typing import TYPE_CHECKING

from discord import Cog, SlashCommandGroup, InteractionContextType, Permissions, ApplicationContext, EmbedField, Color, \
    Option, RawMessageDeleteEvent

from .cogs_base import CogsBase

from bot.view.tickets import TicketTypeConfigView
from bot.utils.pagination_view import PaginationView
from bot.database.schemas import TicketTypeUpdate, TicketPanelCreate
from bot.exception import TicketTypeNotFound
from bot.view.tickets import TicketPanelView
from bot.exception import NonCriticalCogInitializationError

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class TicketsConfig(Cog, CogsBase):
    def __init__(self, bot: "IRBot"):
        self.bot = bot

        self.ticket_panel_message_id: set[int] = set()

    async def initialize(self) -> None:
        """
        Initialize the TicketsConfig cog.
        :return:
        """
        try:
            logger.info("Initializing TicketsConfig")

            all_ticket_panel = await self.bot.db_ticket_panel.get_all_ticket_panel()

            logger.info(f"Loaded {len(all_ticket_panel)} ticket panels from the database")

            for ticket in all_ticket_panel:
                self.ticket_panel_message_id.add(ticket.message_id)

            logger.info("TicketsConfig initialization complete")
        except Exception as e:
            logger.exception("Failed to initialize TicketsConfig", exc_info=e)
            raise NonCriticalCogInitializationError(e)

    tickets_config = SlashCommandGroup(
        name="ticket_config",
        description="Configure ticket related commands",
        contexts={InteractionContextType.guild},
        default_member_permissions=Permissions(administrator=True)
    )

    # Event

    @Cog.listener("on_raw_message_delete")
    async def _on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        try:
            message_id = payload.message_id

            if message_id in self.ticket_panel_message_id:
                ticket_panel = await self.bot.db_ticket_panel.get_ticket_panel_by_message_id(message_id)

                if ticket_panel is not None:
                    await self.bot.db_ticket_panel.delete_ticket_panel(ticket_panel)
                    logger.info("Deleted ticket panel %s", ticket_panel)

                self.ticket_panel_message_id.remove(message_id)
        except Exception as e:
            logger.exception("Failed to handle raw message delete event", exc_info=e)

    # Tickets Type commands

    tickets_type = tickets_config.create_subgroup(
        name="type",
        description="Configure ticket types",
    )

    @tickets_type.command(
        name="create",
        description="Create a new ticket type",
    )
    async def ticket_type_create(self, ctx: ApplicationContext):
        try:
            ticket_type_config_view = TicketTypeConfigView(self.bot)

            await ctx.response.send_modal(ticket_type_config_view)
        except Exception as e:
            logger.exception("Failed to create ticket type", exc_info=e)
            await ctx.respond("An error occurred while creating the ticket type.", ephemeral=True)

    @tickets_type.command(
        name="list",
        description="List all ticket types",
    )
    async def ticket_type_list(self, ctx: ApplicationContext):
        try:
            await ctx.defer(ephemeral=True)

            ticket_types = await self.bot.db_ticket_type.get_all_ticket_types(ctx.guild_id)

            if not ticket_types:
                await ctx.followup.send("No ticket types found for this server.", ephemeral=True)
                return

            ticket_types_view = PaginationView(
                data=ticket_types,
                title="Ticket types",
                format_item_func=lambda item: EmbedField(
                    name=item.name,
                    value=f"ID: {item.id}\nDescription: {item.description[:100]}{"..." if len(item.description) >= 100 else ""}\nEnabled: {"Yes" if item.enabled else "No"}",
                ),
                embed_color=Color.blurple(),
            )

            await ctx.followup.send(
                embed=ticket_types_view.create_page_embed(),
                view=ticket_types_view,
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("Failed to list ticket types", exc_info=e)
            await ctx.respond("An error occurred while listing the ticket types.", ephemeral=True)

    @tickets_type.command(
        name="show",
        description="Show details of a ticket type",
    )
    async def ticket_type_show(
            self,
            ctx: ApplicationContext,
            ticket_type_id: int = Option(
                int,
                description="ID of the ticket type",
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            ticket_type = await self.bot.db_ticket_type.get_ticket_type_by_id(ticket_type_id)

            if not ticket_type or ticket_type.deleted_at is not None:
                await ctx.followup.send("Ticket type not found.", ephemeral=True)
                return

            ticket_type_embed = await TicketTypeConfigView.create_ticket_type_embed(self.bot, ctx.guild, ticket_type)

            await ctx.followup.send(
                embed=ticket_type_embed,
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("Failed to show ticket type", exc_info=e)
            await ctx.respond("An error occurred while showing the ticket type.", ephemeral=True)

    @tickets_type.command(
        name="edit",
        description="Edit a ticket type",
    )
    async def ticket_type_edit(
            self,
            ctx: ApplicationContext,
            ticket_type_id: int = Option(
                int,
                description="ID of the ticket type",
                required=True,
            ),
    ):
        try:
            ticket_type = await self.bot.db_ticket_type.get_ticket_type_by_id(ticket_type_id)

            if not ticket_type or ticket_type.deleted_at is not None:
                await ctx.respond("Ticket type not found.", ephemeral=True)
                return

            ticket_type_config_view = TicketTypeConfigView(self.bot, ticket_type=ticket_type)

            await ctx.response.send_modal(ticket_type_config_view)
        except Exception as e:
            logger.exception("Failed to edit ticket type", exc_info=e)
            await ctx.respond("An error occurred while editing the ticket type.", ephemeral=True)

    @tickets_type.command(
        name="enable",
        description="Enable or disable a ticket type",
    )
    async def ticket_type_enable(
            self,
            ctx: ApplicationContext,
            ticket_type_id: int = Option(
                int,
                description="ID of the ticket type",
                required=True,
            ),
            enable: bool = Option(
                bool,
                description="Enable or disable the ticket type",
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            update_ticket_type = TicketTypeUpdate(
                id=ticket_type_id,
                enabled=enable,
            )

            try:
                ticket_type = await self.bot.db_ticket_type.update_ticket_type(update_ticket_type)
            except TicketTypeNotFound as e:
                logger.exception("Failed to update the ticket type", exc_info=e)
                await ctx.followup.send("Ticket type not found.", ephemeral=True)
                return

            await ctx.respond(
                f"Ticket type has been updated !",
                embed=await TicketTypeConfigView.create_ticket_type_embed(self.bot, ctx.guild, ticket_type),
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("Failed to enable/disable ticket type", exc_info=e)
            await ctx.respond("An error occurred while updating the ticket type.", ephemeral=True)

    @tickets_type.command(
        name="delete",
        description="Delete a ticket type",
    )
    async def ticket_type_delete(
            self,
            ctx: ApplicationContext,
            ticket_type_id: int = Option(
                int,
                description="ID of the ticket type",
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            ticket_type = await self.bot.db_ticket_type.get_ticket_type_by_id(ticket_type_id)

            if ticket_type is None or ticket_type.deleted_at is not None:
                await ctx.respond("Ticket type not found.", ephemeral=True)
                return

            result = await self.bot.db_ticket_type.delete_ticket_type(ticket_type)

            if result:
                await ctx.respond("Ticket type has been deleted.", ephemeral=True)
            else:
                await ctx.respond("Failed to delete the ticket type.", ephemeral=True)
        except Exception as e:
            logger.exception("Failed to delete ticket type", exc_info=e)
            await ctx.respond("An error occurred while deleting the ticket type.", ephemeral=True)

    # Ticket panel commands

    ticket_panel = tickets_config.create_subgroup(
        name="panel",
        description="Panel configuration",
    )

    @ticket_panel.command(
        name="publish",
        description="Publish a ticket type",
    )
    async def ticket_panel_publish(
            self,
            ctx: ApplicationContext,
            ticket_type_id: int = Option(
                int,
                description="ID of the ticket type",
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            ticket_type = await self.bot.db_ticket_type.get_ticket_type_by_id(ticket_type_id)

            if ticket_type is None or ticket_type.deleted_at is not None:
                await ctx.respond("Ticket type not found.", ephemeral=True)
                return

            if not ticket_type.enabled:
                await ctx.respond("Cannot publish a panel for a disabled ticket type.", ephemeral=True)
                return

            ticket_panel_view = TicketPanelView(
                self.bot,
                ticket_type,
            )

            ticket_panel_message = await ctx.channel.send(
                embed=ticket_panel_view.create_panel_embed(),
                view=ticket_panel_view,
            )

            create_ticket_panel = TicketPanelCreate(
                ticket_type_id=ticket_type.id,
                channel_id=ticket_panel_message.channel.id,
                message_id=ticket_panel_message.id,
            )

            await self.bot.db_ticket_panel.create_ticket_panel(create_ticket_panel)

            self.ticket_panel_message_id.add(ticket_panel_message.id)

            await ctx.respond(
                "Ticket panel has been published successfully.",
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("Failed to publish ticket panel", exc_info=e)
            await ctx.respond("An error occurred while publishing the ticket panel.", ephemeral=True)
