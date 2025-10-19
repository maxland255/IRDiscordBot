import logging
from tkinter.font import names

from typing import TYPE_CHECKING
from datetime import datetime, UTC

from discord import Cog, SlashCommandGroup, InteractionContextType, Permissions, ApplicationContext, Option, Embed, \
    Color, TextChannel

from bot.database.schemas import RolePanelCreate, RolePanelSchema, RoleOptionsSchema, RolePanelUpdate
from bot.view.panel_list_view import RolePanelListView
from bot.exception import RolesPanelNotFound
from bot.view.panel_option_view import PanelOptionView
from bot.view.role_panel_view import RolePanelView

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class Roles(Cog):
    def __init__(self, bot: "IRBot"):
        self.bot = bot

    roles = SlashCommandGroup(
        name="roles",
        description="Commands for managing roles panels and roles options",
        default_member_permissions=Permissions(administrator=True),
        contexts={InteractionContextType.guild},
    )

    panel = roles.create_subgroup(
        name="panel",
        description="Commands for managing roles panels",
    )

    options = roles.create_subgroup(
        name="options",
        description="Commands for managing roles options in roles panels",
    )

    # Roles panel commands

    @panel.command(
        name="create",
        description="Create a new roles panel",
    )
    async def create_panel(
            self,
            ctx: ApplicationContext,
            name: str = Option(
                str,
                description="The internal name of the panel",
                required=True,
            ),
            title: str = Option(
                str,
                description="The title of the panel",
                required=True,
            ),
            description: str | None = Option(
                str,
                description="The description of the panel",
                required=False,
                default=None,
            ),
            multiple_choose: bool = Option(
                bool,
                description="Enable multiple role selection",
                default=False,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            guild_config = await self.bot.db_guilds.get_guild_by_id(ctx.guild.id)

            if guild_config is None:
                await ctx.respond(
                    "Guild configuration not found. Please set up the bot using /config init command first.",
                    ephemeral=True,
                )
                return

            new_panel = RolePanelCreate(
                guild_id=ctx.guild.id,
                multiple_choose=multiple_choose,
                name=name,
                title=title,
                description=description,
            )

            new_panel = await self.bot.db_role_panels.create_roles_panel(new_panel)

            panel_embed = await self.__print_role_panels(new_panel, [], preview=True)

            await ctx.respond("Roles panel created successfully!", embed=panel_embed, ephemeral=True)
        except Exception as e:
            logger.error("An error occurred while running the roles panel create command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the roles panel create command", ephemeral=True)

    @panel.command(
        name="list",
        description="List roles panels created in this guild",
    )
    async def list_panel(self, ctx: ApplicationContext):
        try:
            await ctx.defer(ephemeral=True)

            role_panels = await self.bot.db_role_panels.get_all_roles_panel_by_guild_id(guild_id=ctx.guild.id)

            if len(role_panels) == 0:
                await ctx.respond("No roles panels found in this guild.", ephemeral=True)
                return

            role_list_panel_view = RolePanelListView(
                panels=role_panels,
            )

            role_list_panel_view.previous_button.disabled = True
            if len(role_panels) <= role_list_panel_view.item_per_page:
                role_list_panel_view.next_button.disabled = True

            await ctx.respond(
                embed=role_list_panel_view.create_page_embed(),
                view=role_list_panel_view,
                ephemeral=True,
            )
        except Exception as e:
            logger.error("An error occurred while running the roles panel list command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the roles panel list command", ephemeral=True)

    @panel.command(
        name="edit",
        description="Edit roles panel",
    )
    async def edit_panel(
            self,
            ctx: ApplicationContext,
            panel_id: int = Option(
                int,
                description="The id of the panel to edit",
                required=True,
            ),
            name: str | None = Option(
                str,
                description="The internal name of the panel",
                default=None,
            ),
            title: str | None = Option(
                str,
                description="The title of the panel",
                default=None,
            ),
            description: str | None = Option(
                str,
                description="The description of the panel",
                required=False,
                default=None,
            ),
            multiple_choose: bool | None = Option(
                bool,
                description="Enable multiple role selection",
                default=None,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            guild_config = await self.bot.db_guilds.get_guild_by_id(ctx.guild.id)

            if guild_config is None:
                await ctx.respond(
                    "Guild configuration not found. Please set up the bot using /config init command first.",
                    ephemeral=True,
                )
                return

            role_panel_update = RolePanelUpdate(
                id=panel_id,
            )

            if name is not None:
                role_panel_update.name = name

            if title is not None:
                role_panel_update.title = title

            if description is not None:
                role_panel_update.description = description

            if multiple_choose is not None:
                role_panel_update.multiple_choose = multiple_choose

            try:
                role_panel_update = await self.bot.db_role_panels.update_roles_panel(role_panel_update)
            except RolesPanelNotFound:
                await ctx.respond(f"Roles panel with id {panel_id} not found.", ephemeral=True)
                return

            panel_embed = await self.__print_role_panels(role_panel_update, [], preview=True)

            await ctx.respond("Roles panel updated successfully!", embed=panel_embed, ephemeral=True)
        except Exception as e:
            logger.error("An error occurred while running the roles panel edit command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the roles panel edit command", ephemeral=True)

    @panel.command(
        name="delete",
        description="Delete roles panel",
    )
    async def delete_panel(
            self,
            ctx: ApplicationContext,
            panel_id: int = Option(
                int,
                description="The id of the panel to delete",
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            result = await self.bot.db_role_panels.delete_role_panel(panel_id)

            if result:
                await ctx.respond(f"Roles panel with id {panel_id} deleted successfully.", ephemeral=True)
            else:
                await ctx.respond(f"Roles panel with id {panel_id} not found.", ephemeral=True)
        except Exception as e:
            logger.error("An error occurred while running the roles panel delete command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the roles panel delete command", ephemeral=True)

    # Roles option commands

    @options.command(
        name="add",
        description="Add roles option to a roles panel",
    )
    async def add_option(
            self,
            ctx: ApplicationContext,
            panel_id: int = Option(
                int,
                description="The id of the panel to add the option to",
                required=True,
            ),
    ):
        try:
            role_panel = await self.bot.db_role_panels.get_roles_panel_by_id(panel_id)

            if role_panel is None:
                await ctx.respond(f"Roles panel with id {panel_id} not found.", ephemeral=True)
                return

            if len(role_panel.options) >= 25:
                await ctx.respond(f"Roles panel with id {panel_id} already has the maximum number of options (25).",
                                  ephemeral=True)
                return

            panel_option_view = PanelOptionView(
                panel_id=panel_id,
                bot=self.bot,
            )

            await ctx.send_modal(panel_option_view)
        except Exception as e:
            logger.error("An error occurred while running the roles option add command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the roles option add command", ephemeral=True)

    @options.command(
        name="list",
        description="List roles options in a roles panel",
    )
    async def list_options(
            self,
            ctx: ApplicationContext,
            panel_id: int = Option(
                int,
                description="The id of the panel to list the options from",
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            role_panel = await self.bot.db_role_panels.get_roles_panel_by_id(panel_id)

            if role_panel is None:
                await ctx.respond(f"Roles panel with id {panel_id} not found.", ephemeral=True)
                return

            role_options_embed = self.__print_role_options(role_panel.options)

            await ctx.respond(embed=role_options_embed, ephemeral=True)
        except Exception as e:
            logger.error("An error occurred while running the roles option list command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the roles option list command", ephemeral=True)

    @options.command(
        name="edit",
        description="Edit roles option in a roles panel",
    )
    async def edit_options(
            self,
            ctx: ApplicationContext,
            option_id: int = Option(
                int,
                description="The id of the option to edit",
                required=True,
            ),
    ):
        try:
            role_option = await self.bot.db_role_options.get_role_options_by_id(option_id)

            if role_option is None:
                await ctx.respond(f"Roles option with id {option_id} not found.", ephemeral=True)
                return

            panel_option_view = PanelOptionView(
                panel_id=role_option.panel_id,
                bot=self.bot,
                option=role_option,
            )

            await ctx.send_modal(panel_option_view)
        except Exception as e:
            logger.error("An error occurred while running the roles option edit command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the roles option edit command", ephemeral=True)

    @options.command(
        name="delete",
        description="Delete roles option in a roles panel (This is an irreversible action)",
    )
    async def delete_options(
            self,
            ctx: ApplicationContext,
            option_id: int = Option(
                int,
                description="The id of the option to delete",
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            result = await self.bot.db_role_options.delete_role_options(option_id)

            if result:
                await ctx.respond(f"Roles option with id {option_id} deleted successfully.", ephemeral=True)
            else:
                await ctx.respond(f"Roles option with id {option_id} not found.", ephemeral=True)
        except Exception as e:
            logger.error("An error occurred while running the roles option delete command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the roles option delete command", ephemeral=True)

    # General commands

    @roles.command(
        name="preview",
        description="Preview a roles panel",
    )
    async def preview_role_panel(
            self,
            ctx: ApplicationContext,
            panel_id: int = Option(
                int,
                description="The id of the panel to preview",
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            panel = await self.bot.db_role_panels.get_roles_panel_by_id(panel_id)

            if panel is None or panel.deleted_at is not None:
                await ctx.respond(f"Roles panel with id {panel_id} not found.", ephemeral=True)
                return

            if len(panel.options) == 0:
                await ctx.respond(f"Roles panel with id {panel_id} does not have any options.", ephemeral=True)
                return

            panel_embed = self.__create_role_panel_embed(panel, preview=True)

            role_panel_view = RolePanelView(
                panel=panel,
                bot=self.bot,
                preview=True,
            )

            await ctx.respond(embed=panel_embed, view=role_panel_view, ephemeral=True)
        except Exception as e:
            logger.error("An error occurred while running the roles preview command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the roles preview command", ephemeral=True)

    @roles.command(
        name="publish",
        description="Publish a roles panel to a channel",
    )
    async def publish_role_panel(
            self,
            ctx: ApplicationContext,
            panel_id: int = Option(
                int,
                description="The id of the panel to publish",
                required=True,
            ),
            channel: TextChannel | None = Option(
                TextChannel,
                description="The channel to publish the panel to. If not specified, publishes to the current channel.",
                default=None
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            panel = await self.bot.db_role_panels.get_roles_panel_by_id(panel_id)

            if panel is None or panel.deleted_at is not None:
                await ctx.respond(f"Roles panel with id {panel_id} not found.", ephemeral=True)
                return

            if len(panel.options) == 0:
                await ctx.respond(f"Roles panel with id {panel_id} does not have any options.", ephemeral=True)
                return

            panel_embed = self.__create_role_panel_embed(panel)

            role_panel_view = RolePanelView(
                panel=panel,
                bot=self.bot,
            )

            target_channel = channel if channel is not None else ctx.channel

            message = await target_channel.send(embed=panel_embed, view=role_panel_view)

            role_panel_update = RolePanelUpdate(
                id=panel.id,
                channel_id=target_channel.id,
                message_id=message.id,
            )

            await self.bot.db_role_panels.update_roles_panel(role_panel_update)

            await ctx.respond(f"Roles panel published successfully to {target_channel.mention}.", ephemeral=True)
        except Exception as e:
            logger.error("An error occurred while running the publish command: %s", e, exc_info=True)
            await ctx.respond(f"An error occurred while running the roles publish command", ephemeral=True)

    # Methode

    @staticmethod
    async def __print_role_panels(panel: RolePanelSchema, options: list[RoleOptionsSchema],
                                  preview: bool = False) -> Embed:
        panel_embed = Embed(
            title=panel.title if not preview else panel.title + " (Preview)",
            description=panel.description,
            colour=Color.blue(),
            timestamp=datetime.now(UTC),
        )

        if preview and len(options) == 0:
            panel_embed.set_footer(
                text="This is a preview of the role panel. To show roles panel, use the /roles preview command."
            )

        if len(options) == 0:
            panel_embed.add_field(
                name="Multiple Choose",
                value="Yes" if panel.multiple_choose else "No",
                inline=False,
            )
        else:
            for option in options:
                panel_embed.add_field(
                    name=option.label,
                    value=f"Role: <@&{option.role_id}>\n"
                          f"Description: {option.description if option.description else 'No description'}\n"
                          f"Emoji: {option.emoji if option.emoji else 'No emoji'}",
                    inline=False,
                )

        return panel_embed

    @staticmethod
    def __print_role_options(options: list[RoleOptionsSchema]) -> Embed:
        options_embed = Embed(
            title="Role Options",
            colour=Color.green(),
            timestamp=datetime.now(UTC),
        )

        if len(options) == 0:
            options_embed.add_field(
                name="No Options",
                value="There are no role options available.",
                inline=False,
            )
        else:
            for option in options:
                options_embed.add_field(
                    name=option.label,
                    value=f"ID: {option.id}\n"
                          f"Role: <@&{option.role_id}>\n"
                          f"Description: {option.description if option.description else 'No description'}\n"
                          f"Emoji: {option.emoji if option.emoji else 'No emoji'}",
                    inline=False,
                )

        return options_embed

    @staticmethod
    def __create_role_panel_embed(panel: RolePanelSchema, preview: bool = False) -> Embed:
        panel_embed = Embed(
            title=panel.title,
            description=panel.description,
            colour=Color.blue(),
            timestamp=datetime.now(UTC),
        )

        if preview:
            panel_embed.set_footer(
                text="This is a preview of the role panel. No changes have been made."
            )

        return panel_embed
