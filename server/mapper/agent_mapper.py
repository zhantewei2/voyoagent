"""t_agent 表 SQL + agent 装配聚合读。读走免事务单条 SQL，写保持 @transaction。"""

import json
from datetime import datetime

from voyo.db.pg import transaction

from server.db import fetch_all, fetch_one, retry_once
from server.entity.agent_entity import AgentEntity
from server.entity.base import new_id
from server.mapper import mcp_mapper, model_mapper, skill_mapper

_COLUMNS = "id, name, description, soul_prompt, model_id, tool_names, skill_ids, mcp_ids, created_at, updated_at"


@retry_once
@transaction()
async def insert_agent(name: str, description: str, soul_prompt: str, model_id: int,
                       tool_names: list[str], skill_ids: list[int], mcp_ids: list[int],
                       conn=None) -> AgentEntity:
    entity = AgentEntity(id=new_id(), name=name, description=description, soul_prompt=soul_prompt,
                         model_id=model_id, tool_names=tool_names, skill_ids=skill_ids, mcp_ids=mcp_ids)
    await conn.execute(
        f"INSERT INTO t_agent ({_COLUMNS}) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$9)",
        entity.id, entity.name, entity.description, entity.soul_prompt, entity.model_id,
        entity.tool_names, entity.skill_ids, entity.mcp_ids, entity.created_at,
    )
    return entity


@retry_once
@transaction()
async def update_agent(agent_id: int, name: str, description: str, soul_prompt: str, model_id: int,
                       tool_names: list[str], skill_ids: list[int], mcp_ids: list[int],
                       conn=None) -> AgentEntity | None:
    row = await conn.fetchrow(
        f"""UPDATE t_agent SET name=$2, description=$3, soul_prompt=$4, model_id=$5,
                tool_names=$6, skill_ids=$7, mcp_ids=$8, updated_at=now()
            WHERE id=$1 RETURNING {_COLUMNS}""",
        agent_id, name, description, soul_prompt, model_id, tool_names, skill_ids, mcp_ids,
    )
    return to_entity(row)


@retry_once
@transaction()
async def delete_agent(agent_id: int, conn=None) -> bool:
    status = await conn.execute("DELETE FROM t_agent WHERE id = $1", agent_id)
    return status.endswith("1")


async def select_agent(agent_id: int) -> AgentEntity | None:
    row = await fetch_one(f"SELECT {_COLUMNS} FROM t_agent WHERE id = $1", agent_id)
    return to_entity(row)


async def select_agents() -> list[AgentEntity]:
    rows = await fetch_all(f"SELECT {_COLUMNS} FROM t_agent ORDER BY id")
    return [to_entity(row) for row in rows]


async def select_agents_by_model(model_id: int) -> list[AgentEntity]:
    rows = await fetch_all(f"SELECT {_COLUMNS} FROM t_agent WHERE model_id = $1", model_id)
    return [to_entity(row) for row in rows]


async def select_agents_by_skill(skill_id: int) -> list[AgentEntity]:
    rows = await fetch_all(f"SELECT {_COLUMNS} FROM t_agent WHERE $1 = ANY(skill_ids)", skill_id)
    return [to_entity(row) for row in rows]


async def select_agents_by_mcp(mcp_id: int) -> list[AgentEntity]:
    rows = await fetch_all(f"SELECT {_COLUMNS} FROM t_agent WHERE $1 = ANY(mcp_ids)", mcp_id)
    return [to_entity(row) for row in rows]


# ---- 装配聚合读：单条 SQL（标量子查询 + json_agg）一次取回全部集合 ----

