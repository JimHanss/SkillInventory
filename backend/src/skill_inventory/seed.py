from sqlalchemy import select
from sqlalchemy.orm import Session

from skill_inventory.models import Skill
from skill_inventory.schemas import SkillCreate
from skill_inventory.services.skills import create_skill, publish_skill


def seed(session: Session) -> None:
    examples = [
        (
            "code-review",
            "代码审查",
            "统一团队代码审查步骤",
            "# 代码审查\n\n1. 阅读变更背景。\n"
            "2. 检查正确性、边界条件与安全性。\n3. 给出可操作的建议。\n",
            True,
        ),
        (
            "meeting-notes",
            "会议纪要",
            "将会议记录整理为行动项",
            "# 会议纪要\n\n提取结论、负责人和截止时间；不确定的信息标记为待确认。\n",
            False,
        ),
    ]
    for slug, name, description, content, publish in examples:
        with session.begin():
            exists = session.scalar(select(Skill.id).where(Skill.slug == slug))
        if exists is not None:
            continue
        item = create_skill(
            session, SkillCreate(slug=slug, name=name, description=description, content=content)
        )
        if publish:
            publish_skill(session, item.id)
