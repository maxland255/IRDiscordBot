from typing import Any, Type

from .moderation import Moderation
from .configuration import Configuration
from .rules import Rules
from .roles import Roles

ALL_COGS: dict[str, Type[Any]] = {
    "moderation": Moderation,
    "configuration": Configuration,
    "rules": Rules,
    "roles": Roles,
}
