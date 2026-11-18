"""agent 运行时实例管理：instances/locks 登记，配置一律从 PG 读取后装配。"""

import asyncio
import logging
from pathlib import Path

import aiofiles

from server.config import settings
from server.entity.agent_entity import AgentEntity
from server.mapper import agent_mapper
from server.service.tool_service import tool_entry
from voyoagent.yo_agent import Yo_Agent

logger = logging.getLogger(__name__)


class AgentManager:
    #运行时实例登记中心；配置读 PG，create/update 重建实例，delete 关闭实例

    def __init__(self):
        self.instances: dict[int, Yo_Agent] = {}
        self.locks: dict[int, asyncio.Lock] = {}

    def instance(self, agent_id: int) -> Yo_Agent | None:
        return self.instances.get(agent_id)

    def lock(self, agent_id: int) -> asyncio.Lock:
        lock = self.locks.get(agent_id)
        if lock is None:
            lock = self.locks[agent_id] = asyncio.Lock()
        return lock

    async def ensure_instance(self, agent_id: int) -> Yo_Agent | None:
        #实例缺失时按 PG 配置构建；agent 不存在返回 None
        instance = self.instances.get(agent_id)
        if instance is not None:
            return instance
        return await self._build(agent_id)

    async def rebuild_instance(self, agent_id: int) -> Yo_Agent | None:
        await self.close_instance(agent_id)
        return await self.ensure_instance(agent_id)

    async def close_instance(self, agent_id: int) -> None:
        instance = self.instances.pop(agent_id, None)
        if instance is not None:
            await instance.close()

    async def close_all(self) -> None:
        for agent_id in list(self.instances):
            await self.close_instance(agent_id)

    # ---- 内部：按 PG 配置装配实例 ----

    async def _build(self, agent_id: int) -> Yo_Agent | None:
        #一次事务读齐 agent 与模型/技能/MCP 配置
        agent, model, skills, mcps = await agent_mapper.select_agent_detail(agent_id)
        if agent is None:
            return None
        if model is None:
            logger.warning("agent %s 引用的模型不存在: %s", agent_id, agent.model_id)
            return None

        skill_dirs = [await self._materialize_skill(s) for s in skills]
        instance = await self._build_instance(agent, model, skill_dirs, mcps)
        self.instances[agent_id] = instance
        return instance

    async def _build_instance(self, agent: AgentEntity, model, skill_dirs: list[str], mcps) -> Yo_Agent:
        instance = Yo_Agent(
            model=model.model, base_url=model.base_url, api_key=model.api_key,
            effort="none", auto_registry_tool=False,
        )
        for name in agent.tool_names:
            entry = tool_entry(name)
            if entry is not None:
                instance.registry_tool(entry)
            else:
                logger.warning("agent %s 引用未知工具: %s", agent.id, name)
        if agent.soul_prompt:
            #只覆盖 soul；system.md 固定用内置，不许应用端修改
            instance.agent_prompt.soul_prompt = agent.soul_prompt
        if skill_dirs:
            await instance.registry_skill(skill_dirs)
        for mcp in mcps:
            try:
                await instance.registry_mcp(mcp.name, command=mcp.command,
                                             args=list(mcp.args), url=mcp.url)
            except ValueError:
                logger.warning("MCP server 注册冲突: %s", mcp.name)
        await instance.init()
        return instance

    async def _materialize_skill(self, skill) -> str:
        #技能正文原样落成 skill.md，交给框架按目录登记
        dir_path = Path(settings.SKILL_WORK_DIR) / str(skill.id)
        await aiofiles.os.makedirs(dir_path, exist_ok=True)
        async with aiofiles.open(dir_path / "skill.md", "w", encoding="utf-8") as f:
            await f.write(skill.content)
        return str(dir_path)
