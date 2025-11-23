from pydantic import BaseModel, Field
from typing import Optional


class RoleOptionsCreate(BaseModel):
    panel_id: int

    role_id: int

    emoji: str | None = Field(None)
    label: str
    description: str | None = Field(None)


class RoleOptionsSchema(BaseModel):
    id: int

    panel_id: int

    role_id: int

    emoji: str | None
    label: str
    description: str | None

    class Config:
        from_attributes = True


class RoleOptionsUpdate(BaseModel):
    id: int

    role_id: Optional[int] = Field(None)

    emoji: Optional[str] = Field(None)
    label: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
