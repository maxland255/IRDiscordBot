import os

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

GLOBAL_ENV = os.getenv("APP_ENV", "prod")


class Settings(BaseSettings):
    """
    This class loads the bot settings from the environment or the .env file.
    """

    ENV: str = Field("prod", alias="APP_ENV")

    DISCORD_BOT_TOKEN: SecretStr
    DATABASE_URL: str = ""
    GUILD_ID: int | None = None
    LOG_LEVEL: str = "INFO"

    SMTP_SENDER_EMAIL: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: SecretStr
    SMTP_USE_TLS: bool = True
    SMTP_START_TLS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env" if GLOBAL_ENV == "prod" else ".env.dev",
        env_file_encoding="utf-8"
    )


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()
