"""t_agent 表实体。"""

from dataclasses import dataclass, field

from server.entity.base import BaseEntity


@dataclass
class AgentEntity(BaseEntity):
    name: str = ""
    description: str = ""
    soul_prompt: str = ""
    model_id: int = 0
    tool_names: list[str] = field(default_factory=list)
    skill_ids: list[int] = field(default_factory=list)
    mcp_ids: list[int] = field(default_factory=list)
