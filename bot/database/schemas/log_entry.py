from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class LogEntryType(str, Enum):
    # Moderation
    infraction_warn = "INFRACTION_WARN"
    infraction_timeout = "INFRACTION_TIMEOUT"
    infraction_kick = "INFRACTION_KICK"
    infraction_ban = "INFRACTION_BAN"

    # Verification
    verification_manual = "VERIFICATION_MANUAL"

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
