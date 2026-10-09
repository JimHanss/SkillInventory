from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SkillUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    content: str = Field(min_length=1)

    @field_validator("name", "content")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Must not be blank")
        return value

    @field_validator("content")
    @classmethod
    def content_size(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("NUL characters are not supported")
        if len(value.encode("utf-8")) > 262144:
            raise ValueError("Content exceeds 256 KiB")
        return value

    @field_validator("name", "description")
    @classmethod
    def no_nul(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("NUL characters are not supported")
        return value


class SkillCreate(SkillUpdate):
    slug: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class PublishedMetadata(BaseModel):
    slug: str
    name: str
    description: str
    revision: int
    published_at: datetime


class PublishedSnapshot(PublishedMetadata):
    content: str


class SkillSummary(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    published_revision: int | None
    published_at: datetime | None


class SkillDetail(SkillSummary):
    content: str
    published: PublishedSnapshot | None


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
