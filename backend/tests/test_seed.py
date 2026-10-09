from sqlalchemy import select
from sqlalchemy.orm import Session

from skill_inventory.models import PublishedSkill, Skill


def test_seed_is_idempotent_and_preserves_edits(client, engine):
    from skill_inventory.seed import seed

    with Session(engine) as session:
        seed(session)
    with Session(engine) as session:
        item = session.scalar(select(Skill).where(Skill.slug == "code-review"))
        item.content = "User edit"
        session.commit()
    with Session(engine) as session:
        seed(session)
    with Session(engine) as session:
        assert len(session.scalars(select(Skill)).all()) == 2
        assert len(session.scalars(select(PublishedSkill)).all()) == 1
        assert (
            session.scalar(select(Skill).where(Skill.slug == "code-review")).content == "User edit"
        )
