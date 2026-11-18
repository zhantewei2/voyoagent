"""MCP server 定义出入参。"""

from datetime import datetime

from pydantic import BaseModel, Field


class McpCreate(BaseModel):
    name: str
    description: str = ""
    command: str = ""
    args: list[str] = Field(default_factory=list)
    url: str = ""


class McpOut(McpCreate):
    id: int
    created_at: datetime
    updated_at: datetime
