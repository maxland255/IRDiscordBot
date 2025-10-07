from typing import TYPE_CHECKING

from .moderation import ModerationLogger

if TYPE_CHECKING:
    from bot.main import IRBot


class BotLogger:
    def __init__(self, bot: "IRBot"):
        self.moderation = ModerationLogger(bot)
