from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from skill_inventory.models import PublishedSkill, Skill


def find_skill(session: Session, skill_id: UUID, *, lock: bool = False) -> Skill | None:
    statement = select(Skill).where(Skill.id == skill_id)
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement)


def list_rows(session: Session, q, status, limit, offset, *, public=False):
    statement = select(Skill, PublishedSkill).outerjoin(
        PublishedSkill, Skill.id == PublishedSkill.skill_id
    )
    if public or status == "published":
        statement = statement.where(PublishedSkill.skill_id.is_not(None))
    elif status == "draft":
        statement = statement.where(PublishedSkill.skill_id.is_(None))
    if q:
        name = PublishedSkill.name if public else Skill.name
        statement = statement.where(
            or_(name.icontains(q, autoescape=True), Skill.slug.icontains(q, autoescape=True))
        )
    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    rows = session.execute(
        statement.order_by(Skill.created_at.desc(), Skill.id).limit(limit).offset(offset)
    ).all()
    return rows, total


def find_published(session: Session, slug: str):
    return session.execute(
        select(Skill, PublishedSkill)
        .join(PublishedSkill, Skill.id == PublishedSkill.skill_id)
        .where(Skill.slug == slug)
    ).first()
