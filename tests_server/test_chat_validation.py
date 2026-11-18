#chat 校验路径：chat 不存在 / chat 不属于该 agent / agent 不存在
import asyncio

import pytest
from voyo.utils import YoHttpException

from server.entity.chat_entity import ChatEntity
from server.models.chat_models import ChatRequest
from server.service import chat_service
from server.service.chat_service import ChatService


class StubManager:
    #只提供 prepare 用到的两个入口；instance 可控以模拟 agent 不存在

    def __init__(self, instance):
        self._instance = instance
        self._lock = asyncio.Lock()

    async def ensure_instance(self, agent_id: int):
        return self._instance

    def lock(self, agent_id: int):
        return self._lock


def make_service(monkeypatch, chat: ChatEntity | None, instance=object()) -> ChatService:
    async def fake_select_chat(chat_id, conn=None):
        return chat

    monkeypatch.setattr(chat_service.chat_mapper, "select_chat", fake_select_chat)
    return ChatService(StubManager(instance))


async def test_chat_not_found(monkeypatch):
    service = make_service(monkeypatch, chat=None)
    with pytest.raises(YoHttpException) as e:
        await service.prepare(1, ChatRequest(chat_id=9, content="hi"))
    assert e.value.code == 404


async def test_chat_agent_mismatch(monkeypatch):
    service = make_service(monkeypatch, chat=ChatEntity(id=9, agent_id=2))
    with pytest.raises(YoHttpException) as e:
        await service.prepare(1, ChatRequest(chat_id=9, content="hi"))
    assert e.value.code == 400
    assert "不属于" in e.value.msg


async def test_agent_not_found(monkeypatch):
    service = make_service(monkeypatch, chat=ChatEntity(id=9, agent_id=1), instance=None)
    with pytest.raises(YoHttpException) as e:
        await service.prepare(1, ChatRequest(chat_id=9, content="hi"))
    assert e.value.code == 404
