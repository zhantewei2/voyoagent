"""会话与对外 chat 接口：SSE 流式输出。"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from voyo.utils import Methods

from server.dependencies import get_chat_service
from server.models.chat_models import ChatCreate, ChatRequest
from server.service.chat_service import ChatService

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chats", status_code=201)
async def create_chat(body: ChatCreate, service: ChatService = Depends(get_chat_service)):
    return Methods.resp_result(await service.create_chat(body), code=201)


@router.get("/chats/{chat_id}")
async def get_chat(chat_id: int, service: ChatService = Depends(get_chat_service)):
    return Methods.resp_result(await service.get_chat(chat_id))


@router.post("/chat")
async def chat(body: ChatRequest,
               agent: int = Query(..., description="agent id"),
               service: ChatService = Depends(get_chat_service)):
    #对外 chat：仅 stream；chat_id 必填，事件格式与 voyoagent 一致
    run = await service.prepare(agent, body)
    return StreamingResponse(
        service.stream(run),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
