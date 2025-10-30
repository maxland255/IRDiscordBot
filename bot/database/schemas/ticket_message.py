from typing import Any
from datetime import datetime, UTC

from pydantic import BaseModel, Field


class TicketMessageCreate(BaseModel):
    ticket_id: int

    message_id: int
    author_id: int

    content: str | None = Field(None)

    attachments_json: list[dict[Any, Any]] | None = Field(None)
    stickers_json: list[dict[Any, Any]] | None = Field(None)
    poll_json: dict[Any, Any] | None = Field(None)
    reference_json: dict[Any, Any] | None = Field(None)
    embeds_json: list[dict[Any, Any]] | None = Field(None)

    created_at: datetime = Field(datetime.now(UTC))


class TicketMessageSchema(BaseModel):
    id: int
    ticket_id: int

    message_id: int
    author_id: int

    content: str | None

    attachments_json: list[dict[Any, Any]] | None
    stickers_json: list[dict[Any, Any]] | None
    poll_json: dict[Any, Any] | None
    reference_json: dict[Any, Any] | None
    embeds_json: list[dict[Any, Any]] | None

    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None

    class Config:
        from_attributes = True


class TicketMessageUpdate(BaseModel):
    id: int

    content: str | None = Field(None)

    attachments_json: list[dict[Any, Any]] | None = Field(None)
    stickers_json: list[dict[Any, Any]] | None = Field(None)
    poll_json: dict[Any, Any] | None = Field(None)
    reference_json: dict[Any, Any] | None = Field(None)
    embeds_json: list[dict[Any, Any]] | None = Field(None)

    edited_at: datetime | None = Field(datetime.now(UTC))
