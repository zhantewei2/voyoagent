"""t_chat 表实体。"""

from dataclasses import dataclass

from server.entity.base import BaseEntity


@dataclass
class ChatEntity(BaseEntity):
    agent_id: int = 0
    title: str = ""
    history: str = "[]"  # JSON 数组字符串
