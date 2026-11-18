"""t_mcp 表 SQL。读走免事务通道，写保持 @transaction。"""

from voyo.db.pg import transaction

from server.db import fetch_all, fetch_one, retry_once
from server.entity.base import new_id
from server.entity.mcp_entity import McpEntity

_COLUMNS = "id, name, description, command, args, url, created_at, updated_at"


@retry_once
@transaction()
async def insert_mcp(name: str, description: str, command: str, args: list[str], url: str,
                     conn=None) -> McpEntity:
    entity = McpEntity(id=new_id(), name=name, description=description,
                       command=command, args=args, url=url)
    await conn.execute(
        f"INSERT INTO t_mcp ({_COLUMNS}) VALUES ($1,$2,$3,$4,$5,$6,$7,$7)",
        entity.id, entity.name, entity.description, entity.command, entity.args, entity.url,
        entity.created_at,
    )
    return entity


async def select_mcp(mcp_id: int) -> McpEntity | None:
    row = await fetch_one(f"SELECT {_COLUMNS} FROM t_mcp WHERE id = $1", mcp_id)
    return to_entity(row)


async def select_mcps() -> list[McpEntity]:
    rows = await fetch_all(f"SELECT {_COLUMNS} FROM t_mcp ORDER BY id")
    return [to_entity(row) for row in rows]


@retry_once
@transaction()
async def update_mcp(mcp_id: int, name: str, description: str, command: str,
                     args: list[str], url: str, conn=None) -> McpEntity | None:
    row = await conn.fetchrow(
        f"""UPDATE t_mcp SET name=$2, description=$3, command=$4, args=$5, url=$6, updated_at=now()
            WHERE id=$1 RETURNING {_COLUMNS}""",
        mcp_id, name, description, command, args, url,
    )
    return to_entity(row)


@retry_once
@transaction()
async def delete_mcp(mcp_id: int, conn=None) -> bool:
    status = await conn.execute("DELETE FROM t_mcp WHERE id = $1", mcp_id)
    return status.endswith("1")


def to_entity(row) -> McpEntity | None:
    if row is None:
        return None
    return McpEntity(
        id=row["id"], name=row["name"], description=row["description"],
        command=row["command"], args=list(row["args"] or []), url=row["url"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )
