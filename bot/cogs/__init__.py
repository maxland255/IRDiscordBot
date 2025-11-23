from typing import Any, Type

from .moderation import Moderation
from .configuration import Configuration
from .rules import Rules
from .roles import Roles
from .report import Report
from .tickets import Tickets
from .tickets_config import TicketsConfig
from .tickets_admin import TicketsAdmin
from .verifications import Verifications

ALL_COGS: dict[str, Type[Any]] = {
    "moderation": Moderation,
    "configuration": Configuration,
    "rules": Rules,
    "roles": Roles,
    "report": Report,
    "tickets": Tickets,
    "tickets_config": TicketsConfig,
    "tickets_admin": TicketsAdmin,
    "verifications": Verifications,
}
