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

    # Rules
    rules_channel_id: int | None
    rules_message_id: list[int] | None = Field(None)

    # Moderation
    report_channel_id: int | None = Field(None)

    # Verification system
    verification_ticket_type_id: int | None = Field(None)
    verified_role_id: int | None = Field(None)
    student_role_id: int | None = Field(None)
    alumni_role_id: int | None = Field(None)
    external_role_id: int | None = Field(None)
    teacher_role_id: int | None = Field(None)
    grace_period_days: int = Field(30)
    new_member_verification_time_limit: int = Field(24)
    allowed_email_domains: list[str] = Field(default_factory=list)

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

    # Rules
    rules_channel_id: Optional[int] = Field(None)
    rules_message_id: Optional[list[int]] = Field(None)

    # Moderation
    report_channel_id: Optional[int] = Field(None)

    deleted_at: Optional[datetime] = Field(None)

    # Verification system
    verification_ticket_type_id: int | None = Field(None)
    verified_role_id: int | None = Field(None)
    student_role_id: int | None = Field(None)
    alumni_role_id: int | None = Field(None)
    external_role_id: int | None = Field(None)
    teacher_role_id: int | None = Field(None)
    grace_period_days: int | None = Field(None)
    new_member_verification_time_limit: int | None = Field(None)
    allowed_email_domains: list[str] | None = Field(None)
