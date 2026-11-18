"""技能资产 CRUD。"""

import logging

from asyncpg import UniqueViolationError
from voyo.utils import YoHttpException
from voyo.utils.exception import ExceptionType

from server.mapper import agent_mapper, skill_mapper
from server.models.skill_models import SkillCreate, SkillListItem, SkillOut

logger = logging.getLogger(__name__)


class SkillService:

    async def list(self) -> list[SkillListItem]:
        return [to_item(e) for e in await skill_mapper.select_skills()]

    async def get(self, skill_id: int) -> SkillOut:
        return to_out(await self._get(skill_id))

    async def create(self, body: SkillCreate) -> SkillOut:
        name = _check_name(body.name)
        try:
            entity = await skill_mapper.insert_skill(name, body.description, body.content)
        except UniqueViolationError:
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"技能名称已存在: {name}")
        logger.info("创建技能: %s", entity.id)
        return to_out(entity)

    async def update(self, skill_id: int, body: SkillCreate) -> SkillOut:
        await self._get(skill_id)
        name = _check_name(body.name)
        try:
            entity = await skill_mapper.update_skill(skill_id, name, body.description, body.content)
        except UniqueViolationError:
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"技能名称已存在: {name}")
        if entity is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"技能不存在: {skill_id}")
        return to_out(entity)

    async def delete(self, skill_id: int) -> None:
        await self._get(skill_id)
        refs = await agent_mapper.select_agents_by_skill(skill_id)
        if refs:
            names = ", ".join(a.name for a in refs)
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"技能已被 agent 引用: {names}")
        await skill_mapper.delete_skill(skill_id)
        logger.info("删除技能: %s", skill_id)

    async def _get(self, skill_id: int):
        entity = await skill_mapper.select_skill(skill_id)
        if entity is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"技能不存在: {skill_id}")
        return entity


def _check_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise YoHttpException(ExceptionType.PARAM_ERROR, "技能名称不能为空")
    return name


def to_item(entity) -> SkillListItem:
    return SkillListItem(
        id=entity.id, name=entity.name, description=entity.description,
        created_at=entity.created_at, updated_at=entity.updated_at,
    )


def to_out(entity) -> SkillOut:
    return SkillOut(**to_item(entity).model_dump(), content=entity.content)
