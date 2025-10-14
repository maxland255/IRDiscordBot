from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class LogEntryType(str, Enum):
    infraction_warn = "INFRACTION_WARN"
    infraction_timeout = "INFRACTION_TIMEOUT"
    infraction_kick = "INFRACTION_KICK"
    infraction_ban = "INFRACTION_BAN"
    unknown = "UNKNOWN"


class LogEntryCreate(BaseModel):
    guild_id: int
    log_type: LogEntryType

    actor_id: int
    target_id: int

    details: Optional[dict] = Field(None)

    created_at: datetime


class LogEntrySchema(BaseModel):
    id: int

    guild_id: int
    log_type: LogEntryType

    actor_id: int
    target_id: int

    details: Optional[dict] = Field(None)

    created_at: datetime

    class Config:
        from_attributes = True
