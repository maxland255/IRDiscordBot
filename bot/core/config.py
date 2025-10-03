import os

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

GLOBAL_ENV = os.getenv("ENV", "prod")


class Settings(BaseSettings):
    """
    This class loads the bot settings from the environment or the .env file.
    """

    ENV: str = "prod"

    DISCORD_BOT_TOKEN: str = ""
    DATABASE_URL: str = ""
    DATABASE_USER: str | None = None
    DATABASE_PASSWORD: str | None = None
    DATABASE_NAME: str | None = None

    GUILD_ID: int | None = None
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env" if GLOBAL_ENV == "prod" else ".env.dev",
        env_file_encoding="utf-8"
    )


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()
