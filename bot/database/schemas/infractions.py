from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, UTC

from discord import Color

from typing import Optional

from .gravity_level import GravityLevelSchema
from .log_entry import LogEntryType


class InfractionType(str, Enum):
    warn = "warn"
    timeout = "timeout"
    kick = "kick"
    ban = "ban"

    def get_color(self) -> Color:
        match self:
            case InfractionType.warn:
                return Color.dark_gold()
            case InfractionType.timeout:
                return Color.orange()
            case InfractionType.kick:
                return Color.red()
            case InfractionType.ban:
                return Color.dark_red()


class InfractionResult(str, Enum):
    warn = "warn"
    timeout = "timeout"
    kick = "kick"
    ban = "ban"
    none = "none"

    def to_log_entry_type(self) -> LogEntryType:
        match self:
            case InfractionResult.warn:
                return LogEntryType.infraction_warn
            case InfractionResult.timeout:
                return LogEntryType.infraction_timeout
            case InfractionResult.kick:
                return LogEntryType.infraction_kick
            case InfractionResult.ban:
                return LogEntryType.infraction_ban
            case InfractionResult.none:
                raise ValueError("InfractionResult 'none' cannot be converted to a LogEntryType.")


class InfractionsCreate(BaseModel):
    guild_id: int

    user_id: int
    moderator_id: int

    reason: str

    infraction_type: InfractionType

    gravity_id: int | None

    created_at: datetime = Field(datetime.now(UTC))

    infraction_result: InfractionResult
    timeout_end: datetime | None = Field(None)

    is_active: bool = Field(True)


class InfractionsSchema(BaseModel):
    id: int

    guild_id: int

    user_id: int
    moderator_id: int

    reason: str

    infraction_type: InfractionType

    gravity_id: int | None
    gravity: GravityLevelSchema | None

    created_at: datetime

    infraction_result: InfractionResult
    timeout_end: datetime | None = Field(None)

    is_active: bool

    deleted_at: datetime | None = Field(None)

    class Config:
        from_attributes = True


class InfractionsUpdate(BaseModel):
    id: int

    reason: Optional[str] = Field(None)

    infraction_type: Optional[InfractionType] = Field(None)

    gravity_id: Optional[int] = Field(None)
    gravity: Optional[GravityLevelSchema] = Field(None)

    infraction_result: Optional[InfractionResult] = Field(None)
    timeout_end: Optional[datetime] = Field(None)

    is_active: Optional[bool] = Field(None)

    deleted_at: datetime | None = Field(None)
