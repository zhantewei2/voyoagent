"""agent 管理接口。"""

from fastapi import APIRouter, Depends

from voyo.utils import Methods

from server.dependencies import get_agent_db_service
from server.models.agent_models import AgentCreate
from server.service.agent_db_service import AgentDbService

router = APIRouter(prefix="/api/agents", tags=["agent"])


@router.get("")
async def list_agents(service: AgentDbService = Depends(get_agent_db_service)):
    return Methods.resp_result(await service.list())


@router.post("", status_code=201)
async def create_agent(body: AgentCreate, service: AgentDbService = Depends(get_agent_db_service)):
    return Methods.resp_result(await service.create(body), code=201)


@router.get("/{agent_id}")
async def get_agent(agent_id: int, service: AgentDbService = Depends(get_agent_db_service)):
    return Methods.resp_result(await service.get(agent_id))


@router.put("/{agent_id}")
async def update_agent(agent_id: int, body: AgentCreate, service: AgentDbService = Depends(get_agent_db_service)):
    return Methods.resp_result(await service.update(agent_id, body))


@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, service: AgentDbService = Depends(get_agent_db_service)):
    await service.delete(agent_id)
    return Methods.resp_success()
