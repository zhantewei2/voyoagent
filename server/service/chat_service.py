"""会话服务：chat_id 会话管理 + SSE 流式桥接与 history 持久化。"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator

from voyo.utils import YoHttpException
from voyo.utils.exception import ExceptionType
from voyo.utils.json import JSON
from voyoagent.agent_base import ErrorEvent

from server.mapper import agent_mapper, chat_mapper
from server.models.chat_models import ChatCreate, ChatOut, ChatRequest
from server.service.agent_service import AgentManager

logger = logging.getLogger(__name__)

#后台 run 任务强引用，防止任务被垃圾回收
_RUN_TASKS: set[asyncio.Task] = set()


@dataclass
class ChatRun:
    #一次 chat 的运行上下文：prepare 校验产出，stream 持锁后才写 instance
    instance: Any
    chat_id: int
    content: str
    thinking: bool
    lock: asyncio.Lock


def to_sse(event: Any) -> str:
    #事件转 SSE 帧：data: <json> + 空行，字段含 type，与 voyoagent 事件一一对应
    return f"data: {JSON.json(vars(event))}\n\n"


class ChatService:

    def __init__(self, manager: AgentManager):
        self.manager = manager

    async def create_chat(self, body: ChatCreate) -> ChatOut:
        if await agent_mapper.select_agent(body.agent_id) is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"agent 不存在: {body.agent_id}")
        entity = await chat_mapper.insert_chat(body.agent_id, body.title)
        return _to_out(entity)

    async def get_chat(self, chat_id: int) -> ChatOut:
        return _to_out(await self._get(chat_id))

    async def prepare(self, agent_id: int, body: ChatRequest) -> ChatRun:
        #只做校验、读会话与忙预检：不加锁、不改 instance，运行态由 stream 持锁后建立
        chat = await self._get(body.chat_id)
        if chat.agent_id != agent_id:
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"chat 不属于该 agent: {body.chat_id}")
        instance = await self.manager.ensure_instance(agent_id)
        if instance is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"agent 不存在: {agent_id}")
        lock = self.manager.lock(agent_id)
        if lock.locked():
            raise YoHttpException(409, "agent busy")
        return ChatRun(instance=instance, chat_id=chat.id, content=body.content,
                       thinking=body.thinking, lock=lock)

    async def stream(self, run: ChatRun) -> AsyncIterator[str]:
        #生成器真正启动才拿锁（未启动不占锁）；拿到锁后建会话态，收尾取消 run、写回 history 再放锁
        await run.lock.acquire()
        task: asyncio.Task | None = None
        unsubscribe = None
        loaded = False
        try:
            #持锁后重读会话：上一轮写回在放锁前完成，这里读到的必是最新记录
            chat = await self._get(run.chat_id)
            run.instance.history = _load_history(chat.history)
            run.instance.effort = "low" if run.thinking else "none"
            loaded = True
            queue: asyncio.Queue = asyncio.Queue()
            unsubscribe = run.instance.agent_event.subscribe(queue.put_nowait)
            task = asyncio.create_task(run.instance.run(run.content))
            _RUN_TASKS.add(task)

            def _on_run_done(t: asyncio.Task) -> None:
                _RUN_TASKS.discard(t)
                if not t.cancelled():
                    t.exception()  #取出异常避免未检索告警
                queue.put_nowait(None)  #哨兵：唤醒消费端收尾

            task.add_done_callback(_on_run_done)
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield to_sse(event)
            if not task.cancelled():
                error = task.exception()
                if error is not None:
                    yield to_sse(ErrorEvent(str(error)))
        finally:
            if unsubscribe is not None:
                unsubscribe()
            await self._drain(task)
            try:
                if loaded:
                    await self._persist(run)
            finally:
                run.lock.release()

    async def _drain(self, task: asyncio.Task | None) -> None:
        #断连收尾：取消未完成的 run 并短超时等待，避免后台任务并发改写 history
        if task is None:
            return
        if not task.done():
            task.cancel()
        try:
            await asyncio.wait_for(task, 5)
        except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
            pass  #取消/超时/异常都不阻塞后续写回与放锁

    async def _persist(self, run: ChatRun) -> None:
        #run 结束（含异常/中断）把对话历史写回，供同 chat_id 续聊
        try:
            await chat_mapper.update_chat_history(run.chat_id, JSON.json(run.instance.history))
        except Exception:
            logger.exception("chat history 写回失败: %s", run.chat_id)

    async def _get(self, chat_id: int):
        entity = await chat_mapper.select_chat(chat_id)
        if entity is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"chat 不存在: {chat_id}")
        return entity


def _load_history(text: str) -> list:
    try:
        history = JSON.parse(text or "[]")
    except ValueError:
        logger.warning("chat history 解析失败，按空历史处理")
        return []
    return history if isinstance(history, list) else []


def _to_out(entity) -> ChatOut:
    return ChatOut(
        chat_id=entity.id, agent_id=entity.agent_id, title=entity.title,
        history=_load_history(entity.history),
        created_at=entity.created_at, updated_at=entity.updated_at,
    )
