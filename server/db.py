"""PG 连接池：启动建池 + 后台保活，读走免事务通道，死连接换连接重试一次。"""

import asyncio
import functools
import logging
from typing import Any, Callable, TypeVar

from voyo.db.pg import ConnectionPool, asyncpg, get_current_connection, get_default_pool, set_default_pool

from server.config import settings

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

#查询超时：公网死连接不再无限挂起
COMMAND_TIMEOUT = 30.0
#保活间隔：空闲连接定期探活，防被中间设备掐死
KEEPALIVE_INTERVAL = 60.0

_POOL_KWARGS = {"command_timeout": COMMAND_TIMEOUT}

#死连接/连接已关闭类异常：换新连接重试一次
_DEAD_CONN_ERRORS = (
    asyncpg.exceptions.ConnectionDoesNotExistError,
    asyncpg.exceptions.InterfaceError,
    asyncpg.exceptions.InternalClientError,
    OSError,
    EOFError,
)

_pool: ConnectionPool | None = None
_keepalive_task: asyncio.Task | None = None


def retry_once(fn: F) -> F:
    #死连接兜底：原连接上失败时换连接重试一次，仍失败抛给中间件
    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(*args, **kwargs)
        except _DEAD_CONN_ERRORS:
            logger.warning("数据库连接疑似失效，换连接重试一次: %s", fn.__name__)
            return await fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


@retry_once
async def fetch_one(sql: str, *args: Any) -> dict | None:
    #免事务单行读：省掉 BEGIN/COMMIT 往返；处于事务中时复用当前连接
    conn = get_current_connection()
    if conn is not None:
        row = await conn.fetchrow(sql, *args)
        return dict(row) if row else None
    conn = await _acquire()
    try:
        row = await conn.fetchrow(sql, *args)
        return dict(row) if row else None
    finally:
        await _release(conn)


@retry_once
async def fetch_all(sql: str, *args: Any) -> list[dict]:
    #免事务多行读，同上
    conn = get_current_connection()
    if conn is not None:
        rows = await conn.fetch(sql, *args)
        return [dict(row) for row in rows]
    conn = await _acquire()
    try:
        rows = await conn.fetch(sql, *args)
        return [dict(row) for row in rows]
    finally:
        await _release(conn)


async def _acquire():
    pool = get_default_pool()
    if pool is None:
        raise RuntimeError("数据库连接池未初始化")
    return await pool.acquire()


async def _release(conn) -> None:
    pool = get_default_pool()
    if pool is None:
        return
    try:
        await pool.release(conn)
    except Exception:
        logger.warning("连接归还失败，丢弃该连接", exc_info=True)


def start_keepalive() -> None:
    global _keepalive_task
    if get_default_pool() is None:
        return
    if _keepalive_task is None or _keepalive_task.done():
        _keepalive_task = asyncio.create_task(_keepalive_loop())


async def stop_keepalive() -> None:
    global _keepalive_task
    task = _keepalive_task
    _keepalive_task = None
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def _keepalive_loop() -> None:
    while True:
        await asyncio.sleep(KEEPALIVE_INTERVAL)
        try:
            await fetch_one("SELECT 1")
        except Exception:
            logger.warning("数据库保活探测失败", exc_info=True)


async def init_db() -> None:
    #建默认连接池；写操作由 @transaction 复用，读走 fetch_* 免事务通道
    global _pool
    if not settings.DATABASE_URL:
        logger.warning("未配置 DATABASE_URL，跳过数据库连接池初始化")
        return
    _pool = ConnectionPool(
        dsn=settings.DATABASE_URL,
        min_size=settings.PG_POOL_MIN_SIZE,
        max_size=settings.PG_POOL_MAX_SIZE,
        **_POOL_KWARGS,
    )
    set_default_pool(_pool)
    logger.info("数据库连接池已初始化")


async def close_db() -> None:
    global _pool
    await stop_keepalive()
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("数据库连接池已关闭")
