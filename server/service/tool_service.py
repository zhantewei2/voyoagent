"""内置工具只读服务：数据源为 voyoagent 内置工具 + load_skill。"""

from voyoagent.tools import LOAD_SKILL_TOOL
from voyoagent.yo_agent import BUILTIN_TOOLS


def _tool_schemas() -> list[dict]:
    #BUILTIN_TOOLS 为 (schema, handler) 二元组；LOAD_SKILL_TOOL 自带 schema
    return [entry[0] for entry in BUILTIN_TOOLS] + [LOAD_SKILL_TOOL]


_TOOL_INDEX: dict[str, dict] = {schema["name"]: schema for schema in _tool_schemas()}


def list_tools() -> list[dict]:
    return [dict(schema) for schema in _TOOL_INDEX.values()]


def get_tool(name: str) -> dict | None:
    schema = _TOOL_INDEX.get(name)
    return dict(schema) if schema else None


def known_tool_names() -> set[str]:
    #load_skill 由框架自带，不列入可装配工具（Tool 管理列表仍展示）
    return set(_TOOL_INDEX) - {"load_skill"}


def tool_entry(name: str):
    #供 agent 装配取 (schema, handler)；load_skill 由框架自带，不返回条目
    for entry in BUILTIN_TOOLS:
        if entry[0].get("name") == name:
            return entry
    return None
