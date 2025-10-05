from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class GravityLevelCreate(BaseModel):
    guild_id: int
    name: str
    description: str
    weight: float
    deleted_at: Optional[datetime] = Field(None)


class GravityLevelSchema(BaseModel):
    id: int
    guild_id: int
    name: str
    description: str
    weight: float
    deleted_at: Optional[datetime] = Field(None)

    class Config:
        from_attributes = True


class GravityLevelUpdate(BaseModel):
    id: int
    name: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    weight: Optional[float] = Field(None)
    deleted_at: Optional[datetime] = Field(None)
