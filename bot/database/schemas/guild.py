from pydantic import BaseModel, Field
from datetime import datetime

from typing import Optional


class GuildSchema(BaseModel):
    id: int
    name: str

    # Height for all warnings
    warn_height: float

    # Default timeout in seconds
    default_timeout: int

    # salon de logs
    logs_moderation: int | None
    logs_server: int | None

    rules_message_id: int | None

    # tickets system
    # pass

    deleted_at: datetime | None = Field(None)

    class Config:
        from_attributes = True


class GuildUpdate(BaseModel):
    id: int
    name: str

    # Height for all warnings
    warn_height: Optional[float] = Field(None)

    # Default timeout in seconds
    default_timeout: Optional[int] = Field(None)

    # salon de logs
    logs_moderation: Optional[int] = Field(None)
    logs_server: Optional[int] = Field(None)

    rules_message_id: int | None = Field(None)

    deleted_at: datetime | None = Field(None)
