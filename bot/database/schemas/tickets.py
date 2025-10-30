from enum import Enum

from pydantic import BaseModel, Field
from datetime import datetime, UTC

from .ticket_type import TicketTypeSchema


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class TicketsCreate(BaseModel):
    ticket_type_id: int

    member_id: int
    channel_id: int | None = Field(None)

    panel_message_id: int | None = Field(None)

    created_at: datetime = datetime.now(UTC)


class TicketsSchema(BaseModel):
    id: int

    ticket_type_id: int
    ticket_type: TicketTypeSchema

    status: TicketStatus

    member_id: int
    channel_id: int | None

    panel_message_id: int | None

    handler_id: int | None
    is_locked: bool

    created_at: datetime
    deleted_at: datetime | None

    class Config:
        from_attributes = True


class TicketsUpdate(BaseModel):
    id: int

    ticket_type_id: int | None = Field(None)

    status: TicketStatus | None = Field(None)

    channel_id: int | None = Field(None)

    panel_message_id: int | None = Field(None)

    handler_id: int | None = Field(None)
    is_locked: bool | None = Field(None)
