"""模型接入配置 CRUD。"""

import logging

from asyncpg import UniqueViolationError
from voyo.utils import YoHttpException
from voyo.utils.exception import ExceptionType

from server.mapper import agent_mapper, model_mapper
from server.models.model_models import ModelCreate, ModelOut, mask_api_key

logger = logging.getLogger(__name__)


class ModelService:

    async def list(self) -> list[ModelOut]:
        return [to_out(e) for e in await model_mapper.select_models()]

    async def get(self, model_id: int) -> ModelOut:
        return to_out(await self._get(model_id))

    async def create(self, body: ModelCreate) -> ModelOut:
        name = _check_name(body.name)
        if not (body.api_key or "").strip():
            raise YoHttpException(ExceptionType.PARAM_ERROR, "api_key 不能为空")
        try:
            entity = await model_mapper.insert_model(
                name, body.model, body.base_url, body.api_key, body.description)
        except UniqueViolationError:
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"模型名称已存在: {name}")
        logger.info("创建模型: %s", entity.id)
        return to_out(entity)

    async def update(self, model_id: int, body: ModelCreate) -> ModelOut:
        existing = await self._get(model_id)
        name = _check_name(body.name)
        #api_key 留空表示不修改（出参脱敏不可回填，前端约定留空保持原值）
        api_key = (body.api_key or "").strip() or existing.api_key
        try:
            entity = await model_mapper.update_model(
                model_id, name, body.model, body.base_url, api_key, body.description)
        except UniqueViolationError:
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"模型名称已存在: {name}")
        if entity is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"模型不存在: {model_id}")
        return to_out(entity)

    async def delete(self, model_id: int) -> None:
        await self._get(model_id)
        refs = await agent_mapper.select_agents_by_model(model_id)
        if refs:
            names = ", ".join(a.name for a in refs)
            raise YoHttpException(ExceptionType.PARAM_ERROR, f"模型已被 agent 引用: {names}")
        await model_mapper.delete_model(model_id)
        logger.info("删除模型: %s", model_id)

    async def _get(self, model_id: int):
        entity = await model_mapper.select_model(model_id)
        if entity is None:
            raise YoHttpException(ExceptionType.NOT_FOUND, f"模型不存在: {model_id}")
        return entity


def _check_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise YoHttpException(ExceptionType.PARAM_ERROR, "模型名称不能为空")
    return name


def to_out(entity) -> ModelOut:
    return ModelOut(
        id=entity.id, name=entity.name, model=entity.model, base_url=entity.base_url,
        api_key=mask_api_key(entity.api_key), description=entity.description,
        created_at=entity.created_at, updated_at=entity.updated_at,
    )
