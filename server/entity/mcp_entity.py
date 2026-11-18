"""t_mcp 表实体。"""

from dataclasses import dataclass, field

from server.entity.base import BaseEntity


@dataclass
class McpEntity(BaseEntity):
    name: str = ""
    description: str = ""
    command: str = ""
    args: list[str] = field(default_factory=list)
    url: str = ""
