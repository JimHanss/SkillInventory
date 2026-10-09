from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from skill_inventory.models import PublishedSkill, Skill
from skill_inventory.repositories import skills as repository
from skill_inventory.schemas import (
    Page,
    PublishedMetadata,
    PublishedSnapshot,
    SkillCreate,
    SkillDetail,
    SkillSummary,
    SkillUpdate,
)


class SkillNotFound(Exception):
    pass


class SlugConflict(Exception):
    pass


def require_skill(session: Session, skill_id: UUID, *, lock=False):
    skill = repository.find_skill(session, skill_id, lock=lock)
    if skill is None:
        raise SkillNotFound
    return skill


def metadata(skill, published):
    return PublishedMetadata(
        slug=skill.slug,
        name=published.name,
        description=published.description,
        revision=published.revision,
        published_at=published.published_at,
    )


def summary(skill, published):
    return SkillSummary(
        id=skill.id,
        slug=skill.slug,
        name=skill.name,
        description=skill.description,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        published_revision=published.revision if published else None,
        published_at=published.published_at if published else None,
    )


def detail(session, skill):
    published = session.get(PublishedSkill, skill.id)
    snapshot = (
        PublishedSnapshot(**metadata(skill, published).model_dump(), content=published.content)
        if published
        else None
    )
    return SkillDetail(
        **summary(skill, published).model_dump(), content=skill.content, published=snapshot
    )


def create_skill(session: Session, data: SkillCreate) -> SkillDetail:
    try:
        with session.begin():
            skill = Skill(**data.model_dump())
            session.add(skill)
            session.flush()
            result = detail(session, skill)
        return result
    except IntegrityError as exc:
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise SlugConflict from exc
        raise


def get_skill(session: Session, skill_id: UUID) -> SkillDetail:
    return detail(session, require_skill(session, skill_id))


def list_skills(session, q=None, status=None, limit=20, offset=0) -> Page[SkillSummary]:
    rows, total = repository.list_rows(session, q, status, limit, offset)
    return Page(items=[summary(*row) for row in rows], total=total, limit=limit, offset=offset)


def update_skill(session: Session, skill_id: UUID, data: SkillUpdate) -> SkillDetail:
    with session.begin():
        skill = require_skill(session, skill_id, lock=True)
        for key, value in data.model_dump().items():
            setattr(skill, key, value)
        skill.updated_at = datetime.now(timezone.utc)
        session.flush()
        result = detail(session, skill)
    return result


def delete_skill(session: Session, skill_id: UUID) -> None:
    with session.begin():
        session.delete(require_skill(session, skill_id, lock=True))


def publish_skill(
    session: Session, skill_id: UUID, data: SkillUpdate | None = None
) -> PublishedMetadata:
    with session.begin():
        skill = require_skill(session, skill_id, lock=True)
        if data is not None:
            for key, value in data.model_dump().items():
                setattr(skill, key, value)
            skill.updated_at = datetime.now(timezone.utc)
        published = session.get(PublishedSkill, skill_id)
        if published is None:
            published = PublishedSkill(skill_id=skill_id, revision=0)
            session.add(published)
        published.name = skill.name
        published.description = skill.description
        published.content = skill.content
        published.revision += 1
        published.published_at = datetime.now(timezone.utc)
        session.flush()
        result = metadata(skill, published)
    return result


def list_published(session, q=None, limit=20, offset=0) -> Page[PublishedMetadata]:
    rows, total = repository.list_rows(session, q, None, limit, offset, public=True)
    return Page(items=[metadata(*row) for row in rows], total=total, limit=limit, offset=offset)


def get_published(session: Session, slug: str) -> PublishedMetadata:
    row = repository.find_published(session, slug)
    if row is None:
        raise SkillNotFound
    return metadata(*row)


def get_published_content(session: Session, slug: str) -> str:
    row = repository.find_published(session, slug)
    if row is None:
        raise SkillNotFound
    return row[1].content
