from enum import Enum
from datetime import datetime, UTC, date

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    pending_email = "PENDING_EMAIL"
    pending_manual = "PENDING_MANUAL"
    pending_reverification = "PENDING_REVERIFICATION"
    expired = "EXPIRED"
    kicked = "KICKED"
    verified_student = "VERIFIED_STUDENT"
    verified_alumni = "VERIFIED_ALUMNI"
    verified_external = "VERIFIED_EXTERNAL"
    verified_teacher = "VERIFIED_TEACHER"

    @staticmethod
    def from_str(name: str) -> "VerificationStatus":
        for status in VerificationStatus:
            if status.value == name:
                return status
        raise ValueError(f"Unknown VerificationStatus: {name}")


class VerificationsCreate(BaseModel):
    guild_id: int

    joined_at: datetime = Field(datetime.now(UTC))

    user_id: int
    status: VerificationStatus = Field(VerificationStatus.pending_email)

    hashed_code: str | None = Field(None)
    code_expires_at: datetime | None = Field(None)

    user_email: str | None = Field(None)
    verification_expires_at: datetime | None = Field(None)

    grace_period_ends_at: datetime | None = Field(None)

    ticket_id: int | None = Field(None)


class VerificationsSchema(BaseModel):
    id: int
    guild_id: int

    joined_at: datetime

    user_id: int
    status: VerificationStatus

    hashed_code: str | None
    code_expires_at: datetime | None
    last_email_sent_at: datetime | None
    daily_attempts: int
    last_attempt_date: date | None

    user_email: str | None
    verification_expires_at: datetime | None

    grace_period_ends_at: datetime | None
    last_reminder_sent_at: datetime | None

    ticket_id: int | None

    deleted_at: datetime | None

    class Config:
        from_attributes = True


class VerificationsUpdate(BaseModel):
    id: int

    joined_at: datetime | None = Field(None)

    status: VerificationStatus | None = Field(None)

    hashed_code: str | None = Field(None)
    code_expires_at: datetime | None = Field(None)
    last_email_sent_at: datetime | None = Field(None)
    daily_attempts: int | None = Field(None)
    last_attempt_date: date | None = Field(None)

    user_email: str | None = Field(None)
    verification_expires_at: datetime | None = Field(None)

    grace_period_ends_at: datetime | None = Field(None)
    last_reminder_sent_at: datetime | None = Field(None)

    ticket_id: int | None = Field(None)
