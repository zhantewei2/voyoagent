import asyncio
import os
import sys
from pathlib import Path

#直接以脚本运行时项目根不在 sys.path，补上（与 tests_server/conftest.py 同款）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from voyoagent.yo_agent import Yo_Agent
from voyoagent.env import settings
from voyoagent.agent_base import AgentEventType,ThinkingDeltaEvent,ThinkingEndEvent,TextDeltaEvent

#Yo_Agent 已内置 BUILTIN_TOOLS 注册；MCP server 用 registry_mcp 接入
voyo_agent=Yo_Agent(
    model=settings.OPENAI_MODEL,
    base_url=settings.OPENAI_BASE_URL,
    api_key=settings.OPENAI_AUTH_TOKEN,
    effort="high"
)



def std_write(event:AgentEventType):

    if isinstance(event,ThinkingDeltaEvent):
        sys.stdout.write(event.content)
        sys.stdout.flush()
    elif isinstance(event,ThinkingEndEvent):
        sys.stdout.write("\n---\n")
        sys.stdout.flush()
    elif isinstance(event,TextDeltaEvent):
        sys.stdout.write(event.content)
        sys.stdout.flush()

voyo_agent.agent_event.subscribe(std_write)

async def wait_mcp_ready(name:str,timeout:float=120):
    #轮询到 loading 结束（npx 首次下载包可能要等一会）
    while True:
        state=voyo_agent.list_mcp()[[s["name"] for s in voyo_agent.list_mcp()].index(name)]["state"]
        if state!="loading":
            return state
        timeout-=0.5
        if timeout<=0:
            return "loading-timeout"
        await asyncio.sleep(0.5)

async def main():

    await voyo_agent.init()
    await voyo_agent.run("你好")
    await voyo_agent.close()

asyncio.run(main())
