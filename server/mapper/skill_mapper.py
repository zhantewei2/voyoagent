"""t_skill 表 SQL。读走免事务通道，写保持 @transaction。"""

from voyo.db.pg import transaction

from server.db import fetch_all, fetch_one, retry_once
from server.entity.base import new_id
from server.entity.skill_entity import SkillEntity

_COLUMNS = "id, name, description, content, created_at, updated_at"


@retry_once
@transaction()
async def insert_skill(name: str, description: str, content: str, conn=None) -> SkillEntity:
    entity = SkillEntity(id=new_id(), name=name, description=description, content=content)
    await conn.execute(
        f"INSERT INTO t_skill ({_COLUMNS}) VALUES ($1,$2,$3,$4,$5,$5)",
        entity.id, entity.name, entity.description, entity.content, entity.created_at,
    )
    return entity


async def select_skill(skill_id: int) -> SkillEntity | None:
    row = await fetch_one(f"SELECT {_COLUMNS} FROM t_skill WHERE id = $1", skill_id)
    return to_entity(row)


async def select_skills() -> list[SkillEntity]:
    rows = await fetch_all(f"SELECT {_COLUMNS} FROM t_skill ORDER BY id")
    return [to_entity(row) for row in rows]


@retry_once
@transaction()
async def update_skill(skill_id: int, name: str, description: str, content: str,
                       conn=None) -> SkillEntity | None:
    row = await conn.fetchrow(
        f"""UPDATE t_skill SET name=$2, description=$3, content=$4, updated_at=now()
            WHERE id=$1 RETURNING {_COLUMNS}""",
        skill_id, name, description, content,
    )
    return to_entity(row)


@retry_once
@transaction()
async def delete_skill(skill_id: int, conn=None) -> bool:
    status = await conn.execute("DELETE FROM t_skill WHERE id = $1", skill_id)
    return status.endswith("1")


def to_entity(row) -> SkillEntity | None:
    if row is None:
        return None
    return SkillEntity(
        id=row["id"], name=row["name"], description=row["description"], content=row["content"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )
