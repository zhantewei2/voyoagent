from typing import Any,Awaitable,Callable,Literal,TypedDict,Optional


class ToolParameterProperty(TypedDict, total=False):
    type: str #string/number/integer/boolean/array/object
    description: str
    enum: list[str]
    items: dict[str, Any] #type 为 array 时元素定义


class ToolParameters(TypedDict, total=False):
    type: Literal["object"]
    properties: dict[str, ToolParameterProperty]
    required: list[str]


class ToolDef(TypedDict):
    type: Literal["function"]
    name: str
    description: str
    parameters: ToolParameters


# 实现函数约定：入参来自模型给的 JSON，返回值序列化后回传
ToolHandler = Callable[..., Awaitable[str]]

# 注册表条目：名字绑定 schema 描述与实现
ToolEntry = tuple[ToolDef, ToolHandler]

class Tool_call(TypedDict):
    type: str
    name: str #tool name
    call_id: str #call_id 回传时需要
    arguments: Optional[dict] #参数

class Tool_Type(TypedDict):
    id: str
    name: str
    type: str
    description: str
    parameters: ToolParameters
    tool_handler: ToolHandler

