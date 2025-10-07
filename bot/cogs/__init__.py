from typing import Any, Type

from .moderation import Moderation
from .configuration import Configuration
from .rules import Rules

ALL_COGS: dict[str, Type[Any]] = {
    "moderation": Moderation,
    "configuration": Configuration,
    "rules": Rules,
}
