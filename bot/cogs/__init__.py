from typing import Any, Type

from .moderation import Moderation

ALL_COGS: dict[str, Type[Any]] = {
    "moderation": Moderation,
}
