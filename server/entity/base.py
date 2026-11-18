"""entity 基类：表实体的公共部分。"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from voyo.utils import yo_unique


def new_id() -> int:
    #主键统一用 voyolib 的 unique_id 生成
    return yo_unique.get_uid()


def now() -> datetime:
    #带时区 UTC：与 DB 往返值一致，避免创建回显与查询时间错位
    return datetime.now(timezone.utc)


@dataclass
class BaseEntity:
    id: int = field(default_factory=new_id)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)
