import logging
import asyncio

from .utils.logging_setup import setup_logging
from .core.config import get_settings
from .database.data.engine import engine, AsyncSession
from .database.models import Base
from .cogs import ALL_COGS
from .loggers import BotLogger
from .view.role_panel_view import RolePanelView
from .view.report_message.report_log_view import ReportLogView

from .database.repositories import SQLAlchemyGuildRepository, SQLAlchemyGravityLevelRepository, \
    SQLAlchemyInfractionsRepository, SQLAlchemyLogsEntryRepository, SQLAlchemyGuildRulesRepository, \
    SQLAlchemyRolePanelRepository, SQLAlchemyRoleOptionsRepository, SQLAlchemyReportRepository

from discord import Bot, Intents

setup_logging()

logger = logging.getLogger("ir-bot")


class IRBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, intents=Intents.all())

        asyncio.run(self._setup_database())

        if self.settings.ENV == "dev":
            logger.warning("Bot is running in development mode.")
            logger.warning("Please ensure that you have set up the environment correctly.")
            logger.warning("See README.md for more information.")

        # Register listeners
        self.add_listener(self._on_ready, "on_ready")

        # Load cogs
        self._load_cogs()

    @staticmethod
    async def _setup_database():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def run(self):
        """
        Start the bot.
        :return:
        """
        super().run(self.settings.DISCORD_BOT_TOKEN)

    def _load_cogs(self):
        logger.info("Loading cogs...")

        for name, cog in ALL_COGS.items():
            logger.info(f"Loading cog: {name}")
            self.add_cog(cog(self))

        logger.info("Cogs loaded.")

    async def load_all_role_panels(self):
        """
        Load all role panels from the database.
        :return:
        """
        try:
            panels = await self.db_role_panels.get_all_active_roles_panel()

            for panel in panels:
                role_panel_view = RolePanelView(
                    panel=panel,
                    bot=self,
                )

                self.add_view(role_panel_view)
        except Exception as e:
            logger.error(f"Error loading role panels: {e}")

    # Global events
    async def _on_ready(self):
        logger.info(f"Bot is ready as {bot.user}")

        await self.load_all_role_panels()
        
        self.add_view(ReportLogView(self))

    # Property
    @property
    def settings(self):
        return get_settings()

    # Bot logger
    @property
    def logger(self):
        return BotLogger(self)

    # Database repository
    @property
    def db_guilds(self):
        return SQLAlchemyGuildRepository(AsyncSession)

    @property
    def db_gravity_levels(self):
        return SQLAlchemyGravityLevelRepository(AsyncSession)

    @property
    def db_infractions(self):
        return SQLAlchemyInfractionsRepository(AsyncSession)

    @property
    def db_logs_entries(self):
        return SQLAlchemyLogsEntryRepository(AsyncSession)

    @property
    def db_guild_rules(self):
        return SQLAlchemyGuildRulesRepository(AsyncSession)

    @property
    def db_role_panels(self):
        return SQLAlchemyRolePanelRepository(AsyncSession)

    @property
    def db_role_options(self):
        return SQLAlchemyRoleOptionsRepository(AsyncSession)

    @property
    def db_reports(self):
        return SQLAlchemyReportRepository(AsyncSession)


bot: IRBot | None = None

if __name__ == "__main__":
    bot = IRBot()

    bot.run()
