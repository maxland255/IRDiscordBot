import logging

from typing import TYPE_CHECKING, Any, Optional
from pydantic import BaseModel
from datetime import datetime, UTC

from discord import Cog, SlashCommandGroup, Permissions, InteractionContextType, ApplicationContext, Option, Guild, \
    Embed, Color

from bot.database.schemas import GuildSchema, GuildUpdate, GuildRulesCreate, GuildRulesSchema, GuildRulesUpdate
from bot.exception import GuildRuleNotFound
from bot.utils.get_channel import get_channel

from .cogs_base import CogsBase

if TYPE_CHECKING:
    from bot.main import IRBot

logger = logging.getLogger(__name__)


class DiscordRules(BaseModel):
    field_type: str
    label: str
    description: str | None
    automations: Any | None
    required: bool
    values: list[str] | None


class Rules(Cog, CogsBase):
    def __init__(self, bot: "IRBot"):
        self.bot = bot

    rules = SlashCommandGroup(
        name="rules",
        description="Rules commands",
        default_member_permissions=Permissions(administrator=True),
        contexts={InteractionContextType.guild},
    )

    @rules.command(
        name="add",
        description="Add a new rule to the server",
    )
    async def rules_add(
            self,
            ctx: ApplicationContext,
            title: str = Option(
                str,
                max_length=256,
                required=True,
            ),
            rules: str = Option(
                str,
                max_length=1024,
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            guild_config = await self.get_guild_configuration(ctx.guild.id)

            if guild_config is None:
                await ctx.respond(
                    f"Configuration du serveur introuvable, veuillez utiliser la commande `/config init` pour initialiser le bot sur le serveur {ctx.guild.name}."
                )
                return

            new_rules = GuildRulesCreate(
                guild_id=ctx.guild.id,
                title=title,
                rules=rules,
            )

            new_rules = await self.bot.db_guild_rules.create_guild_rules(new_rules)

            rules_embeds = await self.create_rules_embed(ctx.guild, [new_rules], preview=True)

            await ctx.respond(f"Rule added to guild {ctx.guild.name}.", ephemeral=True)

            for embed in rules_embeds:
                await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error adding rule to guild {ctx.guild.name}: {e}", exc_info=True)
            await ctx.respond(f"Error adding rule to guild {ctx.guild.name}", ephemeral=True)

    @rules.command(
        name="edit",
        description="Edit an existing rule in the server",
    )
    async def rules_edit(
            self,
            ctx: ApplicationContext,
            rule_id: int = Option(
                int,
                description="ID of the rule to edit",
                required=True,
            ),
            title: Optional[str] = Option(
                str,
                max_length=256,
            ),
            rules: Optional[str] = Option(
                str,
                max_length=1024,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            update_guild_rules = GuildRulesUpdate(
                id=rule_id,
                rules_require_publish=True,
            )

            if title is not None:
                update_guild_rules.title = title

            if rules is not None:
                update_guild_rules.rules = rules

            try:
                update_guild_rules = await self.bot.db_guild_rules.update_guild_rules(update_guild_rules)
            except GuildRuleNotFound as e:
                logger.exception(e)
                await ctx.respond(f"Error guild rules with id {rule_id} not found.", ephemeral=True)
                return

            rules_embeds = await self.create_rules_embed(ctx.guild, [update_guild_rules], preview=True)

            await ctx.respond(f"Rule {rule_id} edited in guild {ctx.guild.name}.", ephemeral=True)

            for embed in rules_embeds:
                await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error editing rule {rule_id} in guild {ctx.guild.name}: {e}", exc_info=True)
            await ctx.respond(f"Error editing rule {rule_id} in guild {ctx.guild.name}", ephemeral=True)

    @rules.command(
        name="delete",
        description="Delete an existing rule in the server",
    )
    async def rules_delete(
            self,
            ctx: ApplicationContext,
            rule_id: int = Option(
                int,
                description="ID of the rule to delete",
                required=True,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            result = await self.bot.db_guild_rules.delete_guild_rules(rule_id)

            if result:
                await ctx.respond(f"Rule {rule_id} deleted from guild {ctx.guild.name}.", ephemeral=True)
            else:
                await ctx.respond(f"Error guild rules with id {rule_id} not found.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error deleting rule {rule_id} in guild {ctx.guild.name}: {e}", exc_info=True)
            await ctx.respond(f"Error deleting rule {rule_id} in guild {ctx.guild.name}", ephemeral=True)

    @rules.command(
        name="preview",
        description="Preview the rules for the server",
    )
    async def rules_preview(
            self,
            ctx: ApplicationContext,
            with_id: bool = Option(
                bool,
                description="True = include rule ID in the preview",
                default=False,
            )
    ):
        try:
            await ctx.defer(ephemeral=True)

            guild_rules = await self.bot.db_guild_rules.get_guild_rules(ctx.guild.id)

            if len(guild_rules) == 0:
                await ctx.respond(f"No rules found for guild {ctx.guild.name}.", ephemeral=True)
                return

            rules_embeds = await self.create_rules_embed(ctx.guild, guild_rules, preview=True, with_id=with_id)

            for embed in rules_embeds:
                await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error previewing rules for guild {ctx.guild.name}: {e}", exc_info=True)
            await ctx.respond(f"Error previewing rules for guild {ctx.guild.name}", ephemeral=True)

    @rules.command(
        name="publish",
        description="Publish the rules to the server",
    )
    async def rules_publish(
            self,
            ctx: ApplicationContext,
            force_update: bool = Option(
                bool,
                description="Force update the rules even if they are already published",
                default=False,
            ),
    ):
        try:
            await ctx.defer(ephemeral=True)

            guild_config = await self.get_guild_configuration(ctx.guild.id)

            if guild_config is None:
                await ctx.respond(
                    f"Configuration du serveur introuvable, veuillez utiliser la commande `/config init` pour initialiser le bot sur le serveur {ctx.guild.name}."
                )
                return

            if guild_config.rules_channel_id is None:
                await ctx.respond(
                    f"No rules channel set for guild {ctx.guild.name}. Please set a rules channel using `/config configure` command.",
                    ephemeral=True)
                return

            if not force_update and not await self.bot.db_guild_rules.guild_rules_require_publish(ctx.guild.id):
                await ctx.respond(
                    f"Rules are already published for guild {ctx.guild.name}.",
                    ephemeral=True,
                )
                return

            rules_channel = await get_channel(ctx.guild, guild_config.rules_channel_id)

            # Remove all current rules
            if guild_config.rules_message_id is not None:
                for rule_message_id in guild_config.rules_message_id:
                    message = await rules_channel.fetch_message(rule_message_id)

                    if message is not None:
                        await message.delete(reason="Rules published")

            guild_rules = await self.bot.db_guild_rules.get_guild_rules(ctx.guild.id)

            rules_embeds = await self.create_rules_embed(ctx.guild, guild_rules)

            # Publish rules to the rule channel
            new_message_ids = []

            for embed in rules_embeds:
                message = await rules_channel.send(embed=embed)
                new_message_ids.append(message.id)

            # Mark rules as published

            for rule in guild_rules:
                update_guild_rules = GuildRulesUpdate(
                    id=rule.id,
                    rules_require_publish=False,
                )

                await self.bot.db_guild_rules.update_guild_rules(update_guild_rules)

            # Update guild config with new rules message IDs
            update_guild_config = GuildUpdate(
                id=ctx.guild.id,
                name=ctx.guild.name,
                rules_message_id=new_message_ids,
            )

            await self.bot.db_guilds.update_guild(update_guild_config)

            await ctx.respond(f"Rules published to guild {ctx.guild.name} in rules channel {rules_channel.mention}.",
                              ephemeral=True)
        except Exception as e:
            logger.error(f"Error publishing rules for guild {ctx.guild.name}: {e}", exc_info=True)
            await ctx.respond(f"Error publishing rules for guild {ctx.guild.name}", ephemeral=True)

    # Methode
    async def get_guild_configuration(self, guild_id: int) -> GuildSchema | None:
        try:
            guild_config = await self.bot.db_guilds.get_guild_by_id(guild_id)

            return guild_config
        except Exception as e:
            logger.error(f"Error checking guild configuration for guild {guild_id}: {e}", exc_info=True)
            return None

    @staticmethod
    async def create_rules_embed(guild: Guild, rules: list[GuildRulesSchema], preview: bool = False,
                                 with_id: bool = False) -> list[Embed]:
        rules_embeds: list[Embed] = []

        rules_embed = Embed(
            title=f"Rules for {guild.name}" if not preview else f"Rules preview for {guild.name}",
            description="Please read these rules carefully before participating in this server."
                        " If you do not agree with any of these rules, you will be kicked.",
            colour=Color.green(),
            timestamp=datetime.now(UTC),
        )
        rules_number = 0

        for rule in rules:
            if rules_number > 25:
                rules_embeds.append(rules_embed)
                rules_embed = Embed(
                    colour=Color.green(),
                )
                rules_number = 0

            rules_number += 1

            rules_embed.add_field(
                name=(
                         rule.title if not with_id else f"{rule.id}: {rule.title}") + (
                         " (Not published)" if preview and rule.rules_require_publish else ""),
                value=rule.rules,
                inline=False,
            )

        rules_embeds.append(rules_embed)

        if preview:
            rules_embeds[-1].set_footer(
                text="Warning: this is a preview of the rules. It's possible that it's incomplete."
            )

        return rules_embeds

    # @Cog.listener()
    # async def on_guild_update(self, _: Guild, after: Guild):
    #     try:
    #         if self.disable_rules_updates:
    #             logger.critical("Rules updates are disabled. Please check logs for more information.")
    #             return
    #
    #         all_rules: set[str] = set()
    #
    #         new_rules = await self.fetch_rules_from_undocumented_api(after.id)
    #
    #         if new_rules is None:
    #             return
    #
    #         for rule in new_rules:
    #             if rule.field_type == "TERMS":
    #                 for value in rule.values:
    #                     all_rules.add(value)
    #
    #         await self.send_rules_to_guild(after, list(all_rules))
    #     except Exception as e:
    #         logger.error(f"Error updating rules for guild {after.id}: {e}", exc_info=True)
