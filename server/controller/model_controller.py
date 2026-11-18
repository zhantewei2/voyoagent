"""模型管理接口。"""

from fastapi import APIRouter, Depends

from voyo.utils import Methods

from server.dependencies import get_model_service
from server.models.model_models import ModelCreate
from server.service.model_service import ModelService

router = APIRouter(prefix="/api/models", tags=["model"])


@router.get("")
async def list_models(service: ModelService = Depends(get_model_service)):
    return Methods.resp_result(await service.list())


@router.post("", status_code=201)
async def create_model(body: ModelCreate, service: ModelService = Depends(get_model_service)):
    return Methods.resp_result(await service.create(body), code=201)


@router.get("/{model_id}")
async def get_model(model_id: int, service: ModelService = Depends(get_model_service)):
    return Methods.resp_result(await service.get(model_id))


@router.put("/{model_id}")
async def update_model(model_id: int, body: ModelCreate, service: ModelService = Depends(get_model_service)):
    return Methods.resp_result(await service.update(model_id, body))


@router.delete("/{model_id}")
async def delete_model(model_id: int, service: ModelService = Depends(get_model_service)):
    await service.delete(model_id)
    return Methods.resp_success()
