import logging

from typing import TYPE_CHECKING

from discord import InputTextStyle, Interaction
from discord.ui import DesignerModal, Label, InputText

from bot.database.schemas import GuildRulesSchema, GuildRulesCreate, GuildRulesUpdate

if TYPE_CHECKING:
    from bot.main import IRBot
    from bot.cogs.rules import Rules

logger = logging.getLogger(__name__)


class RulesEditModal(DesignerModal):
    def __init__(self, bot: "IRBot", rules_cogs: "Rules", rules: GuildRulesSchema | None = None):
        super().__init__(title="Edit Server Rules")
        self.bot = bot
        self.rules_cogs = rules_cogs
        self.rules = rules

        self.title_input = InputText(
            placeholder="Rules title",
            required=True,
            max_length=256,
            value=self.rules.title if self.rules is not None else "",
        )
        self.title_label = Label(
            label="Rules title",
            item=self.title_input,
        )

        self.text_input = InputText(
            placeholder="Rules description",
            required=True,
            style=InputTextStyle.long,
            max_length=1024,
            value=self.rules.rules if self.rules is not None else "",
        )
        self.text_label = Label(
            label="Rules description",
            item=self.text_input,
        )

        self.add_item(self.title_label)
        self.add_item(self.text_label)

    async def callback(self, interaction: Interaction):
        try:
            if self.rules is None:
                new_rules = GuildRulesCreate(
                    guild_id=interaction.guild_id,
                    title=self.title_input.value,
                    rules=self.text_input.value,
                )

                new_rules = await self.bot.db_guild_rules.create_guild_rules(new_rules)
            else:
                update_guild_rules = GuildRulesUpdate(
                    id=self.rules.id,
                    title=self.title_input.value,
                    rules=self.text_input.value,
                    rules_require_publish=True,
                )

                new_rules = await self.bot.db_guild_rules.update_guild_rules(update_guild_rules)

            rules_embed = await self.rules_cogs.create_rules_embed(interaction.guild, [new_rules], preview=True)

            await interaction.respond(
                f"Rule added/updated to guild {interaction.guild.name}.",
                ephemeral=True,
            )

            for rule_embed in rules_embed:
                await interaction.respond(
                    embed=rule_embed,
                    ephemeral=True,
                )
        except Exception as e:
            logger.error(f"Error while creating/editing guild rules", exc_info=e)
            await interaction.response.send_message(
                "An error occurred while creating/editing the guild rules. Please try again later.",
                ephemeral=True,
            )
