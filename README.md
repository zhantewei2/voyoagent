# voyoagent

基于 OpenAI Responses API 的极简异步 Agent 框架：流式事件输出、工具注册、Skill 渐进加载、MCP 接入、提示词 fragment 与生命周期钩子。核心是基类 `Voyo_Agent`，`await agent.run("...")` 即完成一次多轮工具调用对话，全过程经 `agent_event` 以 dataclass 事件推送；`Yo_Agent` 是预置内置工具的高阶封装。

## 特性

- **流式事件**：思考流 / 正文流 / 工具调用 / 工具结果 / 错误，全部以 dataclass 事件从单一订阅点推送
- **工具**：`(schema, handler)` 二元组注册，async handler，参数由模型 JSON 给出、返回字符串回传
- **Skill**：扫描目录登记技能（SKILL.md frontmatter），模型经 `load_skill` 工具按需读取全文
- **MCP**：stdio 子进程与 streamable http 两种接入，后台连接，`loading → ready/error` 状态机
- **提示词**：system + 动态 fragment（按 id 增删改）+ soul 三段拼接
- **钩子**：`on_agent_init` / `on_user_input` / `on_dialog_end`，回调支持同步与 async

## 安装

```bash
uv add voyoagent
# 或
pip install voyoagent
```

依赖 `voyolib`（提供 `voyo.model.OpenAiResponsesClient` 与工具函数）。

## 快速开始（Voyo_Agent）

```python
import asyncio
from datetime import datetime

from voyoagent import Voyo_Agent
from voyoagent.agent_base import ThinkingDeltaEvent, TextDeltaEvent, DoneEvent
from voyoagent.tools.tool_types import ToolDef

GET_TIME_TOOL: ToolDef = {
    "type": "function",
    "name": "get_time",
    "description": "获取当前时间",
    "parameters": {"type": "object", "properties": {}},
}

async def get_time() -> str:
    return datetime.now().isoformat()

agent = Voyo_Agent(
    model="gpt-5.2",
    base_url="https://api.example.com/v1",
    api_key="sk-...",
    effort="high",              # 思考力度: none/low/medium/high
)
agent.registry_tool((GET_TIME_TOOL, get_time))

def on_event(event):
    if isinstance(event, ThinkingDeltaEvent):
        print(event.content, end="")
    elif isinstance(event, TextDeltaEvent):
        print(event.content, end="")
    elif isinstance(event, DoneEvent):
        print(f"\n=== 最终回答 ===\n{event.content}")

agent.agent_event.subscribe(on_event)

async def main():
    await agent.init()   # 注册 MCP 管理工具、登记技能，触发 on_agent_init 钩子
    await agent.run("现在几点了？")
    await agent.close()  # 断开全部 MCP server

asyncio.run(main())
```

## Voyo_Agent 能力总览

`Voyo_Agent` 由四个能力层 mixin（AgentChat / AgentTool / Agent_MCP / Agent_Skill）加三个横切组件（AgentPrompt / Agent_Hook / agent_event）组成：

| 组成 | 职责 | 关键接口 |
| --- | --- | --- |
| AgentChat | 模型对话、多轮循环、history 维护 | `run()` / `achat()` / `history` |
| AgentTool | 工具注册、schema 下发、调用执行 | `registry_tool()` / `unregistry_tool()` |
| Agent_MCP | MCP server 接入与状态机 | `registry_mcp()` / `list_mcp()` / `close()` |
| Agent_Skill | 技能登记与按需加载 | `registry_skill()` / `list_skill()` |
| AgentPrompt | system + fragment + soul 拼接 | `append_fragment_prompt()` / `replace_fragment_prompt()` |
| Agent_Hook | 生命周期钩子 | `on_agent_init` / `on_user_input` / `on_dialog_end` |
| agent_event | 事件流推送 | `subscribe()` |

生命周期三个入口：

- **`init()`**：注册 MCP 管理工具（`mcp_list` / `mcp_remove` / `mcp_reload`）→ 登记 `skill_dirs` 技能 → 触发 `on_agent_init`
- **`run(content)`**：触发 `on_user_input` → 模型响应 → 工具调用 → 结果回传，循环至无待回传调用或达到 `MAX_TURNS` → 触发 `on_dialog_end` → 推送 `DoneEvent`
- **`close()`**：断开全部 MCP server，销毁前调用一次

构造参数：`model` / `base_url` / `api_key` / `effort` / `system_prompt_path` / `soul_prompt_path` / `skill_dirs`。对话全程可读 `agent.history`（reasoning 内容随轮写回，供下一轮上下文使用）。

以下各节展开这些能力。

## 自定义工具

```python
from voyoagent.tools.tool_types import ToolDef

GET_TIME_TOOL: ToolDef = {
    "type": "function",
    "name": "get_time",
    "description": "获取当前时间",
    "parameters": {
        "type": "object",
        "properties": {"timezone": {"type": "string", "description": "时区，可选"}},
    },
}

async def get_time(timezone: str = None) -> str:
    return datetime.now().isoformat()

agent.registry_tool((GET_TIME_TOOL, get_time))
agent.unregistry_tool("get_time")   # 注销
```

