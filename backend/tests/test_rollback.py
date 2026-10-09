import pytest
from sqlalchemy.orm import Session

from skill_inventory.models import PublishedSkill
from skill_inventory.services import skills


def test_failed_save_and_publish_rolls_back_draft_and_snapshot(client, draft, monkeypatch):
    skill_id = client.post("/api/admin/skills", json=draft).json()["id"]
    client.post(f"/api/admin/skills/{skill_id}/publish")
    original_metadata = skills.metadata

    def fail_after_flush(skill, published):
        raise RuntimeError("injected save and publish failure")

    monkeypatch.setattr(skills, "metadata", fail_after_flush)
    with pytest.raises(RuntimeError, match="injected save and publish failure"):
        client.post(
            f"/api/admin/skills/{skill_id}/publish",
            json={"name": "Changed", "description": "Changed", "content": "# Changed"},
        )
    monkeypatch.setattr(skills, "metadata", original_metadata)
    detail = client.get(f"/api/admin/skills/{skill_id}").json()
    assert detail["name"] == draft["name"]
    assert detail["description"] == draft["description"]
    assert detail["content"] == draft["content"]
    assert detail["published"]["content"] == draft["content"]
    assert detail["published"]["revision"] == 1


def test_failed_publish_rolls_back_snapshot(client, draft, engine, monkeypatch):
    skill_id = client.post("/api/admin/skills", json=draft).json()["id"]
    original_metadata = skills.metadata

    def fail_after_flush(skill, published):
        raise RuntimeError("injected failure after database flush")

    monkeypatch.setattr(skills, "metadata", fail_after_flush)
    from uuid import UUID

    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="injected failure"):
            skills.publish_skill(session, UUID(skill_id))
    with Session(engine) as session:
        assert session.get(PublishedSkill, UUID(skill_id)) is None
    monkeypatch.setattr(skills, "metadata", original_metadata)
    assert client.post(f"/api/admin/skills/{skill_id}/publish").json()["revision"] == 1
