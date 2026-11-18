import asyncio
import logging
import traceback
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import TypedDict, Literal
from voyo.utils.json import JSON
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from voyoagent.utils.exception import YoAgentCode,YoAgentException

logger= logging.getLogger(__name__)

class Agent_MCP_Interface:
    #Agent_MCP 的对外接口，宿主 agent 只依赖这一层。
    #状态机：registry_mcp 后 loading(连接/安装中) -> ready(可用) | error(失败，可 reload 重试)。


    def registry_tool(self, tool_entry):
        #宿主 agent 提供的注册入口：接收 (schema, handler) 二元组，写入 agent 工具表。
        #多继承时由 MRO 中更靠前的子类覆盖此声明。
        raise NotImplementedError


    def unregistry_tool(self, tool_name: str):
        #宿主 agent 提供的注销入口：按 schema name 从 agent 工具表移除条目。
        #server 断开/重载时必须，否则工具表残留死 handler，重注册还会撞「重复注册」。
        raise NotImplementedError


    async def registry_mcp(self, name: str, command: str = "", args: list[str] | None = None, url: str = ""):
        #连接一个标准 MCP server，并把它的全部工具注册进 agent（工具名加前缀 mcp__<server>__<原名>）。
        #command=stdio 子进程接入（如 npx 安装耗时，状态停在 loading）；url=streamable http 接入，二者必传其一。
        #连接在后台进行、立即返回；失败只落 error 状态。同名 server 已存在且非 error 状态时抛 ValueError。
        raise NotImplementedError


    async def reload_mcp(self, name: str):
        #按注册时的原参数重连指定 server：ready 用于刷新工具列表，error 用于重试；loading 中拒绝。
        raise NotImplementedError


    async def remove_mcp(self, name: str):
        #断开指定 server，注销它提供的全部工具并删除状态记录；loading 中拒绝。
        raise NotImplementedError


    def list_mcp(self) -> list[dict]:
        #返回全部 server 的状态快照（同步、立即返回）：
        #每项含 name/state(loading|ready|error)/error/tools/command/args/url。
        raise NotImplementedError


    def registry_mcp_base_tools(self):
        #把 mcp_list / mcp_remove / mcp_reload 三个管理动作注册为 agent 工具，
        #让模型自主查看、重载、移除 MCP server。是否调用由宿主决定（不调则模型无此能力）。
        raise NotImplementedError


    async def close(self):
        #整体收尾：取消后台注册任务、断开全部 server 并清空状态。宿主 agent 销毁时调用一次。
        raise NotImplementedError


@dataclass
class MCPServerState:
    #server 连接状态快照：loading(连接/安装中) -> ready | error
    name: str
    state: Literal["loading", "error", "ready"] = "loading"
    error: str = ""
    tools: list[str] = field(default_factory=list)
    command: str = ""
    args: list[str] = field(default_factory=list)
    url: str = ""
    mcp_session: ClientSession =None
    keep_event: asyncio.Event =None
    task: asyncio.Task= None


class Mcp_Tool_Info(TypedDict):
    tool_full_name: str
    mcp_name: str
    tool_name: str

MCP_LIST_TOOL = {
    "type": "function",
    "name": "mcp_list",
    "description": "查看当前已注册的 MCP server 列表及状态（loading=连接/安装中，ready=可用，error=失败及原因），含各 server 提供的工具。",
    "parameters": {"type": "object", "properties": {}},
}
MCP_REMOVE_TOOL = {
    "type": "function",
    "name": "mcp_remove",
    "description": "断开并移除指定 MCP server，其提供的工具随之注销。",
    "parameters": {
        "type": "object",
        "properties": {"name": {"type": "string", "description": "MCP server 名称"}},
        "required": ["name"],
    },
}
MCP_RELOAD_TOOL = {
    "type": "function",
    "name": "mcp_reload",
    "description": "用原参数重新连接指定 MCP server（ready 或 error 状态均可），并以重连后的工具列表为准。",
    "parameters": {
        "type": "object",
        "properties": {"name": {"type": "string", "description": "MCP server 名称"}},
        "required": ["name"],
    },
}




