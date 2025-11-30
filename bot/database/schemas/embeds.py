from datetime import datetime

from pydantic import BaseModel, Field


class EmbedsCreate(BaseModel):
    guild_id: int

    title: str = Field(max_length=256)
    description: str | None = Field(max_length=4096, default=None)
    url: str | None = Field(default=None)
    timestamp: datetime | None = Field(default=None)
    color: int | None = Field(default=None)

    footer_text: str | None = Field(max_length=2048, default=None)
    footer_icon_url: str | None = Field(default=None)

    image_url: str | None = Field(default=None)

    thumbnail_url: str | None = Field(default=None)

    video_url: str | None = Field(default=None)

    provider_name: str | None = Field(max_length=256, default=None)
    provider_url: str | None = Field(default=None)

    author_name: str | None = Field(max_length=256, default=None)
    author_url: str | None = Field(default=None)
    author_icon_url: str | None = Field(default=None)


class EmbedsSchema(BaseModel):
    id: int
    guild_id: int

    title: str = Field(max_length=256)
    description: str | None = Field(max_length=4096)
    url: str | None
    timestamp: datetime | None
    color: int | None

    footer_text: str | None = Field(max_length=2048)
    footer_icon_url: str | None

    image_url: str | None

    thumbnail_url: str | None

    video_url: str | None

    provider_name: str | None = Field(max_length=256)
    provider_url: str | None

    author_name: str | None = Field(max_length=256)
    author_url: str | None
    author_icon_url: str | None

    deleted_at: datetime | None

    class Config:
        from_attributes = True


class EmbedsUpdate(BaseModel):
    id: int

    title: str | None = Field(max_length=256, default=None)
    description: str | None = Field(max_length=4096, default=None)
    url: str | None = Field(default=None)
    timestamp: datetime | None = Field(default=None)
    color: int | None = Field(default=None)

    footer_text: str | None = Field(max_length=2048, default=None)
    footer_icon_url: str | None = Field(default=None)

    image_url: str | None = Field(default=None)

    thumbnail_url: str | None = Field(default=None)

    video_url: str | None = Field(default=None)

    provider_name: str | None = Field(max_length=256, default=None)
    provider_url: str | None = Field(default=None)

    author_name: str | None = Field(max_length=256, default=None)
    author_url: str | None = Field(default=None)
    author_icon_url: str | None = Field(default=None)


class EmbedFieldsCreate(BaseModel):
    embed_id: int

    name: str = Field(max_length=256)
    value: str = Field(max_length=1024)
    inline: bool = Field(default=False)

    position: int = Field(default=0)


class EmbedFieldsSchema(BaseModel):
    id: int
    embed_id: int
    embed: EmbedsSchema

    name: str = Field(max_length=256)
    value: str = Field(max_length=1024)
    inline: bool

    position: int

    deleted_at: datetime | None

    class Config:
        from_attributes = True


class EmbedFieldsUpdate(BaseModel):
    id: int

    name: str | None = Field(max_length=256, default=None)
    value: str | None = Field(max_length=1024, default=None)
    inline: bool | None = Field(default=None)

    position: int | None = Field(default=None)
