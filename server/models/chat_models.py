"""会话与对外 chat 出入参。"""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatCreate(BaseModel):
    agent_id: int
    title: str = ""


class ChatOut(BaseModel):
    chat_id: int
    agent_id: int
    title: str
    history: list = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ChatRequest(BaseModel):
    chat_id: int
    content: str
    thinking: bool = False  # True 打开思考流（effort=low），默认关闭（effort=none）
