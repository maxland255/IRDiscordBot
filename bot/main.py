import logging

from .utils.logging_setup import setup_logging
from .core.config import get_settings
from .database.data.engine import init_db
from .database.models import Base
from .cogs import ALL_COGS
from .loggers import BotLogger
from .view.role_panel_view import RolePanelView
from .view.report_message.report_log_view import ReportLogView
from .cogs.cogs_base import CogsBase
from .exception import CogInitializationError, CriticalCogInitializationError, NonCriticalCogInitializationError
from .view.tickets import TicketPanelView, TicketManagePanelView
from .view.verifications.verification_choose_view import VerificationChooseView
from .view.verifications.ticket_verif_result_panel_view import TicketVerifResultPanelView
from .services.mailer import VerificationMailer

from .database.repositories import GuildRepository, GravityLevelRepository, InfractionsRepository, LogsEntryRepository, \
    GuildRulesRepository, RolePanelRepository, RoleOptionsRepository, ReportRepository, TicketsRepository, \
    TicketMessageRepository, TicketPanelRepository, TicketTypeRepository, VerificationsRepository, EmbedsRepository
from .database.repositories import SQLAlchemyGuildRepository, SQLAlchemyGravityLevelRepository, \
    SQLAlchemyInfractionsRepository, SQLAlchemyLogsEntryRepository, SQLAlchemyGuildRulesRepository, \
    SQLAlchemyRolePanelRepository, SQLAlchemyRoleOptionsRepository, SQLAlchemyReportRepository, \
    SQLAlchemyTicketsRepository, SQLAlchemyTicketMessageRepository, SQLAlchemyTicketPanelRepository, \
    SQLAlchemyTicketTypeRepository, SQLAlchemyVerificationsRepository, SQLAlchemyEmbedsRepository

from discord import Bot, Intents
from sqlalchemy.ext.asyncio import AsyncEngine

setup_logging()

logger = logging.getLogger("ir-bot")


class IRBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, intents=Intents.all())

        self._has_init = False

        self._engine: AsyncEngine | None = None
        self._AsyncSession = None

        if self.settings.ENV == "dev":
            logger.warning("Bot is running in development mode.")
            logger.warning("Please ensure that you have set up the environment correctly.")
            logger.warning("See README.md for more information.")

        # Register global listeners
        self.add_listener(self._on_ready, "on_ready")

        # Load cogs
        self._load_cogs()

        # Services
        self._verification_mail_service: VerificationMailer = VerificationMailer()

    async def _setup_database(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def run(self):
        """
        Start the bot.
        :return:
        """
        super().run(self.settings.DISCORD_BOT_TOKEN.get_secret_value())

    async def close(self) -> None:
        await self._send_shutdown_message()

        await self._engine.dispose()

        logger.info(f"Shutting down bot...")

        await super().close()

    async def _send_shutdown_message(self) -> None:
        """
        Send a shutdown message to the log channel if configured.
        :return:
        """
        guild = await self.db_guilds.get_all_guilds()

        for g in guild:
            if g.logs_server is not None:
                channel = self.get_channel(g.logs_server)
                if channel is not None:
                    await channel.send(f"⚠️ {self.user.mention} ({self.user.display_name}) Bot is shutting down...")

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

    async def load_services(self):
        """
        Load bot services.
        :return:
        """
        pass

    # Global events
    async def _on_ready(self):
        logger.info(f"Bot is ready as {bot.user}")

        if not self._has_init:
            self._has_init = True

            self._engine, self._AsyncSession = await init_db()

            await self._setup_database()

            await self.init_all_cogs()

            # Load role panels views
            await self.load_all_role_panels()

            # Load persistent views
            self.add_view(ReportLogView(self))
            self.add_view(TicketPanelView(self))
            self.add_view(TicketManagePanelView(self))
            self.add_view(VerificationChooseView(self))
            self.add_view(TicketVerifResultPanelView(self))

            # Load Bot services
            await self.load_services()

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
    def db_guilds(self) -> GuildRepository:
        return SQLAlchemyGuildRepository(self._AsyncSession)

    @property
    def db_gravity_levels(self) -> GravityLevelRepository:
        return SQLAlchemyGravityLevelRepository(self._AsyncSession)

    @property
    def db_infractions(self) -> InfractionsRepository:
        return SQLAlchemyInfractionsRepository(self._AsyncSession)

    @property
    def db_logs_entries(self) -> LogsEntryRepository:
        return SQLAlchemyLogsEntryRepository(self._AsyncSession)

    @property
    def db_guild_rules(self) -> GuildRulesRepository:
        return SQLAlchemyGuildRulesRepository(self._AsyncSession)

    @property
    def db_role_panels(self) -> RolePanelRepository:
        return SQLAlchemyRolePanelRepository(self._AsyncSession)

    @property
    def db_role_options(self) -> RoleOptionsRepository:
        return SQLAlchemyRoleOptionsRepository(self._AsyncSession)

    @property
    def db_reports(self) -> ReportRepository:
        return SQLAlchemyReportRepository(self._AsyncSession)

    @property
    def db_ticket_type(self) -> TicketTypeRepository:
        return SQLAlchemyTicketTypeRepository(self._AsyncSession)

    @property
    def db_ticket_panel(self) -> TicketPanelRepository:
        return SQLAlchemyTicketPanelRepository(self._AsyncSession)

    @property
    def db_tickets(self) -> TicketsRepository:
        return SQLAlchemyTicketsRepository(self._AsyncSession)

    @property
    def db_ticket_messages(self) -> TicketMessageRepository:
        return SQLAlchemyTicketMessageRepository(self._AsyncSession)

    @property
    def db_verifications(self) -> VerificationsRepository:
        return SQLAlchemyVerificationsRepository(self._AsyncSession)

    @property
    def db_embeds(self) -> EmbedsRepository:
        return SQLAlchemyEmbedsRepository(self._AsyncSession)

    # Services property
    @property
    def verification_mail_service(self):
        return self._verification_mail_service


bot: IRBot | None = None

if __name__ == "__main__":
    bot = IRBot()

    bot.run()
