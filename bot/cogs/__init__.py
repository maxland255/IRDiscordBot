from typing import Any, Type

from .moderation import Moderation
from .configuration import Configuration

ALL_COGS: dict[str, Type[Any]] = {
    "moderation": Moderation,
    "configuration": Configuration,
}
