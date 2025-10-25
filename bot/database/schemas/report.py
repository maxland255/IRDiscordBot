from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class ReportStatus(str, Enum):
    OPEN = "open"
    HANDLED = "handled"
    DISMISSED = "dismissed"


class ReportAction(str, Enum):
    none = "none"
    deleted = "deleted"
    warned = "warned"
    timeout = "timeout"


class ReportCreate(BaseModel):
    guild_id: int

    reporter_id: int
    report_reason: str
    offender_id: int

    reported_channel_id: int
    reported_message_id: int
    log_message_id: int

    status: ReportStatus = Field(ReportStatus.OPEN)


class ReportSchema(BaseModel):
    id: int
    guild_id: int

    reporter_id: int
    report_reason: str
    offender_id: int

    reported_channel_id: int
    reported_message_id: int
    log_message_id: int

    status: ReportStatus

    handler_id: int | None
    handler_action: ReportAction | None
    handled_at: datetime | None

    class Config:
        from_attributes = True


class ReportUpdate(BaseModel):
    id: int

    status: ReportStatus | None = Field(None)

    handler_id: int | None = Field(None)
    handler_action: ReportAction | None = Field(None)
    handled_at: datetime | None = Field(None)
