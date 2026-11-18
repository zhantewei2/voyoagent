"""模型接入配置出入参。"""

from datetime import datetime

from pydantic import BaseModel


def mask_api_key(api_key: str) -> str:
    #出参脱敏：只保留后 4 位
    if not api_key:
        return ""
    return "****" + api_key[-4:] if len(api_key) >= 4 else "****"


class ModelCreate(BaseModel):
    name: str
    model: str
    base_url: str
    api_key: str
    description: str = ""


class ModelOut(BaseModel):
    id: int
    name: str
    model: str
    base_url: str
    api_key: str  # 脱敏值，见 mask_api_key
    description: str
    created_at: datetime
    updated_at: datetime
