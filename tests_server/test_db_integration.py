#真实 DB 集成用例：/api/models、/api/agents 快乐路径 + 列表 SQL 往返数；DATABASE_URL 不可用时跳过
import asyncio
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from voyo.db.pg import asyncpg, get_default_pool

from server.config import settings

SCHEMA_SQL = (Path(__file__).resolve().parent.parent / "server" / "sql" / "schema.sql").read_text(encoding="utf-8")


async def _db_available() -> bool:
    if not settings.DATABASE_URL:
        return False
    try:
        conn = await asyncio.wait_for(asyncpg.connect(settings.DATABASE_URL), 15)
        await conn.close()
        return True
    except Exception:
        return False


@pytest.fixture
async def api_client():
    if not await _db_available():
        pytest.skip("DATABASE_URL 不可用，跳过真实 DB 集成用例")
    from server.app import app
    from server.db import close_db, init_db
    from server.service.agent_service import AgentManager

    await init_db()
    pool = get_default_pool()
    conn = await pool.acquire()
    try:
        await conn.execute(SCHEMA_SQL)  # 建表脚本幂等
    finally:
        await pool.release(conn)
    app.state.manager = AgentManager()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await app.state.manager.close_all()
    await close_db()


def _payload(resp) -> dict:
    body = resp.json()
    assert body["status_code"] == resp.status_code
    return body["message"]


def _model_body(suffix: str) -> dict:
    return {"name": f"it-model-{suffix}", "model": "m", "base_url": "http://b",
            "api_key": "sk-12345678", "description": "集成"}


async def test_model_crud_happy_path(api_client):
    suffix = uuid.uuid4().hex[:8]

    created = _payload(await api_client.post("/api/models", json=_model_body(suffix)))
    model_id = created["id"]
    assert created["name"] == f"it-model-{suffix}"
    assert created["api_key"] == "****5678"  # 出参脱敏

    names = [m["name"] for m in _payload(await api_client.get("/api/models"))]
    assert f"it-model-{suffix}" in names

    detail = _payload(await api_client.get(f"/api/models/{model_id}"))
    assert detail["id"] == model_id and detail["model"] == "m"

    body = _model_body(suffix)
    body["description"] = "改过"
    updated = _payload(await api_client.put(f"/api/models/{model_id}", json=body))
    assert updated["description"] == "改过"

    assert _payload(await api_client.delete(f"/api/models/{model_id}")) == "success"
    names = [m["name"] for m in _payload(await api_client.get("/api/models"))]
    assert f"it-model-{suffix}" not in names


async def test_agent_crud_happy_path(api_client):
    suffix = uuid.uuid4().hex[:8]
    model = _payload(await api_client.post("/api/models", json=_model_body(suffix)))
    agent_body = {
        "name": f"it-agent-{suffix}", "description": "集成", "soul_prompt": "测试 soul",
        "model_id": model["id"], "tool_names": ["read_file"], "skill_ids": [], "mcp_ids": [],
    }

    created = _payload(await api_client.post("/api/agents", json=agent_body))
    agent_id = created["id"]
    assert created["model_name"] == f"it-model-{suffix}"
    assert created["tool_names"] == ["read_file"]

    items = _payload(await api_client.get("/api/agents"))
    assert any(a["id"] == agent_id for a in items)

    detail = _payload(await api_client.get(f"/api/agents/{agent_id}"))
    assert detail["soul_prompt"] == "测试 soul"
    assert detail["model"]["name"] == f"it-model-{suffix}"
    assert isinstance(detail["mcp_states"], list)

    agent_body["soul_prompt"] = "改过 soul"
    updated = _payload(await api_client.put(f"/api/agents/{agent_id}", json=agent_body))
    assert updated["id"] == agent_id

    _payload(await api_client.delete(f"/api/agents/{agent_id}"))
    _payload(await api_client.delete(f"/api/models/{model['id']}"))
    items = _payload(await api_client.get("/api/agents"))
    assert all(a["id"] != agent_id for a in items)


async def test_agent_list_db_round_trips(api_client):
    #列表接口读路径合并：一次列表请求的连接批次数（≈事务数）不超过 2
    suffix = uuid.uuid4().hex[:8]
    model = _payload(await api_client.post("/api/models", json=_model_body(suffix)))
    agent_body = {
        "name": f"it-agent-{suffix}", "description": "", "soul_prompt": "",
        "model_id": model["id"], "tool_names": [], "skill_ids": [], "mcp_ids": [],
    }
    created = _payload(await api_client.post("/api/agents", json=agent_body))

    pool = get_default_pool()
    count = {"n": 0}
    orig_acquire = pool.acquire

    async def counting_acquire(*args, **kwargs):
        count["n"] += 1
        return await orig_acquire(*args, **kwargs)

    pool.acquire = counting_acquire
    try:
        resp = await api_client.get("/api/agents")
    finally:
        pool.acquire = orig_acquire

    assert resp.status_code == 200
    assert count["n"] <= 2, f"GET /api/agents 连接批次数过多: {count['n']}"

    _payload(await api_client.delete(f"/api/agents/{created['id']}"))
    _payload(await api_client.delete(f"/api/models/{model['id']}"))
