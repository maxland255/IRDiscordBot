from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

from .role_options import RoleOptionsSchema


class RolePanelCreate(BaseModel):
    guild_id: int

    channel_id: int | None = Field(None)
    message_id: int | None = Field(None)

    multiple_choose: bool = Field(False)

    name: str

    title: str
    description: str | None

    deleted_at: datetime | None = Field(None)


class RolePanelSchema(BaseModel):
    id: int
    guild_id: int

    channel_id: int | None
    message_id: int | None

    multiple_choose: bool

    # An internal name to identify the panel
    name: str

    # A title and description to display above the options
    title: str
    description: str | None

    deleted_at: datetime | None

    options: list[RoleOptionsSchema]

    class Config:
        from_attributes = True


class RolePanelUpdate(BaseModel):
    id: int

    channel_id: Optional[int] = Field(None)
    message_id: Optional[int] = Field(None)

    multiple_choose: Optional[bool] = Field(None)

    name: Optional[str] = Field(None)

    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)

    deleted_at: Optional[datetime] = Field(None)
