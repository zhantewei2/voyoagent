"""依赖注入：从 app.state 取出全局单例，供 controller 注入。"""

from fastapi import Request

from server.service.agent_db_service import AgentDbService
from server.service.chat_service import ChatService
from server.service.mcp_service import McpService
from server.service.model_service import ModelService
from server.service.skill_service import SkillService


def get_agent_db_service(request: Request) -> AgentDbService:
    return AgentDbService(request.app.state.manager)


def get_chat_service(request: Request) -> ChatService:
    return ChatService(request.app.state.manager)


def get_model_service() -> ModelService:
    return ModelService()


def get_skill_service() -> SkillService:
    return SkillService()


def get_mcp_service() -> McpService:
    return McpService()
