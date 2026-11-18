"""t_chat 表 SQL。读走免事务通道，写保持 @transaction。"""

from voyo.db.pg import transaction

from server.db import fetch_one, retry_once
from server.entity.chat_entity import ChatEntity
from server.entity.base import new_id

_COLUMNS = "id, agent_id, title, history, created_at, updated_at"


@retry_once
@transaction()
async def insert_chat(agent_id: int, title: str = "", history: str = "[]",
                      conn=None) -> ChatEntity:
    entity = ChatEntity(id=new_id(), agent_id=agent_id, title=title, history=history)
    await conn.execute(
        f"INSERT INTO t_chat ({_COLUMNS}) VALUES ($1,$2,$3,$4,$5,$5)",
        entity.id, entity.agent_id, entity.title, entity.history, entity.created_at,
    )
    return entity


async def select_chat(chat_id: int) -> ChatEntity | None:
    row = await fetch_one(f"SELECT {_COLUMNS} FROM t_chat WHERE id = $1", chat_id)
    return to_entity(row)


@retry_once
@transaction()
async def update_chat_history(chat_id: int, history: str, conn=None) -> ChatEntity | None:
    row = await conn.fetchrow(
        f"UPDATE t_chat SET history=$2, updated_at=now() WHERE id=$1 RETURNING {_COLUMNS}",
        chat_id, history,
    )
    return to_entity(row)


def to_entity(row) -> ChatEntity | None:
    if row is None:
        return None
    return ChatEntity(
        id=row["id"], agent_id=row["agent_id"], title=row["title"], history=row["history"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )
