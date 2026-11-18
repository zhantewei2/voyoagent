"""技能出入参。"""

from datetime import datetime

from pydantic import BaseModel


class SkillCreate(BaseModel):
    name: str
    description: str = ""
    content: str  # 含 frontmatter 的技能全文


class SkillListItem(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class SkillOut(SkillListItem):
    content: str
