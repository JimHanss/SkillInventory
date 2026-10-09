from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from skill_inventory.db import get_session
from skill_inventory.schemas import Page, PublishedMetadata
from skill_inventory.services import skills

router = APIRouter(prefix="/api/v1/skills", tags=["Client"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=Page[PublishedMetadata])
def list_published(
    session: SessionDep,
    q: str | None = Query(None, max_length=120),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return skills.list_published(session, q, limit, offset)


@router.get("/{slug}", response_model=PublishedMetadata)
def get_published(slug: str, session: SessionDep):
    return skills.get_published(session, slug)


@router.get("/{slug}/content", response_class=PlainTextResponse)
def get_content(slug: str, session: SessionDep):
    return PlainTextResponse(skills.get_published_content(session, slug))
