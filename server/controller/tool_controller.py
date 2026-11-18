"""内置工具只读接口。"""

from fastapi import APIRouter

from voyo.utils import Methods, YoHttpException
from voyo.utils.exception import ExceptionType

from server.service import tool_service

router = APIRouter(prefix="/api/tools", tags=["tool"])


@router.get("")
async def list_tools():
    return Methods.resp_result(tool_service.list_tools())


@router.get("/{name}")
async def get_tool(name: str):
    tool = tool_service.get_tool(name)
    if tool is None:
        raise YoHttpException(ExceptionType.NOT_FOUND, f"工具不存在: {name}")
    return Methods.resp_result(tool)
