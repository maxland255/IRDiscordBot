import logging
import asyncio

from .utils.logging_setup import setup_logging
from .core.config import get_settings
from .database.data.engine import engine
from .database.models import Base
from .cogs import ALL_COGS

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

    # Global events
    @staticmethod
    async def _on_ready():
        logger.info(f"Bot is ready as {bot.user}")

    # Property
    @property
    def settings(self):
        return get_settings()


bot: IRBot | None = None

if __name__ == "__main__":
    bot = IRBot()

    bot.run()
