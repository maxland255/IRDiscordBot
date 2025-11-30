import logging

from typing import TYPE_CHECKING

from discord import Cog, SlashCommandGroup, Permissions, InteractionContextType, ApplicationContext, Option, Embed, \
    EmbedField, Color

from .cogs_base import CogsBase

from bot.database.schemas import EmbedsCreate, EmbedsSchema, EmbedFieldsSchema
from bot.view.embeds.edit_embed_view import EditEmbedView
from bot.utils.pagination_view import PaginationView

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class Embeds(Cog, CogsBase):
    def __init__(self, bot: "IRBot"):
        self.bot = bot

    embeds = SlashCommandGroup(
        name="embeds",
        description="Commands to create and manage embeds.",
        default_member_permissions=Permissions(administrator=True),
        contexts={InteractionContextType.guild},
    )

    # Embeds commands

    @embeds.command(
        name="create",
        description="Create a new embed.",
    )
    async def embeds_create(
            self,
            ctx: ApplicationContext,
            title: str = Option(
                str,
                description="The title of the embed.",
            ),
    ):
        try:
            guild_config = await self.bot.db_guilds.get_guild_by_id(ctx.guild_id)

            if guild_config is None:
                await ctx.respond(
                    "An error occurred while trying to process your request. No guild configuration found.",
                    ephemeral=True,
                )
                return

            embed_create = EmbedsCreate(
                guild_id=ctx.guild_id,
                title=title
            )

            embed = await self.bot.db_embeds.create_embeds(embed_create)

            await ctx.respond(
                f"Embed created successfully with ID: {embed.id}",
                embed=self.create_embed(embed, []),
                view=EditEmbedView(self.bot, self, embed, []),
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error creating embed", exc_info=e)
            await ctx.respond(
                "An error occurred while trying to create the embed. Please contact an administrator.",
                ephemeral=True,
            )

    @embeds.command(
        name="edit",
        description="Edit an existing embed.",
    )
    async def embeds_edit(
            self,
            ctx: ApplicationContext,
            embed_id: int = Option(
                int,
                description="The ID of the embed to edit.",
            )
    ):
        try:
            embed = await self.bot.db_embeds.get_specific_embed(embed_id)

            if embed is None or embed.deleted_at is not None:
                await ctx.respond(
                    "Embed not found. Please check the ID and try again.",
                    ephemeral=True,
                )
                return

            embed_field = await self.bot.db_embeds.get_all_embed_fields(embed.id)

            await ctx.respond(
                embed=self.create_embed(embed, embed_field),
                view=EditEmbedView(self.bot, self, embed, embed_field),
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error editing embed", exc_info=e)
            await ctx.respond(
                "An error occurred while trying to edit the embed. Please contact an administrator.",
                ephemeral=True,
            )

    @embeds.command(
        name="delete",
        description="Delete an embed.",
    )
    async def embeds_delete(
            self,
            ctx: ApplicationContext,
            embed_id: int = Option(
                int,
                description="The ID of the embed to delete.",
            )
    ):
        try:
            await ctx.defer(ephemeral=True)

            embed = await self.bot.db_embeds.get_specific_embed(embed_id)

            if embed is None:
                await ctx.respond(
                    "Embed not found. Please check the ID and try again.",
                    ephemeral=True,
                )
                return

            await self.bot.db_embeds.delete_embeds(embed)

            await ctx.respond(
                "Embed deleted successfully.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error deleting embed", exc_info=e)
            await ctx.respond(
                "An error occurred while trying to delete the embed. Please contact an administrator.",
                ephemeral=True,
            )

    @embeds.command(
        name="list",
        description="List all embeds.",
    )
    async def embeds_list(
            self,
            ctx: ApplicationContext,
    ):
        try:
            await ctx.defer(ephemeral=True)

            embeds = await self.bot.db_embeds.get_all_embeds(ctx.guild_id)

            if len(embeds) == 0:
                await ctx.respond(
                    "No embeds found for this server.",
                    ephemeral=True,
                )
                return

            pagination_view = PaginationView(
                data=embeds,
                title="All embeds",
                format_item_func=lambda embed: EmbedField(
                    name=embed.title[:224] + f" (ID: {embed.id})",
                    value=embed.description[:1024] if embed.description is not None else "No description.",
                ),
                embed_color=Color.orange(),
                items_per_page=5,
                mode="fields",
            )

            await ctx.respond(
                embed=pagination_view.create_page_embed(),
                view=pagination_view,
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error listing embeds", exc_info=e)
            await ctx.respond(
                "An error occurred while trying to list the embeds. Please contact an administrator.",
                ephemeral=True,
            )
            return

    @embeds.command(
        name="publish",
        description="Publish an embed.",
    )
    async def embeds_publish(
            self,
            ctx: ApplicationContext,
            embed_id: int = Option(
                int,
                description="The ID of the embed to publish.",
            ),
    ):
        try:
            embed = await self.bot.db_embeds.get_specific_embed(embed_id)

            if embed is None or embed.deleted_at is not None:
                await ctx.respond(
                    "Embed not found. Please check the ID and try again.",
                    ephemeral=True,
                )
                return

            embed_field = await self.bot.db_embeds.get_all_embed_fields(embed.id)

            discord_embed = self.create_embed(embed, embed_field)

            await ctx.channel.send(
                embed=discord_embed,
            )

            await ctx.respond(
                "Embed published successfully.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error publishing embed", exc_info=e)
            await ctx.respond(
                "An error occurred while trying to publish the embed. Please contact an administrator.",
                ephemeral=True,
            )

    # Method

    @staticmethod
    def create_embed(embed: EmbedsSchema, embed_fields: list[EmbedFieldsSchema]) -> Embed:
        discord_embed = Embed(
            title=embed.title,
            description=embed.description,
            color=embed.color,
            timestamp=embed.timestamp,
            url=embed.url,
        )

        if embed.author_name is not None:
            discord_embed.set_author(
                name=embed.author_name,
                url=embed.author_url,
                icon_url=embed.author_icon_url,
            )

        if embed.image_url is not None:
            discord_embed.set_image(url=embed.image_url)

        if embed.thumbnail_url is not None:
            discord_embed.set_thumbnail(url=embed.thumbnail_url)

        if embed.footer_text is not None:
            discord_embed.set_footer(
                text=embed.footer_text,
                icon_url=embed.footer_icon_url,
            )

        for field in embed_fields:
            discord_embed.add_field(
                name=field.name,
                value=field.value,
                inline=field.inline,
            )

        return discord_embed
