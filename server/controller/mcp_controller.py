"""MCP server 管理接口。"""

from fastapi import APIRouter, Depends

from voyo.utils import Methods

from server.dependencies import get_mcp_service
from server.models.mcp_models import McpCreate
from server.service.mcp_service import McpService

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


@router.get("")
async def list_mcp(service: McpService = Depends(get_mcp_service)):
    return Methods.resp_result(await service.list())


@router.post("", status_code=201)
async def create_mcp(body: McpCreate, service: McpService = Depends(get_mcp_service)):
    return Methods.resp_result(await service.create(body), code=201)


@router.get("/{mcp_id}")
async def get_mcp(mcp_id: int, service: McpService = Depends(get_mcp_service)):
    return Methods.resp_result(await service.get(mcp_id))


@router.put("/{mcp_id}")
async def update_mcp(mcp_id: int, body: McpCreate, service: McpService = Depends(get_mcp_service)):
    return Methods.resp_result(await service.update(mcp_id, body))


@router.delete("/{mcp_id}")
async def delete_mcp(mcp_id: int, service: McpService = Depends(get_mcp_service)):
    await service.delete(mcp_id)
    return Methods.resp_success()
