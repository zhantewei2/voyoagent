"""t_model 表实体。"""

from dataclasses import dataclass

from server.entity.base import BaseEntity


@dataclass
class ModelEntity(BaseEntity):
    name: str = ""
    model: str = ""
    base_url: str = ""
    api_key: str = ""
    description: str = ""
