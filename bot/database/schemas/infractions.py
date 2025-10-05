from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

from typing import Optional

from .gravity_level import GravityLevelSchema


class InfractionType(str, Enum):
    warn = "warn"
    timeout = "timeout"
    kick = "kick"
    ban = "ban"


class InfractionsCreate(BaseModel):
    user_id: int
    moderator_id: int

    reason: str

    infraction_type: InfractionType

    gravity_id: int
    gravity: GravityLevelSchema

    created_at: datetime

    timeout_end: datetime | None = Field(None)

    is_active: bool


class InfractionsSchema(BaseModel):
    id: int
    user_id: int
    moderator_id: int

    reason: str

    infraction_type: InfractionType

    gravity_id: int
    gravity: GravityLevelSchema

    created_at: datetime

    timeout_end: datetime | None = Field(None)

    is_active: bool

    class Config:
        from_attributes = True


class InfractionsUpdate(BaseModel):
    id: int

    reason: Optional[str]

    infraction_type: Optional[InfractionType]

    gravity_id: Optional[int]
    gravity: Optional[GravityLevelSchema]

    timeout_end: Optional[datetime] = Field(None)

    is_active: Optional[bool]
