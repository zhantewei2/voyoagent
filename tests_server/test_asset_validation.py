#资产校验代表用例：重复名、被引用拒绝删除（mock mapper，不连真库）
import pytest
from asyncpg import UniqueViolationError
from voyo.utils import YoHttpException

from server.entity.agent_entity import AgentEntity
from server.models.model_models import ModelCreate
from server.service import model_service
from server.service.model_service import ModelService


async def test_model_duplicate_name(monkeypatch):
    async def fake_insert(*args, **kwargs):
        raise UniqueViolationError("duplicate")

    monkeypatch.setattr(model_service.model_mapper, "insert_model", fake_insert)
    service = ModelService()
    with pytest.raises(YoHttpException) as e:
        await service.create(ModelCreate(name="m1", model="x", base_url="b", api_key="k"))
    assert e.value.code == 400
    assert "已存在" in e.value.msg


async def test_model_delete_rejected_when_referenced(monkeypatch):
    from server.entity.model_entity import ModelEntity

    async def fake_select(model_id, conn=None):
        return ModelEntity(id=model_id, name="m1", model="x", base_url="b", api_key="k")

    async def fake_refs(model_id, conn=None):
        return [AgentEntity(id=1, name="agent-a")]

    async def fake_delete(model_id, conn=None):
        raise AssertionError("被引用时不应执行删除")

    monkeypatch.setattr(model_service.model_mapper, "select_model", fake_select)
    monkeypatch.setattr(model_service.agent_mapper, "select_agents_by_model", fake_refs)
    monkeypatch.setattr(model_service.model_mapper, "delete_model", fake_delete)

    service = ModelService()
    with pytest.raises(YoHttpException) as e:
        await service.delete(1)
    assert e.value.code == 400
    assert "agent-a" in e.value.msg
