import logging

from discord import Cog, SlashCommandGroup, Permissions, InteractionContextType, ApplicationContext, TextChannel, \
    Option, ChannelType, Embed, Color, Guild

from bot.database.schemas import GuildSchema, GuildUpdate, GravityLevelCreate, GravityLevelSchema, GravityLevelUpdate
from bot.utils.get_channel import get_channel

from typing import TYPE_CHECKING, Optional

from bot.exception import GuildNotFound, GravityLevelNotFound

if TYPE_CHECKING:
    from bot.main import IRBot


class Configuration(Cog):
    def __init__(self, bot: "IRBot"):
        self.bot = bot

    logger = logging.getLogger(__name__)

    configuration = SlashCommandGroup(
        name="config",
        description="Configuration commands",
        default_member_permissions=Permissions(administrator=True),
        contexts={InteractionContextType.guild},
    )

    gravity_levels = configuration.create_subgroup(
        name="gravity-levels",
        description="Manage infractions gravity levels",
    )

    @configuration.command(
        name="init",
        description="Initialise the guild configuration",
    )
    async def init(
            self,
            ctx: ApplicationContext,
            warn_height: float = Option(
                float,
                name="warn-height",
                default=0.2,
                min_value=0.1,
                max_value=1.0,
            ),
            default_timeout: int = Option(
                int,
                name="default-timeout",
                description="Default timeout in seconds",
                default=600,
                min_value=60,
                max_value=1800,
            ),
            logs_moderation: Optional[TextChannel] = Option(
                TextChannel,
                channel_types=ChannelType.text,
            ),
            logs_server: Optional[TextChannel] = Option(
                TextChannel,
                channel_types=ChannelType.text,
            ),
            rules_channel: Optional[TextChannel] = Option(
                TextChannel,
                channel_types=ChannelType.text,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            guild = await self.bot.db_guilds.get_guild_by_id(ctx.guild.id)

            if guild is not None:
                await ctx.respond(
                    f"La configuration initial du bot pour le serveur {ctx.guild.name} est déjà configuré\n\n*Veuillez utiliser la commande `/config configure` pour modifier les configurations du serveur.*"
                )
                return

            new_guild_schema = GuildSchema(
                id=ctx.guild.id,
                name=ctx.guild.name,
                warn_height=warn_height,
                default_timeout=default_timeout,
                logs_moderation=logs_moderation.id if logs_moderation is not None else None,
                logs_server=logs_server.id if logs_server is not None else None,
                rules_channel_id=rules_channel.id if rules_channel is not None else None,
                rules_message_id=None,
            )

            new_guild = await self.bot.db_guilds.create_guild(new_guild_schema)

            guild_config_embed = await self.print_configuration(ctx.guild, new_guild)

            await ctx.respond(embed=guild_config_embed)
        except Exception as e:
            self.logger.exception(e)
            await ctx.respond("An error occurred", ephemeral=True)

    @configuration.command(
        name="configure",
        description="Modifier les configurations du serveur",
    )
    async def configure(
            self,
            ctx: ApplicationContext,
            warn_height: Optional[float] = Option(
                float,
                name="warn-height",
                min_value=0.1,
                max_value=1.0,
            ),
            default_timeout: Optional[int] = Option(
                int,
                name="default-timeout",
                description="Default timeout in seconds",
                min_value=60,
                max_value=1800,
            ),
            logs_moderation: Optional[TextChannel] = Option(
                TextChannel,
                channel_types=ChannelType.text,
            ),
            logs_server: Optional[TextChannel] = Option(
                TextChannel,
                channel_types=ChannelType.text,
            ),
            rules_channel: Optional[TextChannel] = Option(
                TextChannel,
                channel_types=ChannelType.text,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            updated_guild = GuildUpdate(
                id=ctx.guild.id,
                name=ctx.guild.name,
            )

            if warn_height is not None:
                updated_guild.warn_height = warn_height

            if default_timeout is not None:
                updated_guild.default_timeout = default_timeout

            if logs_moderation is not None:
                updated_guild.logs_moderation = logs_moderation.id

            if logs_server is not None:
                updated_guild.logs_server = logs_server.id

            if rules_channel is not None:
                updated_guild.rules_channel_id = rules_channel.id

            try:
                updated_guild = await self.bot.db_guilds.update_guild(updated_guild)
            except GuildNotFound as e:
                self.logger.exception(e)
                await ctx.respond(
                    f"Configuration du serveur introuvable, veuillez utiliser la commande `/config init` pour initialiser le bot sur le serveur {ctx.guild.name}."
                )
                return

            await ctx.respond(embed=await self.print_configuration(ctx.guild, updated_guild))
        except Exception as e:
            self.logger.exception(e)
            await ctx.respond("An error occurred", ephemeral=True)

    @configuration.command(
        name="unconfigure",
        description="Supprime une ou plusieurs configurations du serveur",
    )
    async def unconfigure(
            self,
            ctx: ApplicationContext,
            logs_moderation: bool = Option(
                bool,
                description="True = supprime la configuration",
                default=False,
            ),
            logs_server: bool = Option(
                bool,
                description="True = supprime la configuration",
                default=False,
            ),
            rules_channel: bool = Option(
                bool,
                description="True = supprime la configuration",
                default=False,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            updated_guild = GuildUpdate(
                id=ctx.guild.id,
                name=ctx.guild.name,
            )

            if logs_moderation:
                updated_guild.logs_moderation = None

            if logs_server:
                updated_guild.logs_server = None

            if rules_channel:
                updated_guild.rules_channel_id = None

            try:
                updated_guild = await self.bot.db_guilds.update_guild(updated_guild)
            except GuildNotFound as e:
                self.logger.exception(e)
                await ctx.respond(
                    f"Configuration du serveur introuvable, veuillez utiliser la commande `/config init` pour initialiser le bot sur le serveur {ctx.guild.name}."
                )
                return

            await ctx.respond(embed=await self.print_configuration(ctx.guild, updated_guild))
        except Exception as e:
            self.logger.exception(e)
            await ctx.respond("An error occurred", ephemeral=True)

    @configuration.command(
        name="view",
        description="Visualise la configuration du serveur",
    )
    async def view(self, ctx: ApplicationContext):
        try:
            await ctx.defer(ephemeral=True)

            guild_config = await self.bot.db_guilds.get_guild_by_id(ctx.guild.id)

            if guild_config is None:
                await ctx.respond(
                    f"Configuration du serveur introuvable, veuillez utiliser la commande `/config init` pour initialiser le bot sur le serveur {ctx.guild.name}."
                )
                return

            await ctx.respond(embed=await self.print_configuration(ctx.guild, guild_config))
        except Exception as e:
            self.logger.exception(e)
            await ctx.respond("An error occurred", ephemeral=True)

    # Infractions configurations

    @gravity_levels.command(
        name="create",
        description="Create a new gravity level",
    )
    async def gravity_levels_create(
            self,
            ctx: ApplicationContext,
            name: str = Option(
                str,
                max_length=25,
                required=True,
            ),
            description: str = Option(
                str,
                max_length=100,
                default="",
            ),
            weight: float = Option(
                float,
                min_value=0.1,
                max_value=10.0,
                default=1.0,
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            if not await self.check_guild_configuration_exist(ctx.guild):
                await ctx.respond(
                    f"Configuration du serveur introuvable, veuillez utiliser la commande `/config init` pour initialiser le bot sur le serveur {ctx.guild.name}."
                )
                return

            new_gravity_level = GravityLevelCreate(
                guild_id=ctx.guild.id,
                name=name,
                description=description,
                weight=weight,
            )

            created_gravity_level = await self.bot.db_gravity_levels.create_gravity_level(new_gravity_level)

            await ctx.respond(embed=await self.print_gravity_levels_configuration(ctx.guild, [created_gravity_level]))
        except Exception as e:
            self.logger.exception(e)
            await ctx.respond("An error occurred", ephemeral=True)

    @gravity_levels.command(
        name="view",
        description="View all gravity levels for the guild",
    )
    async def gravity_levels_view(self, ctx: ApplicationContext):
        try:
            await ctx.defer(ephemeral=True)

            if not await self.check_guild_configuration_exist(ctx.guild):
                await ctx.respond(
                    f"Configuration du serveur introuvable, veuillez utiliser la commande `/config init` pour initialiser le bot sur le serveur {ctx.guild.name}."
                )
                return

            gravity_levels = await self.bot.db_gravity_levels.get_all_gravity_level(guild_id=ctx.guild.id)

            if len(gravity_levels) == 0:
                await ctx.respond("No gravity levels found for this guild.", ephemeral=True)
                return

            await ctx.respond(embed=await self.print_gravity_levels_configuration(ctx.guild, gravity_levels))
        except Exception as e:
            self.logger.exception(e)
            await ctx.respond("An error occurred", ephemeral=True)

    @gravity_levels.command(
        name="delete",
        description="Delete all gravity levels for the guild",
    )
    async def gravity_levels_delete(
            self,
            ctx: ApplicationContext,
            gravity_level_id: int = Option(
                int,
                name="gravity-level-id",
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            if not await self.check_guild_configuration_exist(ctx.guild):
                await ctx.respond(
                    f"Configuration du serveur introuvable, veuillez utiliser la commande `/config init` pour initialiser le bot sur le serveur {ctx.guild.name}."
                )
                return

            await self.bot.db_gravity_levels.delete_gravity_level_by_id(gravity_level_id)

            await ctx.respond(f"Gravity level with ID {gravity_level_id} has been deleted.", ephemeral=True)
        except Exception as e:
            self.logger.exception(e)
            await ctx.respond("An error occurred", ephemeral=True)

    @gravity_levels.command(
        name="update",
        description="Update all gravity levels for the guild",
    )
    async def gravity_levels_update(
            self,
            ctx: ApplicationContext,
            gravity_level_id: int = Option(
                int,
                name="gravity-level-id",
                required=True,
            ),
            name: Optional[str] = Option(
                str,
                max_length=25,
            ),
            description: Optional[str] = Option(
                str,
                max_length=100,
            ),
            weight: Optional[float] = Option(
                float,
                min_value=0.1,
                max_value=10.0,
                default=1.0,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            if not await self.check_guild_configuration_exist(ctx.guild):
                await ctx.respond(
                    f"Configuration du serveur introuvable, veuillez utiliser la commande `/config init` pour initialiser le bot sur le serveur {ctx.guild.name}."
                )
                return

            updated_gravity_level = GravityLevelUpdate(
                id=gravity_level_id,
            )

            if name is not None:
                updated_gravity_level.name = name

            if description is not None:
                updated_gravity_level.description = description

            if weight is not None:
                updated_gravity_level.weight = weight

            try:
                updated_gravity_level = await self.bot.db_gravity_levels.update_gravity_level(updated_gravity_level)
            except GravityLevelNotFound as e:
                self.logger.exception(e)
                await ctx.respond(
                    f"Gravity level with ID {gravity_level_id} not found.",
                    ephemeral=True,
                )
                return

            await ctx.respond(embed=await self.print_gravity_levels_configuration(ctx.guild, [updated_gravity_level]))
        except Exception as e:
            self.logger.exception(e)
            await ctx.respond("An error occurred", ephemeral=True)

    # Methode
    @staticmethod
    async def print_configuration(guild: Guild, guild_config: GuildUpdate | GuildSchema) -> Embed:
        assert isinstance(guild_config, GuildSchema)
        assert isinstance(guild, Guild)

        guild_config_embed = Embed(
            title=f"{guild_config.name} configuration",
            color=Color.dark_blue(),
        )

        guild_config_embed.add_field(
            name="Warn height",
            value=str(guild_config.warn_height),
            inline=False,
        )

        guild_config_embed.add_field(
            name="Default timeout",
            value=f"{guild_config.default_timeout} seconds",
            inline=False,
        )

        logs_moderation = await get_channel(guild, guild_config.logs_moderation)

        guild_config_embed.add_field(
            name="Logs moderation",
            value=logs_moderation.mention if logs_moderation is not None else "Not configured",
            inline=False,
        )

        logs_server = await get_channel(guild, guild_config.logs_server)

        guild_config_embed.add_field(
            name="Logs server",
            value=logs_server.mention if logs_server is not None else "Not configured",
            inline=False,
        )

        rules_channel = await get_channel(guild, guild_config.rules_channel_id)

        guild_config_embed.add_field(
            name="Rules channel",
            value=rules_channel.mention if rules_channel is not None else "Not configured",
            inline=False,
        )

        return guild_config_embed

    async def print_gravity_levels_configuration(self, guild: Guild, gravity_levels: list[GravityLevelSchema]) -> Embed:
        gravity_levels_config_embed = Embed(
            title=f"Gravity levels configuration for {guild.name}",
            color=Color.dark_red(),
        )

        gravity_levels_num = 0

        for gravity_level in gravity_levels:
            gravity_levels_num += 1

            gravity_levels_config_embed.add_field(
                name=f"Gravity level {gravity_level.name}",
                value=f"""ID: {gravity_level.id}
Description: {gravity_level.description}
Weight: {gravity_level.weight}""",
                inline=False,
            )

            if gravity_levels_num >= 25:
                self.logger.error(f"Gravity level {gravity_level.name} is too high for serveur {guild.id}")
                gravity_levels_config_embed.description = "Too many gravity levels to display, please use the website to view all gravity levels."
                break

        return gravity_levels_config_embed

    async def check_guild_configuration_exist(self, guild: Guild) -> bool:
        try:
            guild_config = await self.bot.db_guilds.get_guild_by_id(guild.id, raise_if_not_found=True)
            return True if guild_config is not None else False
        except GuildNotFound:
            return False
