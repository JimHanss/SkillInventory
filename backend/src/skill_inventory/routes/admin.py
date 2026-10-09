from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from skill_inventory.db import get_session
from skill_inventory.schemas import (
    Page,
    PublishedMetadata,
    SkillCreate,
    SkillDetail,
    SkillSummary,
    SkillUpdate,
)
from skill_inventory.services import skills

router = APIRouter(prefix="/api/admin/skills", tags=["Management"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=Page[SkillSummary])
def list_skills(
    session: SessionDep,
    q: str | None = Query(None, max_length=120),
    status: Literal["draft", "published"] | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return skills.list_skills(session, q, status, limit, offset)


@router.post("", response_model=SkillDetail, status_code=201)
def create_skill(data: SkillCreate, session: SessionDep):
    return skills.create_skill(session, data)


@router.get("/{skill_id}", response_model=SkillDetail)
def get_skill(skill_id: UUID, session: SessionDep):
    return skills.get_skill(session, skill_id)


@router.put("/{skill_id}", response_model=SkillDetail)
def update_skill(skill_id: UUID, data: SkillUpdate, session: SessionDep):
    return skills.update_skill(session, skill_id, data)


@router.delete("/{skill_id}", status_code=204)
def delete_skill(skill_id: UUID, session: SessionDep):
    skills.delete_skill(session, skill_id)
    return Response(status_code=204)


@router.post("/{skill_id}/publish", response_model=PublishedMetadata)
def publish_skill(skill_id: UUID, session: SessionDep, data: SkillUpdate | None = None):
    return skills.publish_skill(session, skill_id, data)
