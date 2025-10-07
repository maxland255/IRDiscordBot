from enum import Enum


class LogEntryType(str, Enum):
    infraction_warn = "INFRACTION_WARN"
    infraction_timeout = "INFRACTION_TIMEOUT"
    infraction_kick = "INFRACTION_KICK"
    infraction_ban = "INFRACTION_BAN"
