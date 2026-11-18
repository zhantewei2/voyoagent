"""技能管理接口。"""

from fastapi import APIRouter, Depends

from voyo.utils import Methods

from server.dependencies import get_skill_service
from server.models.skill_models import SkillCreate
from server.service.skill_service import SkillService

router = APIRouter(prefix="/api/skills", tags=["skill"])


@router.get("")
async def list_skills(service: SkillService = Depends(get_skill_service)):
    return Methods.resp_result(await service.list())


@router.post("", status_code=201)
async def create_skill(body: SkillCreate, service: SkillService = Depends(get_skill_service)):
    return Methods.resp_result(await service.create(body), code=201)


@router.get("/{skill_id}")
async def get_skill(skill_id: int, service: SkillService = Depends(get_skill_service)):
    return Methods.resp_result(await service.get(skill_id))


@router.put("/{skill_id}")
async def update_skill(skill_id: int, body: SkillCreate, service: SkillService = Depends(get_skill_service)):
    return Methods.resp_result(await service.update(skill_id, body))


@router.delete("/{skill_id}")
async def delete_skill(skill_id: int, service: SkillService = Depends(get_skill_service)):
    await service.delete(skill_id)
    return Methods.resp_success()
