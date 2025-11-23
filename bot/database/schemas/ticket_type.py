from pydantic import BaseModel, Field
from datetime import datetime


class TicketTypeCreate(BaseModel):
    guild_id: int

    name: str = Field(max_length=16)
    description: str = Field(max_length=4096)

    ticket_channel_category_id: int

    requires_initial_reason: bool = Field(True)

    moderator_role_id: int

    enabled: bool = Field(True)

    is_system: bool = Field(False)


class TicketTypeSchema(BaseModel):
    id: int
    guild_id: int

    name: str = Field(max_length=16)
    description: str = Field(max_length=4096)

    ticket_channel_category_id: int

    requires_initial_reason: bool

    moderator_role_id: int

    enabled: bool

    is_system: bool

    deleted_at: datetime | None

    class Config:
        from_attributes = True


class TicketTypeUpdate(BaseModel):
    id: int

    name: str | None = Field(None, max_length=16)
    description: str | None = Field(None, max_length=4096)

    ticket_channel_category_id: int | None = Field(None)

    requires_initial_reason: bool | None = Field(None)

    moderator_role_id: int | None = Field(None)

    enabled: bool | None = Field(None)
