"""MCP server 定义 CRUD。"""

import logging

from asyncpg import UniqueViolationError
from voyo.utils import YoHttpException
from voyo.utils.exception import ExceptionType

from server.mapper import agent_mapper, mcp_mapper
from server.models.mcp_models import McpCreate, McpOut

logger = logging.getLogger(__name__)


class McpService:

    async def list(self) -> list[McpOut]:
        return [to_out(e) for e in await mcp_mapper.select_mcps()]

    async def get(self, mcp_id: int) -> McpOut:
        return to_out(await self._get(mcp_id))

    async def create(self, body: McpCreate) -> McpOut:
        name = _check(body.name, body.command, body.url)
        try:
            entity = await mcp_mapper.insert_mcp(
                name, body.description, body.command, body.args, body.url)
        except UniqueViolationError:
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"MCP server 名称已存在: {name}")
        logger.info("创建 MCP server: %s", entity.id)
        return to_out(entity)

    async def update(self, mcp_id: int, body: McpCreate) -> McpOut:
        await self._get(mcp_id)
        name = _check(body.name, body.command, body.url)
        try:
            entity = await mcp_mapper.update_mcp(
                mcp_id, name, body.description, body.command, body.args, body.url)
        except UniqueViolationError:
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"MCP server 名称已存在: {name}")
        if entity is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"MCP server 不存在: {mcp_id}")
        return to_out(entity)

    async def delete(self, mcp_id: int) -> None:
        await self._get(mcp_id)
        refs = await agent_mapper.select_agents_by_mcp(mcp_id)
        if refs:
            names = ", ".join(a.name for a in refs)
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"MCP server 已被 agent 引用: {names}")
        await mcp_mapper.delete_mcp(mcp_id)
        logger.info("删除 MCP server: %s", mcp_id)

    async def _get(self, mcp_id: int):
        entity = await mcp_mapper.select_mcp(mcp_id)
        if entity is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"MCP server 不存在: {mcp_id}")
        return entity


def _check(name: str, command: str, url: str) -> str:
    name = (name or "").strip()
    if not name:
        raise YoHttpException(ExceptionType.PARAM_ERROR, "MCP server 名称不能为空")
    if not (command or "").strip() and not (url or "").strip():
        raise YoHttpException(ExceptionType.PARAM_ERROR, "MCP server 需要 command(stdio) 或 url(http) 之一")
    return name


def to_out(entity) -> McpOut:
    return McpOut(
        id=entity.id, name=entity.name, description=entity.description,
        command=entity.command, args=entity.args, url=entity.url,
        created_at=entity.created_at, updated_at=entity.updated_at,
    )
