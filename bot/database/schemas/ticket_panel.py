from pydantic import BaseModel, Field

from .ticket_type import TicketTypeSchema


class TicketPanelCreate(BaseModel):
    ticket_type_id: int

    channel_id: int
    message_id: int


class TicketPanelSchema(BaseModel):
    id: int

    ticket_type_id: int
    ticket_type: TicketTypeSchema

    channel_id: int
    message_id: int

    class Config:
        from_attributes = True


class TicketPanelUpdate(BaseModel):
    id: int

    ticket_type_id: int | None = Field(None)

    channel_id: int | None = Field(None)
    message_id: int | None = Field(None)