async def select_agents_overview():
    #列表页：agent 全量 + 三张引用表全量，一条查询免事务取回
    row = await fetch_one(
        """
        SELECT
            (SELECT json_agg(to_jsonb(a) ORDER BY a.id) FROM t_agent a) AS agents,
            (SELECT json_agg(to_jsonb(m) ORDER BY m.id) FROM t_model m) AS models,
            (SELECT json_agg(to_jsonb(s) ORDER BY s.id) FROM t_skill s) AS skills,
            (SELECT json_agg(to_jsonb(c) ORDER BY c.id) FROM t_mcp c) AS mcps
        """
    )
    agents = [to_entity(_decode(item)) for item in _json_list(row["agents"])]
    models = {m.id: m for m in [model_mapper.to_entity(_decode(i)) for i in _json_list(row["models"])]}
    skills = {s.id: s for s in [skill_mapper.to_entity(_decode(i)) for i in _json_list(row["skills"])]}
    mcps = {m.id: m for m in [mcp_mapper.to_entity(_decode(i)) for i in _json_list(row["mcps"])]}
    return agents, models, skills, mcps


async def select_agent_detail(agent_id: int):
    #详情/装配构建：agent + 模型 + 技能 + MCP 一条查询取回
    row = await fetch_one(
        """
        WITH a AS (SELECT * FROM t_agent WHERE id = $1)
        SELECT
            (SELECT to_jsonb(x) FROM a x) AS agent,
            (SELECT to_jsonb(m) FROM t_model m, a WHERE m.id = a.model_id) AS model,
            (SELECT json_agg(to_jsonb(s)) FROM t_skill s, a WHERE s.id = ANY(a.skill_ids)) AS skills,
            (SELECT json_agg(to_jsonb(c)) FROM t_mcp c, a WHERE c.id = ANY(a.mcp_ids)) AS mcps
        """,
        agent_id,
    )
    agent_data = _json_obj(row["agent"])
    if agent_data is None:
        return None, None, [], []
    model_data = _json_obj(row["model"])
    model = model_mapper.to_entity(_decode(model_data)) if model_data else None
    skills = [skill_mapper.to_entity(_decode(i)) for i in _json_list(row["skills"])]
    mcps = [mcp_mapper.to_entity(_decode(i)) for i in _json_list(row["mcps"])]
    return to_entity(_decode(agent_data)), model, skills, mcps


@retry_once
@transaction()
async def select_assembly_refs(model_id: int, skill_ids: list[int], mcp_ids: list[int], conn=None):
    #装配字段校验所需的三张资产一次事务读完
    model = model_mapper.to_entity(
        await conn.fetchrow("SELECT * FROM t_model WHERE id = $1", model_id))
    skills = [skill_mapper.to_entity(r) for r in
              await conn.fetch("SELECT * FROM t_skill WHERE id = ANY($1)", skill_ids)]
    mcps = [mcp_mapper.to_entity(r) for r in
            await conn.fetch("SELECT * FROM t_mcp WHERE id = ANY($1)", mcp_ids)]
    return model, skills, mcps


def to_entity(row) -> AgentEntity | None:
    if row is None:
        return None
    return AgentEntity(
        id=row["id"], name=row["name"], description=row["description"], soul_prompt=row["soul_prompt"],
        model_id=row["model_id"], tool_names=list(row["tool_names"] or []),
        skill_ids=[int(i) for i in row["skill_ids"] or []], mcp_ids=[int(i) for i in row["mcp_ids"] or []],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


def _json_list(value) -> list[dict]:
    #json_agg 结果：asyncpg 默认给字符串，兼容已解析的列表
    if value is None:
        return []
    return json.loads(value) if isinstance(value, str) else list(value)


def _json_obj(value) -> dict | None:
    if value is None:
        return None
    return json.loads(value) if isinstance(value, str) else dict(value)


def _decode(data: dict) -> dict:
    #json 行里时间戳是 ISO 字符串，转回 datetime 保持与直读实体一致
    out = dict(data)
    for key in ("created_at", "updated_at"):
        value = out.get(key)
        if isinstance(value, str):
            out[key] = datetime.fromisoformat(value)
    return out
