"""t_skill 表实体。"""

from dataclasses import dataclass

from server.entity.base import BaseEntity


@dataclass
class SkillEntity(BaseEntity):
    name: str = ""
    description: str = ""
    content: str = ""  # 含 frontmatter 的技能全文