handler 入参来自模型给出的 JSON（无参数时可不带），返回值序列化后作为 `function_call_output` 回传；handler 抛异常时错误文本回传给模型并推送 `ToolErrorEvent`。同名工具重复注册抛 `YoAgentException`。

## Skill

技能即一个含 `SKILL.md` 的目录，frontmatter 提供元数据：

```markdown
---
name: weather-report
description: 查询并生成城市天气报告
---
（操作指南正文，模型经 load_skill 读取）
```

```python
# 构造时传入
agent = Voyo_Agent(skill_dirs=["./skills"])

# 运行期增删查
await agent.registry_skill("./more-skills")   # 目录自身含 SKILL.md 按单技能，否则扫描一级子目录
await agent.unregistry_skill("./more-skills")
agent.list_skill()   # [{name, description, readed, skill_dir}, ...]
```

登记后技能集合以 fragment 注入系统提示词，模型按需调用 `load_skill` 读取全文，`readed` 标记已读状态。

## MCP

```python
# stdio 子进程接入（npx 首次安装耗时，状态停在 loading）
await agent.registry_mcp("fetch", command="npx", args=["-y", "@modelcontextprotocol/server-fetch"])

# streamable http 接入
await agent.registry_mcp("remote", url="https://example.com/mcp")

agent.list_mcp()      # [{name, state: loading|ready|error, error, tools, command, args, url}, ...]
await agent.reload_mcp("fetch")   # 原参数重连（ready 刷新工具表，error 重试）
await agent.remove_mcp("fetch")   # 断开并注销其全部工具
```

连接在后台任务中进行，`registry_mcp` 立即返回；失败落 `error` 状态、通过 `list_mcp()['error']` 查看原因。server 工具以 `mcp__<server>__<工具名>` 注册。`init()` 已把 `mcp_list` / `mcp_reload` / `mcp_remove` 注册为模型工具，agent 可自主查看与管理 MCP server。

## 事件流

`agent.agent_event.subscribe(handler)` 订阅，`handler` 收到全部事件 dataclass：

| 事件 | 字段 | 时机 |
| --- | --- | --- |
| `RunStartEvent` | - | `run()` 开始 |
| `ThinkingStartEvent` / `ThinkingDeltaEvent` / `ThinkingEndEvent` | `content`（delta） | 思考流 |
| `TextStartEvent` / `TextDeltaEvent` | `content`（delta） | 正文流 |
| `ToolCallEvent` | `call_id` / `name` / `arguments` | 工具调用前 |
| `ToolResultEvent` / `ToolErrorEvent` | `call_id` / `name` / `result` 或 `error` | 工具返回后 |
| `ResponseCompletedEvent` | - | 一轮模型响应流结束 |
| `TurnEndEvent` | - | 一轮工具结果回传完成 |
| `DoneEvent` | `content` | `run()` 结束，最终全文 |
| `ErrorEvent` | `content` | 错误 |

事件类型汇总为 `AgentEventType`；thinking 流结束时框架把 reasoning 内容写回 history，供下一轮上下文使用。

## 生命周期钩子

```python
agent.agent_hook.on_agent_init.subscribe(my_init)     # init() 尾部触发一次
agent.agent_hook.on_user_input.subscribe(my_hook)     # 每次 run() 入口，参数: 用户输入 str
agent.agent_hook.on_dialog_end.subscribe(my_hook)     # 每次 run() 结束
```

回调支持同步函数或 async 函数。

## 提示词体系

最终 system 提示词 = `system.md` + 动态 fragment 区 + `soul.md`：

```python
agent.agent_prompt.append_fragment_prompt("rules", "额外规则文本")
agent.agent_prompt.replace_fragment_prompt("rules", "新文本")  # 按 id 替换，id 不存在返回 False
```

默认提示词文件随包内置（`voyoagent/prompts/`），构造时用 `system_prompt_path` / `soul_prompt_path` 覆盖。

## Yo_Agent：高阶封装

`Yo_Agent` 继承 `Voyo_Agent`，预置常用能力，构造即可投入使用：

- **内置工具**（构造即注册，`auto_registry_tool=False` 可关闭）：`read_file` / `write_file` / `replace_file` / `list_dir` / `run_shell` / `get_weather`
- **fragment 自动注入**：当前时间（每轮 `run()` 刷新）与操作系统平台

```python
from voyoagent import Yo_Agent

agent = Yo_Agent(
    model="gpt-5.2",
    base_url="https://api.example.com/v1",
    api_key="sk-...",
    skill_dirs=["./skills"],
)
```

构造参数与 `Voyo_Agent` 一致，额外多 `auto_registry_tool`；事件、Skill、MCP、钩子、提示词等接口全部继承自 `Voyo_Agent`。
