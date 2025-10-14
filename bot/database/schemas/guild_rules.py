from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class GuildRulesCreate(BaseModel):
    guild_id: int

    title: str = Field(max_length=256)
    rules: str = Field(max_length=1024)


class GuildRulesSchema(BaseModel):
    id: int
    guild_id: int

    title: str = Field(max_length=256)
    rules: str = Field(max_length=1024)

    rules_require_publish: bool

    deleted_at: Optional[datetime] = Field(None)

    class Config:
        from_attributes = True


class GuildRulesUpdate(BaseModel):
    id: int

    title: Optional[str] = Field(None, max_length=256)
    rules: Optional[str] = Field(None, max_length=1024)

    rules_require_publish: Optional[bool] = Field(None)
