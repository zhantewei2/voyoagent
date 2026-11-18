"""FastAPI 应用装配：生命周期、路由注册、异常中间件。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from voyo.utils import init_logger

from server.config import settings
from server.controller import (
    agent_controller,
    chat_controller,
    mcp_controller,
    model_controller,
    skill_controller,
    tool_controller,
)
from server.db import close_db, init_db, start_keepalive, stop_keepalive
from server.middleware.exception import YoExceptionMiddleware
from server.service.agent_service import AgentManager

logger = logging.getLogger(__name__)

__all__ = ["app"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    init_logger(log_dir=settings.LOG_DIR)
    start_keepalive()
    app.state.manager = AgentManager()
    yield
    await stop_keepalive()
    await app.state.manager.close_all()
    await close_db()


app = FastAPI(lifespan=lifespan)
app.add_middleware(YoExceptionMiddleware)

app.include_router(model_controller.router)
app.include_router(skill_controller.router)
app.include_router(mcp_controller.router)
app.include_router(tool_controller.router)
app.include_router(agent_controller.router)
app.include_router(chat_controller.router)
