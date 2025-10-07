import logging

from typing import TYPE_CHECKING, Any
from pydantic import BaseModel
from datetime import datetime, UTC

from discord import Cog, Guild, Route, HTTPException, Embed

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


class Rules(Cog):
    def __init__(self, bot: "IRBot"):
        self.bot = bot

        # Disable rules updates if an error occurs during the update process.
        # This prevents the bot from spaming the undocumented API if it is down or if the api changes.
        self.disable_rules_updates = False

    @Cog.listener()
    async def on_guild_update(self, _: Guild, after: Guild):
        try:
            if self.disable_rules_updates:
                logger.critical("Rules updates are disabled. Please check logs for more information.")
                return

            all_rules: set[str] = set()

            new_rules = await self.fetch_rules_from_undocumented_api(after.id)

            if new_rules is None:
                return

            for rule in new_rules:
                if rule.field_type == "TERMS":
                    for value in rule.values:
                        all_rules.add(value)

            await self.send_rules_to_guild(after, list(all_rules))
        except Exception as e:
            logger.error(f"Error updating rules for guild {after.id}: {e}", exc_info=True)

    async def send_rules_to_guild(self, guild: Guild, rules: list[str]) -> None:
        rules_channel = guild.rules_channel

        if rules_channel is None:
            logger.info(f"Rules channel not found for guild {guild.id}.")
            return

        if isinstance(rules_channel, int):
            rules_channel = await guild.fetch_channel(rules_channel)

            if rules_channel is None:
                logger.info(f"Rules channel not found for guild {guild.id}.")
                return

        rules_embed = self.create_rules_embed(guild, rules)

        await rules_channel.send(embed=rules_embed)

    @staticmethod
    def create_rules_embed(guild: Guild, rules: list[str]) -> Embed:
        rules_number = 0

        new_rules_embed = Embed(
            title=f"Rules for {guild.name}",
            description="Please read these rules carefully before participating in this server."
                        " If you do not agree with any of these rules, you will be kicked.",
            color=0x00FF00,
            timestamp=datetime.now(UTC),
        )

        for rule in rules:
            rules_number += 1

            new_rules_embed.add_field(
                name=f"{rules_number}:",
                value=rule,
                inline=False,
            )

        return new_rules_embed

    async def fetch_rules_from_undocumented_api(self, guild_id: int) -> list[DiscordRules] | None:
        try:
            route = Route(
                "GET",
                "/guilds/{guild_id}/member-verification?with_guild=false",
                guild_id=guild_id,
            )

            data = await self.bot.http.request(route)

            form_fields = data.get("form_fields", [])

            fields: list[DiscordRules] = [DiscordRules(**field) for field in form_fields]

            return fields
        except HTTPException as e:
            logger.critical(f"Error fetching rules from undocumented API: {e}", exc_info=True)
            logger.critical("Disabling rules updates.")
            self.disable_rules_updates = True
            return None
        except Exception as e:
            logger.critical(f"Error fetching rules from undocumented API: {e}", exc_info=True)
            logger.critical("Disabling rules updates.")
            self.disable_rules_updates = True
            return None
