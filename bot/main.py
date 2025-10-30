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
from .cogs.cogs_base import CogsBase
from .exception import CogInitializationError, CriticalCogInitializationError, NonCriticalCogInitializationError
from .view.tickets import TicketPanelView
from .view.tickets import TicketManagePanelView

from .database.repositories import SQLAlchemyGuildRepository, SQLAlchemyGravityLevelRepository, \
    SQLAlchemyInfractionsRepository, SQLAlchemyLogsEntryRepository, SQLAlchemyGuildRulesRepository, \
    SQLAlchemyRolePanelRepository, SQLAlchemyRoleOptionsRepository, SQLAlchemyReportRepository, \
    SQLAlchemyTicketsRepository, SQLAlchemyTicketMessageRepository, SQLAlchemyTicketPanelRepository, \
    SQLAlchemyTicketTypeRepository

from discord import Bot, Intents

setup_logging()

logger = logging.getLogger("ir-bot")


class IRBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, intents=Intents.all())

        self._has_init = False

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

    async def init_all_cogs(self):
        """
        Run the initialize method for all cogs.
        :return:
        """
        logger.info("Initializing cogs...")

        for name, cog in self.cogs.items():
            cog: CogsBase
            if issubclass(cog.__class__, CogsBase):
                logger.info(f"Initializing cog: {name}")
                try:
                    await cog.initialize()
                except NonCriticalCogInitializationError as e:
                    logger.error(f"NON CRITICAL ERROR bot will work in degraded mode: Error initializing cog: {e}",
                                 exc_info=e)
                except CriticalCogInitializationError as e:
                    logger.critical(f"CRITICAL ERROR: Error initializing cog: {e}", exc_info=e)
                    await self.close()
                    exit(1)
                except CogInitializationError as e:
                    logger.error(f"Cog initialization error: {e}", exc_info=e)
                    await self.close()
                    exit(1)
                except Exception as e:
                    logger.exception(f"Error initializing cog: {e}", exc_info=e)
                    await self.close()
                    exit(1)

    # Global events
    async def _on_ready(self):
        logger.info(f"Bot is ready as {bot.user}")

        if not self._has_init:
            self._has_init = True
            await self.init_all_cogs()

            # Load role panels views
            await self.load_all_role_panels()

            # Load persistent views
            self.add_view(ReportLogView(self))
            self.add_view(TicketPanelView(self))
            self.add_view(TicketManagePanelView(self))

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

    @property
    def db_ticket_type(self):
        return SQLAlchemyTicketTypeRepository(AsyncSession)

    @property
    def db_ticket_panel(self):
        return SQLAlchemyTicketPanelRepository(AsyncSession)

    @property
    def db_tickets(self):
        return SQLAlchemyTicketsRepository(AsyncSession)

    @property
    def db_ticket_messages(self):
        return SQLAlchemyTicketMessageRepository(AsyncSession)


bot: IRBot | None = None

if __name__ == "__main__":
    bot = IRBot()

    bot.run()
