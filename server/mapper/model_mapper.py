"""t_model 表 SQL。读走免事务通道，写保持 @transaction。"""

from voyo.db.pg import transaction

from server.db import fetch_all, fetch_one, retry_once
from server.entity.base import new_id
from server.entity.model_entity import ModelEntity

_COLUMNS = "id, name, model, base_url, api_key, description, created_at, updated_at"


@retry_once
@transaction()
async def insert_model(name: str, model: str, base_url: str, api_key: str,
                       description: str = "", conn=None) -> ModelEntity:
    entity = ModelEntity(id=new_id(), name=name, model=model, base_url=base_url,
                         api_key=api_key, description=description)
    await conn.execute(
        f"INSERT INTO t_model ({_COLUMNS}) VALUES ($1,$2,$3,$4,$5,$6,$7,$7)",
        entity.id, entity.name, entity.model, entity.base_url, entity.api_key, entity.description,
        entity.created_at,
    )
    return entity


async def select_model(model_id: int) -> ModelEntity | None:
    row = await fetch_one(f"SELECT {_COLUMNS} FROM t_model WHERE id = $1", model_id)
    return to_entity(row)


async def select_models() -> list[ModelEntity]:
    rows = await fetch_all(f"SELECT {_COLUMNS} FROM t_model ORDER BY id")
    return [to_entity(row) for row in rows]


@retry_once
@transaction()
async def update_model(model_id: int, name: str, model: str, base_url: str, api_key: str,
                       description: str, conn=None) -> ModelEntity | None:
    row = await conn.fetchrow(
        f"""UPDATE t_model SET name=$2, model=$3, base_url=$4, api_key=$5, description=$6, updated_at=now()
            WHERE id=$1 RETURNING {_COLUMNS}""",
        model_id, name, model, base_url, api_key, description,
    )
    return to_entity(row)


@retry_once
@transaction()
async def delete_model(model_id: int, conn=None) -> bool:
    status = await conn.execute("DELETE FROM t_model WHERE id = $1", model_id)
    return status.endswith("1")


def to_entity(row) -> ModelEntity | None:
    if row is None:
        return None
    return ModelEntity(
        id=row["id"], name=row["name"], model=row["model"], base_url=row["base_url"],
        api_key=row["api_key"], description=row["description"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )
