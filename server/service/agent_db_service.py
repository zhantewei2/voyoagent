"""agent 配置 CRUD（PG 持久化）+ 装配字段校验 + 运行时实例联动。"""

import logging

from asyncpg import UniqueViolationError
from voyo.utils import YoHttpException
from voyo.utils.exception import ExceptionType

from server.entity.agent_entity import AgentEntity
from server.mapper import agent_mapper
from server.models.agent_models import AgentCreate, AgentDetail, AgentListItem
from server.service import mcp_service, model_service, skill_service
from server.service.agent_service import AgentManager
from server.service.tool_service import known_tool_names

logger = logging.getLogger(__name__)


class AgentDbService:
    #agent 配置的持久化与校验；实例构建/关闭交给 AgentManager

    def __init__(self, manager: AgentManager):
        self.manager = manager

    async def list(self) -> list[AgentListItem]:
        agents, models, skills, mcps = await agent_mapper.select_agents_overview()
        items = []
        for agent in agents:
            model = models.get(agent.model_id)
            items.append(self._list_item(
                agent, model,
                [skills[i] for i in agent.skill_ids if i in skills],
                [mcps[i] for i in agent.mcp_ids if i in mcps]))
        return items

    async def get(self, agent_id: int) -> AgentDetail:
        agent, model, skills, mcps = await agent_mapper.select_agent_detail(agent_id)
        if agent is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"agent 不存在: {agent_id}")
        #详情只读配置：运行时状态仅当实例已存在时附带，不做冷构建
        instance = self.manager.instance(agent_id)
        return AgentDetail(
            id=agent.id, name=agent.name, description=agent.description,
            soul_prompt=agent.soul_prompt, model_id=agent.model_id,
            model=model_service.to_out(model) if model else None,
            tool_names=agent.tool_names,
            skills=[skill_service.to_item(s) for s in skills],
            mcps=[mcp_service.to_out(m) for m in mcps],
            mcp_states=instance.list_mcp() if instance else [],
            created_at=agent.created_at, updated_at=agent.updated_at,
        )

    async def create(self, body: AgentCreate) -> AgentListItem:
        name = self._check_name(body.name)
        model, skills, mcps = await self._check_refs(body)
        try:
            agent = await agent_mapper.insert_agent(
                name, body.description, body.soul_prompt, body.model_id,
                body.tool_names, body.skill_ids, body.mcp_ids)
        except UniqueViolationError:
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"agent 名称已存在: {name}")
        await self._rebuild(agent.id)
        logger.info("创建 agent: %s", agent.id)
        return self._list_item(agent, model, skills, mcps)

    async def update(self, agent_id: int, body: AgentCreate) -> AgentListItem:
        await self._get(agent_id)
        name = self._check_name(body.name)
        model, skills, mcps = await self._check_refs(body)
        try:
            agent = await agent_mapper.update_agent(
                agent_id, name, body.description, body.soul_prompt, body.model_id,
                body.tool_names, body.skill_ids, body.mcp_ids)
        except UniqueViolationError:
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"agent 名称已存在: {name}")
        if agent is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"agent 不存在: {agent_id}")
        await self._rebuild(agent_id)
        return self._list_item(agent, model, skills, mcps)

    async def delete(self, agent_id: int) -> None:
        await self._get(agent_id)
        await self.manager.close_instance(agent_id)
        await agent_mapper.delete_agent(agent_id)
        logger.info("删除 agent: %s", agent_id)

    # ---- 内部 ----

    async def _get(self, agent_id: int) -> AgentEntity:
        entity = await agent_mapper.select_agent(agent_id)
        if entity is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"agent 不存在: {agent_id}")
        return entity

    def _check_name(self, name: str) -> str:
        name = (name or "").strip()
        if not name:
            raise YoHttpException(ExceptionType.PARAM_ERROR, "agent 名称不能为空")
        return name

    async def _check_refs(self, body: AgentCreate):
        #装配字段校验：模型/技能/MCP 必须存在，工具必须是内置工具；返回引用明细供响应复用
        model, skills, mcps = await agent_mapper.select_assembly_refs(
            body.model_id, body.skill_ids, body.mcp_ids)
        if model is None:
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"模型不存在: {body.model_id}")
        unknown = [n for n in body.tool_names if n not in known_tool_names()]
        if unknown:
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"未知工具: {', '.join(unknown)}")
        missing = set(body.skill_ids) - {s.id for s in skills}
        if missing:
            raise YoHttpException(ExceptionType.PARAM_ERROR,
                                  f"技能不存在: {', '.join(str(i) for i in sorted(missing))}")
        missing = set(body.mcp_ids) - {m.id for m in mcps}
        if missing:
            raise YoHttpException(ExceptionType.PARAM_ERROR,
                                  f"MCP server 不存在: {', '.join(str(i) for i in sorted(missing))}")
        return model, skills, mcps

    async def _rebuild(self, agent_id: int) -> None:
        #装配失败不阻塞配置保存，聊天时会懒重建
        try:
            await self.manager.rebuild_instance(agent_id)
        except Exception:
            logger.exception("agent 实例构建失败: %s", agent_id)

    def _list_item(self, agent: AgentEntity, model, skills: list, mcps: list) -> AgentListItem:
        return AgentListItem(
            id=agent.id, name=agent.name, description=agent.description,
            model_id=agent.model_id, model_name=model.name if model else "",
            tool_names=agent.tool_names,
            skill_names=[s.name for s in skills],
            mcp_names=[m.name for m in mcps],
            created_at=agent.created_at, updated_at=agent.updated_at,
        )