class Agent_MCP(Agent_MCP_Interface):

    mcp_states: dict[str, MCPServerState]

    #MCP server 接入器 mixin：把标准 MCP server 的工具转成 (schema, handler) 交给 registry_tool 注册
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mcp_states= {} #mcp_name : mcpServerState

    def registry_tool(self, tool_entry):
        #空实现仅声明接口；实际注册由 MRO 中更前的子类覆盖（如 Voyo_Agent 的工具注册表）
        pass


    def unregistry_tool(self, tool_name):
        #同上，standalone 空实现；真实注销由宿主覆盖
        pass

    
    async def registry_mcp(self, name: str, command: str = "", args: list[str] | None = None, url: str = ""):
        #command=stdio 子进程接入（如 npx 安装耗久则停留在 loading）；url=streamable http 接入
        #连接在后台进行、不阻塞调用方（如 agent 初始化），失败只落 error 状态不抛出
        if not name:
            raise ValueError("MCP server 名称不能为空")
        old = self.mcp_states.get(name)
        if old and old.state != "error":
            raise ValueError(f"MCP server 已注册且未失败: {name!r} ({old.state})")
        await self._register(name, command, args or [], url)


    async def reload_mcp(self, name: str):
        #按原参数重连；ready 可刷新工具列表，error 可重试
        mcp_state = self._get_mcp_state(name)
        if mcp_state.state == "loading":
            raise ValueError(f"{name!r} 正在连接中，暂不能 reload")
        await self._register(name, mcp_state.command, mcp_state.args, mcp_state.url)


    async def _register(self, name: str, command: str, args: list[str], url: str):
        if name in self.mcp_states:
            await self._drop(name) #error 重试前收掉旧连接，避免子进程残留
        self.mcp_states[name] = mcp_state = MCPServerState(name=name, command=command, args=args, url=url)
        mcp_state.task = asyncio.create_task(self._owner(mcp_state, command, args, url))
        

    async def _owner(self, mcp_state:MCPServerState, command: str, args: list[str], url: str):

        stack = AsyncExitStack()
        async with stack:
            try:
                mcp_state.state="loading"
                if command:
                    params = StdioServerParameters(command=command, args=args)
                    read, write = await stack.enter_async_context(stdio_client(params))
                elif url:
                    read, write = await stack.enter_async_context(streamable_http_client(url))
                else:
                    raise ValueError("registry_mcp 需要 command(stdio) 或 url(http) 之一")
                
                mcp_state.mcp_session = await stack.enter_async_context(ClientSession(read, write))
                await mcp_state.mcp_session.initialize()
                mcp_state.keep_event=keep_event=asyncio.Event()
                await self._registry_owner_tools(mcp_state)
                mcp_state.state="ready"
                await keep_event.wait()
            except Exception as e:
                logger.error("MCP %s 连接失败:\n%s", mcp_state.name, traceback.format_exc())
                mcp_state.error=str(e)
                mcp_state.state= "error"
            finally:
                #正常/报错/强杀退出都摘掉已注册工具（unregistry 对不存在名字是 no-op）
                for tool_name in mcp_state.tools:
                    self.unregistry_tool(self.get_tool_full_name(mcp_state.name, tool_name))
                self.clear_mcp_state(mcp_state)

    def clear_mcp_state(self,mcp_state: MCPServerState):
        #仅摘运行时引用；state/error 留给 list_mcp 展示与 registry_mcp 的重试判断
        mcp_state.mcp_session=None
        mcp_state.keep_event=None
        mcp_state.task=None

    async def _registry_owner_tools(self,mcp_state: MCPServerState):
        tools=(await mcp_state.mcp_session.list_tools()).tools
        mcp_state.tools=[t.name for t in tools] #注销与 list_mcp 都以此为准
        for tool in tools:
            self._registry_tool(mcp_state.name, mcp_state.mcp_session, tool)

    async def remove_mcp(self, name: str):
        #断开并注销整个 server（含状态记录）
        state = self._get_mcp_state(name)
        if state.state == "loading":
            raise ValueError(f"{name!r} 正在连接中，暂不能 remove")
        await self._drop(name)
        del self.mcp_states[name]


    def list_mcp(self) -> list[dict]:
        #各 server 状态快照

        return [{
            "name": name,
            "state": state.state,
            "command": state.command,
            "args": state.args,
            "url": state.url,
            "error": state.error,
            "tools": state.tools
        } for name, state in self.mcp_states.items()]


    def registry_mcp_base_tools(self):
        #把 MCP 管理能力注册为 agent 工具，让 agent 自主 list/remove/reload
        self.registry_tool((MCP_LIST_TOOL, self._tool_list))
        self.registry_tool((MCP_REMOVE_TOOL, self._tool_remove))
        self.registry_tool((MCP_RELOAD_TOOL, self._tool_reload))


    async def _tool_list(self, args: dict) -> str:
        return JSON.json(self.list_mcp())

    async def _tool_remove(self, args: dict) -> str:
        name = args.get("name", "")
        await self.remove_mcp(name)
        return f"已移除 MCP server: {name}"

    #
    # {name: str}  #name mcp_name
    #
    async def _tool_reload(self, args: dict) -> str:
        #后台重载：不让模型在 npx 安装上阻塞整个 turn，用 mcp_list 轮询结果
        name = args.get("name", "")
        await self.reload_mcp(name)
        return f"已在后台重载 MCP server: {name}，可用 mcp_list 查看状态"


    def _get_mcp_state(self, name: str) -> MCPServerState:
        state = self.mcp_states.get(name)
        if state is None:
            raise YoAgentException(YoAgentCode.MCP_ERROR, f"MCP server 未注册: {name!r}，可用 mcp_list 查看现存列表")
        
        return state

    def get_tool_full_name(self,mcp_name:str, tool_name:str)->str:
        return f"mcp__{mcp_name}__{tool_name}"

    def _registry_tool(self, mcp_name: str, session: ClientSession, tool) -> None:
        self.registry_tool(({
            "type": "function",
            "name": self.get_tool_full_name(mcp_name,tool.name),
            "description": tool.description or "",
            "parameters": tool.input_schema or {"type": "object", "properties": {}},
        }, self._make_handler(session, tool.name)))


    @staticmethod
    def _make_handler(session: ClientSession, tool_name: str):
        async def handler(args: dict) -> str:
            result = await session.call_tool(tool_name, args or {})
            texts = [c.text for c in result.content if getattr(c, "text", None)]
            body = "\n".join(texts) if texts else "(无文本返回)"
            return f"工具执行失败: {body}" if result.is_error else body
        return handler


    async def _drop(self, name: str):
        #断开单个 server：唤醒/取消 owner 任务；工具注销与状态清理都由 owner 的 finally 完成
        mcp_state= self.mcp_states.get(name)
        if mcp_state is None:
            return

        if mcp_state.keep_event:
            mcp_state.keep_event.set() #优雅唤醒 owner 正常退出
        task= mcp_state.task
        if task is not None and not task.done():
            try:
                #正常毫秒级退出；卡在安装/初始化/list_tools 时由超时取消强杀
                await asyncio.wait_for(task, 5)
            except Exception:
                pass #收尾失败不掩盖主流程


    async def close(self):

        for mcp_name in list(self.mcp_states):
            await self._drop(mcp_name)
        self.mcp_states.clear()
