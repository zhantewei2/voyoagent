from voyo.model import OpenAiResponsesClient,ModelUsage,ThinkingEffort
from voyo.model.types import OpenAiResponsesMsg,ResponsesFunctionCallOutputItem,ResponsesFunctionCallItem


from voyo.utils.json import JSON
from typing import TypedDict,Literal,AsyncIterator
import sys
from voyoagent.constants import Constants

from voyoagent.agent_base import AgentEvent,RunStartEvent,TurnEndEvent,DoneEvent
from voyoagent.agent_chat import AgentChat
from voyoagent.agent_hook import Agent_Hook
from voyoagent.functional.logger_event_handler import logger_event_handler
from voyoagent.prompt import AgentPrompt
from voyoagent.constants import root_dir
from voyoagent.agent_mcp import Agent_MCP
from voyoagent.agent_skill import Agent_Skill


class Voyo_Agent(AgentChat, Agent_MCP, Agent_Skill):
    history: list[OpenAiResponsesMsg]
    model:str
    effort: ThinkingEffort
    next_call_tools:list[ResponsesFunctionCallOutputItem|ResponsesFunctionCallItem]
    agent_prompt: AgentPrompt
    
    def __init__(
            self,
            model:str=None,
            base_url:str="",
            api_key:str="",
            effort:ThinkingEffort="none",
            system_prompt_path:str="",
            soul_prompt_path:str="",
            skill_dirs:list[str]|None=None
        ):
        self.client= OpenAiResponsesClient(
            base_url=base_url,
            api_key=api_key
        )

        system_prompt_path=system_prompt_path if system_prompt_path else str(root_dir / "prompts" / "system.md")
        soul_prompt_path=soul_prompt_path if soul_prompt_path else str(root_dir / "prompts" / "soul.md")

        super().__init__(AgentEvent())
        self.model=model
        self.effort=effort
        self.history=[]
        self.next_call_tools=[]
        self.skill_dirs=skill_dirs if skill_dirs else []
        self.agent_prompt = AgentPrompt(
            system_prompt_path=system_prompt_path,
            soul_prompt_path=soul_prompt_path
        )

        logger_event_handler(self.agent_event)

    async def init(self):
        #先触发钩子，订阅方注入的 fragment 能进入随后的统一提示词
        self.registry_mcp_base_tools()
        if self.skill_dirs:
            await self.registry_skill(self.skill_dirs)
        await self.agent_hook.emit_agent_init()

        
    async def run(self,content:str):
        await self.agent_hook.emit_user_input(content)
        self.agent_event.write(RunStartEvent())
        await self.achat(content)
        for _ in range(Constants.MAX_TURNS):
            if not self.next_call_tools: break
            self.history.extend(self.next_call_tools)
            self.next_call_tools=[]
            await self.achat()
            self.agent_event.write(TurnEndEvent())
        await self.agent_hook.emit_dialog_end()
        self.agent_event.write(DoneEvent(self._final_text()))

    def _final_text(self)->str:
        #最终回答取最后一条 assistant 文本消息
        for msg in reversed(self.history):
            if msg.get("role")=="assistant" and isinstance(msg.get("content"),str):
                return msg["content"]
        return ""
    

   

        