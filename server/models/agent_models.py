"""agent 配置出入参。"""

from datetime import datetime

from pydantic import BaseModel, Field

from server.models.mcp_models import McpOut
from server.models.model_models import ModelOut
from server.models.skill_models import SkillListItem


class AgentCreate(BaseModel):
    name: str
    description: str = ""
    soul_prompt: str = ""
    model_id: int
    tool_names: list[str] = Field(default_factory=list)
    skill_ids: list[int] = Field(default_factory=list)
    mcp_ids: list[int] = Field(default_factory=list)


class AgentListItem(BaseModel):
    id: int
    name: str
    description: str
    model_id: int
    model_name: str
    tool_names: list[str]
    skill_names: list[str]
    mcp_names: list[str]
    created_at: datetime
    updated_at: datetime


class AgentDetail(BaseModel):
    id: int
    name: str
    description: str
    soul_prompt: str
    model_id: int
    model: ModelOut | None = None
    tool_names: list[str]
    skills: list[SkillListItem]
    mcps: list[McpOut]
    mcp_states: list[dict]  # 运行时 MCP 连接状态，未构建实例时为空
    created_at: datetime
    updated_at: datetime
